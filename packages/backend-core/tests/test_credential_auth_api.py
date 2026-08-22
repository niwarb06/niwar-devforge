from collections.abc import Generator
from uuid import uuid4

from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from devforge_core.api.auth import get_rate_limiter
from devforge_core.auth.abuse import (
    RateLimitBackendUnavailable,
    RateLimitDecision,
    RateLimiter,
    RedisFixedWindowRateLimiter,
)
from devforge_core.auth.models import Base, User
from devforge_core.config import get_settings
from devforge_core.database import get_db
from devforge_core.main import create_app


class StubRateLimiter:
    def __init__(
        self,
        decision: RateLimitDecision | None = None,
        *,
        unavailable: bool = False,
    ) -> None:
        self._decision = decision or RateLimitDecision(
            allowed=True,
            retry_after_seconds=1,
        )
        self._unavailable = unavailable

    def check(
        self,
        scope: str,
        subject: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if self._unavailable:
            raise RateLimitBackendUnavailable("test_backend_unavailable")
        return self._decision


def _make_db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def _client_with_db(
    db: Session,
    limiter: RateLimiter | None = None,
) -> TestClient:
    resolved_limiter = limiter or StubRateLimiter()

    def override_db() -> Generator[Session, None, None]:
        yield db

    def override_limiter() -> RateLimiter:
        return resolved_limiter

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_rate_limiter] = override_limiter
    return TestClient(app)


def _registration_payload(email: str, password: str = "correct-horse") -> dict[str, str]:
    return {
        "email": email,
        "password": password,
        "display_name": "  Credential User  ",
    }


def test_registration_is_generic_for_new_and_existing_email() -> None:
    with _make_db() as db:
        client = _client_with_db(db)
        email = f"register-{uuid4()}@example.com"
        payload = _registration_payload(email)

        first = client.post("/api/v1/auth/register", json=payload)
        second = client.post("/api/v1/auth/register", json=payload)

        users = db.scalars(select(User)).all()

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json() == {"accepted": True}
    assert second.json() == first.json()
    assert first.headers["cache-control"] == "no-store"
    assert second.headers["cache-control"] == "no-store"
    assert len(users) == 1
    assert users[0].email == email
    assert users[0].display_name == "Credential User"


def test_registration_returns_typed_password_policy_error() -> None:
    with _make_db() as db:
        response = _client_with_db(db).post(
            "/api/v1/auth/register",
            json=_registration_payload(
                f"weak-{uuid4()}@example.com",
                password="short",
            ),
        )

    assert response.status_code == 422
    assert response.json() == {
        "code": "password_policy_violation",
        "message": "password_too_short",
    }
    assert response.headers["cache-control"] == "no-store"


def test_login_returns_session_and_session_authenticates_profile() -> None:
    with _make_db() as db:
        client = _client_with_db(db)
        email = f"login-{uuid4()}@example.com"
        password = "correct-horse"
        register = client.post(
            "/api/v1/auth/register",
            json=_registration_payload(email, password),
        )
        assert register.status_code == 202

        login = client.post(
            "/api/v1/auth/login",
            json={"identifier": email, "password": password},
        )
        assert login.status_code == 200
        assert login.headers["cache-control"] == "no-store"
        body = login.json()
        assert body["token_type"] == "bearer"
        assert body["expires_in_seconds"] > 0
        assert body["session_token"] != password

        profile = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {body['session_token']}"},
        )

    assert profile.status_code == 200
    assert profile.json()["email"] == email
    assert profile.json()["display_name"] == "Credential User"


def test_login_failure_is_generic_and_never_returns_token() -> None:
    with _make_db() as db:
        response = _client_with_db(db).post(
            "/api/v1/auth/login",
            json={
                "identifier": f"missing-{uuid4()}@example.com",
                "password": "not-the-password",
            },
        )

    assert response.status_code == 401
    assert response.json() == {"code": "invalid_credentials", "message": None}
    assert response.headers["cache-control"] == "no-store"
    assert "session_token" not in response.text


def test_credential_routes_return_retry_after_when_rate_limited() -> None:
    limiter = StubRateLimiter(
        RateLimitDecision(
            allowed=False,
            retry_after_seconds=42,
        )
    )
    with _make_db() as db:
        response = _client_with_db(db, limiter).post(
            "/api/v1/auth/login",
            json={
                "identifier": f"limited-{uuid4()}@example.com",
                "password": "not-the-password",
            },
        )

    assert response.status_code == 429
    assert response.json() == {"code": "rate_limited", "message": None}
    assert response.headers["retry-after"] == "42"
    assert response.headers["cache-control"] == "no-store"


def test_credential_routes_fail_closed_if_limiter_backend_is_unavailable() -> None:
    with _make_db() as db:
        response = _client_with_db(
            db,
            StubRateLimiter(unavailable=True),
        ).post(
            "/api/v1/auth/login",
            json={
                "identifier": f"unavailable-{uuid4()}@example.com",
                "password": "not-the-password",
            },
        )

    assert response.status_code == 503
    assert response.json() == {
        "code": "auth_service_unavailable",
        "message": None,
    }
    assert response.headers["cache-control"] == "no-store"


def test_redis_rate_limiter_is_distributed_and_hashes_subject_keys() -> None:
    redis_client = Redis.from_url(
        get_settings().redis_url,
        decode_responses=True,
    )
    scope = f"test-auth-{uuid4()}"
    subject = f"private-{uuid4()}@example.com"
    keys: list[str] = []

    try:
        limiter = RedisFixedWindowRateLimiter(redis_client)
        first = limiter.check(
            scope,
            subject,
            limit=2,
            window_seconds=60,
        )
        second = limiter.check(
            scope,
            subject,
            limit=2,
            window_seconds=60,
        )
        third = limiter.check(
            scope,
            subject,
            limit=2,
            window_seconds=60,
        )

        keys = list(
            redis_client.scan_iter(
                match=f"devforge:ratelimit:{scope}:*",
            )
        )
    finally:
        if keys:
            redis_client.delete(*keys)
        redis_client.close()

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds > 0
    assert len(keys) == 1
    assert subject not in keys[0]


def test_openapi_exposes_credential_contracts() -> None:
    schema = create_app().openapi()

    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/auth/login" in schema["paths"]
    assert "RegistrationAcceptedResponse" in schema["components"]["schemas"]
    assert "SessionTokenResponse" in schema["components"]["schemas"]

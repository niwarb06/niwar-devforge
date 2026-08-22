from collections.abc import Generator
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from devforge_core.api.auth import get_credential_rate_limiter
from devforge_core.auth.abuse import (
    RateLimitBackendUnavailable,
    RateLimitDecision,
)
from devforge_core.auth.models import Base, UserRole
from devforge_core.database import get_db
from devforge_core.main import create_app


class RecordingLimiter:
    def __init__(
        self,
        *,
        allowed: bool = True,
        retry_after_seconds: int = 1,
        fail: bool = False,
    ) -> None:
        self.allowed = allowed
        self.retry_after_seconds = retry_after_seconds
        self.fail = fail
        self.calls: list[tuple[str, int, int]] = []

    async def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
        self.calls.append((key, limit, window_seconds))
        if self.fail:
            raise RateLimitBackendUnavailable()
        return RateLimitDecision(
            allowed=self.allowed,
            retry_after_seconds=self.retry_after_seconds,
        )


def _make_db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def _client_with_db(db: Session, limiter: RecordingLimiter) -> TestClient:
    def override_db() -> Generator[Session, None, None]:
        yield db

    def override_limiter() -> RecordingLimiter:
        return limiter

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_credential_rate_limiter] = override_limiter
    return TestClient(app)


def _registration_payload(email: str) -> dict[str, str]:
    return {
        "email": email,
        "password": "correct-horse-battery-staple",
        "display_name": "Credential User",
    }


def test_registration_persists_default_role_and_never_returns_session_token() -> None:
    with _make_db() as db:
        limiter = RecordingLimiter()
        client = _client_with_db(db, limiter)
        email = f"register-{uuid4()}@example.com"

        response = client.post("/api/v1/auth/register", json=_registration_payload(email))

        assert response.status_code == 201
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["email"] == email
        assert "session_token" not in response.json()
        roles = db.scalars(select(UserRole.role)).all()
        assert roles == ["user"]


def test_registration_duplicate_uses_generic_public_error() -> None:
    with _make_db() as db:
        client = _client_with_db(db, RecordingLimiter())
        email = f"duplicate-{uuid4()}@example.com"
        payload = _registration_payload(email)

        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        duplicate = client.post("/api/v1/auth/register", json=payload)

        assert duplicate.status_code == 400
        assert duplicate.json() == {"code": "registration_failed", "message": None}


def test_login_returns_mobile_api_bearer_session_and_unlocks_profile() -> None:
    with _make_db() as db:
        client = _client_with_db(db, RecordingLimiter())
        email = f"login-{uuid4()}@example.com"
        password = "correct-horse-battery-staple"
        payload = _registration_payload(email)
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201

        login = client.post(
            "/api/v1/auth/session",
            json={"identifier": email, "password": password},
        )

        assert login.status_code == 200
        assert login.headers["cache-control"] == "no-store"
        body = login.json()
        assert body["token_type"] == "bearer"
        assert body["expires_in_seconds"] > 0
        assert body["session_token"]

        profile = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {body['session_token']}"},
        )
        assert profile.status_code == 200
        assert profile.json()["email"] == email


def test_login_failure_is_generic_for_wrong_credentials() -> None:
    with _make_db() as db:
        client = _client_with_db(db, RecordingLimiter())
        response = client.post(
            "/api/v1/auth/session",
            json={"identifier": "missing@example.com", "password": "wrong-password"},
        )

        assert response.status_code == 401
        assert response.json() == {"code": "invalid_credentials", "message": None}


def test_rate_limit_keys_hide_client_and_identifier_and_denial_sets_retry_after() -> None:
    with _make_db() as db:
        allowed = RecordingLimiter()
        client = _client_with_db(db, allowed)
        email = f"privacy-{uuid4()}@example.com"
        response = client.post("/api/v1/auth/register", json=_registration_payload(email))
        assert response.status_code == 201
        assert len(allowed.calls) == 2
        assert all(email not in key for key, _limit, _window in allowed.calls)
        assert all("testclient" not in key for key, _limit, _window in allowed.calls)
        assert any(":ip:" in key for key, _limit, _window in allowed.calls)
        assert any(":identifier:" in key for key, _limit, _window in allowed.calls)

        denied = RecordingLimiter(allowed=False, retry_after_seconds=17)
        denied_client = _client_with_db(db, denied)
        limited = denied_client.post(
            "/api/v1/auth/session",
            json={"identifier": email, "password": "irrelevant-password"},
        )
        assert limited.status_code == 429
        assert limited.headers["retry-after"] == "17"
        assert limited.json()["code"] == "rate_limited"


def test_rate_limit_backend_failure_fails_credentials_closed() -> None:
    with _make_db() as db:
        client = _client_with_db(db, RecordingLimiter(fail=True))
        response = client.post(
            "/api/v1/auth/session",
            json={"identifier": "user@example.com", "password": "irrelevant-password"},
        )

        assert response.status_code == 503
        assert response.json() == {"code": "temporarily_unavailable", "message": None}


def test_openapi_exposes_abuse_protected_credential_contracts() -> None:
    schema = create_app().openapi()

    register = schema["paths"]["/api/v1/auth/register"]["post"]
    session = schema["paths"]["/api/v1/auth/session"]["post"]
    assert "429" in register["responses"]
    assert "503" in register["responses"]
    assert "429" in session["responses"]
    assert "SessionResponse" in str(session["responses"])

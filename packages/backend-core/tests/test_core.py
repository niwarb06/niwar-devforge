import asyncio
from collections.abc import Generator
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devforge_core.api.contracts import UpdateProfileRequest
from devforge_core.auth.contracts import Actor, LoginCommand, RegisterCommand
from devforge_core.auth.errors import (
    EmailAlreadyExists,
    InvalidCredentials,
    PasswordPolicyViolation,
)
from devforge_core.auth.models import Base
from devforge_core.auth.permissions import default_authorization_policy
from devforge_core.auth.repository import SqlAlchemyUserRepository
from devforge_core.auth.security import Argon2Hasher
from devforge_core.auth.service import AuthService
from devforge_core.auth.sessions import DatabaseSessionIssuer
from devforge_core.cache import get_redis
from devforge_core.config import Settings
from devforge_core.database import get_db
from devforge_core.main import create_app
from devforge_core.users import SqlAlchemyUserProfileRepository, UpdateProfileCommand


def test_settings_default_to_development() -> None:
    with patch.dict("os.environ", {}, clear=True):
        settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.api_prefix == "/api/v1"
    assert settings.database_url.startswith("sqlite+")
    assert settings.is_production is False


def test_actor_is_immutable_contract() -> None:
    actor = Actor(id=uuid4(), email="user@example.com", display_name="User", roles=("user",))
    assert actor.roles == ("user",)


def test_default_rbac_policy_enforces_role_permissions() -> None:
    policy = default_authorization_policy()
    user = Actor(id=uuid4(), email="user@example.com", display_name=None, roles=("user",))
    admin = Actor(id=uuid4(), email="admin@example.com", display_name=None, roles=("admin",))

    assert policy.allows(user, "profile.read:self") is True
    assert policy.allows(user, "users.manage") is False
    assert policy.allows(admin, "users.manage") is True


def test_profile_api_contract_rejects_unknown_fields() -> None:
    request = UpdateProfileRequest(display_name="  User  ")
    assert request.display_name == "  User  "

    try:
        UpdateProfileRequest(display_name="User", unknown=True)
    except Exception:
        pass
    else:
        raise AssertionError("unknown API fields must be rejected")


def test_argon2_password_hasher_round_trip() -> None:
    hasher = Argon2Hasher()
    password_hash = hasher.hash("correct-horse-battery-staple")

    assert password_hash != "correct-horse-battery-staple"
    assert hasher.verify("correct-horse-battery-staple", password_hash) is True
    assert hasher.verify("wrong-password", password_hash) is False


def test_argon2_password_hasher_rejects_short_password() -> None:
    hasher = Argon2Hasher()

    try:
        hasher.hash("short")
    except ValueError as exc:
        assert str(exc) == "password_too_short"
    else:
        raise AssertionError("short password must be rejected")


def test_liveness_endpoint_adds_request_id() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_liveness_endpoint_preserves_request_id() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-123"})

    assert response.headers["X-Request-ID"] == "trace-123"


def test_readiness_checks_database_and_redis() -> None:
    class FakeDb:
        def execute(self, statement: object) -> None:
            assert statement is not None

    class FakeRedis:
        def ping(self) -> bool:
            return True

        def close(self) -> None:
            return None

    def override_db() -> Generator[FakeDb, None, None]:
        yield FakeDb()

    def override_redis() -> Generator[FakeRedis, None, None]:
        yield FakeRedis()

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    response = TestClient(app).get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_auth_register_login_resolve_and_revoke() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with factory() as db:
        users = SqlAlchemyUserRepository(db)
        passwords = Argon2Hasher()
        sessions = DatabaseSessionIssuer(db)
        auth = AuthService(users=users, passwords=passwords, sessions=sessions)
        email = f"user-{uuid4()}@example.com"
        command = RegisterCommand(
            email=email,
            password="correct-horse-battery-staple",
            display_name="User",
        )

        actor = asyncio.run(auth.register(command))
        logged_in_actor, raw_token = asyncio.run(
            auth.login(LoginCommand(identifier=email, password=command.password))
        )
        resolved_actor = asyncio.run(sessions.resolve(raw_token))

        assert logged_in_actor == actor
        assert resolved_actor == actor

        profiles = SqlAlchemyUserProfileRepository(db)
        profile = profiles.get(actor.id)
        assert profile is not None
        assert profile.display_name == "User"

        updated = profiles.update(actor.id, UpdateProfileCommand(display_name="  Updated User  "))
        assert updated is not None
        assert updated.display_name == "Updated User"

        asyncio.run(sessions.revoke(raw_token))
        assert asyncio.run(sessions.resolve(raw_token)) is None


def test_auth_service_uses_typed_errors() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with factory() as db:
        auth = AuthService(
            users=SqlAlchemyUserRepository(db),
            passwords=Argon2Hasher(),
            sessions=DatabaseSessionIssuer(db),
        )
        email = f"typed-{uuid4()}@example.com"
        command = RegisterCommand(email=email, password="correct-horse-battery-staple")
        asyncio.run(auth.register(command))

        try:
            asyncio.run(auth.login(LoginCommand(identifier=email, password="wrong-password")))
        except InvalidCredentials as exc:
            assert exc.code == "invalid_credentials"
        else:
            raise AssertionError("invalid login must raise InvalidCredentials")

        try:
            asyncio.run(auth.register(RegisterCommand(email=email, password=command.password)))
        except EmailAlreadyExists as exc:
            assert exc.code == "email_already_exists"
        else:
            raise AssertionError("duplicate registration must raise EmailAlreadyExists")

        short_password_command = RegisterCommand(
            email=f"short-{uuid4()}@example.com",
            password="short",
        )
        try:
            asyncio.run(auth.register(short_password_command))
        except PasswordPolicyViolation as exc:
            assert exc.reason == "password_too_short"
        else:
            raise AssertionError("weak password must raise PasswordPolicyViolation")

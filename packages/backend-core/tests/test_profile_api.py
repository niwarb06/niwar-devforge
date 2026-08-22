import asyncio
from collections.abc import Generator
from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from devforge_core.auth.contracts import Actor
from devforge_core.auth.models import Base, User, UserRole
from devforge_core.auth.sessions import DatabaseSessionIssuer
from devforge_core.database import get_db
from devforge_core.main import create_app


def _make_db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def _client_with_db(db: Session) -> TestClient:
    def override_db() -> Generator[Session, None, None]:
        yield db

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def _create_session(db: Session, role: str = "user") -> tuple[User, str]:
    user = User(
        email=f"profile-{uuid4()}@example.com",
        display_name="Profile User",
        password_hash="hash",
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role=role))
    db.commit()
    db.refresh(user)

    actor = Actor(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=(role,),
    )
    token = asyncio.run(DatabaseSessionIssuer(db, ttl=timedelta(hours=1)).issue(actor))
    return user, token


def test_profile_route_requires_authentication() -> None:
    with _make_db() as db:
        response = _client_with_db(db).get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json() == {"code": "not_authenticated", "message": None}


def test_profile_routes_use_persisted_session_roles() -> None:
    with _make_db() as db:
        user, token = _create_session(db, role="admin")
        client = _client_with_db(db)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["user_id"] == str(user.id)
        assert response.json()["display_name"] == "Profile User"

        updated = client.patch(
            "/api/v1/users/me/profile",
            headers=headers,
            json={"display_name": "  Updated Profile  "},
        )
        assert updated.status_code == 200
        assert updated.json()["display_name"] == "Updated Profile"


def test_logout_revokes_current_session() -> None:
    with _make_db() as db:
        _user, token = _create_session(db)
        client = _client_with_db(db)
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.delete("/api/v1/auth/session", headers=headers)
        assert logout.status_code == 204

        after_logout = client.get("/api/v1/users/me", headers=headers)
        assert after_logout.status_code == 401
        assert after_logout.json()["code"] == "not_authenticated"


def test_openapi_exposes_profile_contract_and_session_security() -> None:
    schema = create_app().openapi()

    assert "/api/v1/users/me" in schema["paths"]
    assert "/api/v1/users/me/profile" in schema["paths"]
    assert "/api/v1/auth/session" in schema["paths"]
    assert "DevForgeSession" in schema["components"]["securitySchemes"]

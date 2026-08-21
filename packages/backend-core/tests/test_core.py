from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from devforge_core.auth.contracts import Actor
from devforge_core.auth.security import Argon2Hasher
from devforge_core.config import Settings
from devforge_core.main import create_app


def test_settings_default_to_development() -> None:
    with patch.dict("os.environ", {}, clear=True):
        settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.api_prefix == "/api/v1"
    assert settings.is_production is False


def test_actor_is_immutable_contract() -> None:
    actor = Actor(id=uuid4(), email="user@example.com", display_name="User", roles=("user",))
    assert actor.roles == ("user",)


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


def test_liveness_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

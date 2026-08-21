from uuid import uuid4

from fastapi.testclient import TestClient

from src.devforge_core.auth.contracts import Actor
from src.devforge_core.config import Settings
from src.devforge_core.main import create_app


def test_settings_default_to_development() -> None:
    settings = Settings(_env_file=None)
    assert settings.environment == "development"
    assert settings.api_prefix == "/api/v1"
    assert settings.is_production is False


def test_actor_is_immutable_contract() -> None:
    actor = Actor(id=uuid4(), email="user@example.com", display_name="User", roles=("user",))
    assert actor.roles == ("user",)


def test_liveness_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

import logging
from uuid import UUID

from fastapi.testclient import TestClient

from devforge_core.main import create_app
from devforge_core.observability import configure_logging


def test_malformed_request_id_is_replaced() -> None:
    client = TestClient(create_app())
    supplied = "unsafe request id"

    response = client.get("/api/v1/health/live", headers={"X-Request-ID": supplied})

    assert response.status_code == 200
    resolved = response.headers["X-Request-ID"]
    assert resolved != supplied
    UUID(resolved)


def test_oversized_request_id_is_replaced() -> None:
    client = TestClient(create_app())
    supplied = "a" * 129

    response = client.get("/api/v1/health/live", headers={"X-Request-ID": supplied})

    resolved = response.headers["X-Request-ID"]
    assert resolved != supplied
    UUID(resolved)


def test_configure_logging_is_idempotent_and_preserves_root_handlers() -> None:
    root = logging.getLogger()
    devforge = logging.getLogger("devforge")
    sentinel = logging.NullHandler()
    original_root_handlers = list(root.handlers)
    original_devforge_handlers = list(devforge.handlers)
    original_level = devforge.level
    original_propagate = devforge.propagate

    try:
        root.addHandler(sentinel)
        devforge.handlers.clear()

        configure_logging("INFO")
        configure_logging("DEBUG")

        owned_handlers = [
            handler
            for handler in devforge.handlers
            if getattr(handler, "_devforge_json_handler", False)
        ]
        assert sentinel in root.handlers
        assert len(owned_handlers) == 1
        assert devforge.level == logging.DEBUG
        assert devforge.propagate is False
    finally:
        root.handlers[:] = original_root_handlers
        devforge.handlers[:] = original_devforge_handlers
        devforge.setLevel(original_level)
        devforge.propagate = original_propagate

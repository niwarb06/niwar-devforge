#!/usr/bin/env python3
"""Verify the backend OpenAPI auth contract and generated Dart proof stay in parity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ParityError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ParityError(f"cannot read valid JSON schema: {path}") from exc
    if not isinstance(data, dict):
        raise ParityError("OpenAPI root must be an object")
    return data


def _operation(schema: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    paths = schema.get("paths")
    if not isinstance(paths, dict):
        raise ParityError("OpenAPI paths object is missing")
    path_item = paths.get(path)
    if not isinstance(path_item, dict):
        raise ParityError(f"missing path: {path}")
    operation = path_item.get(method.lower())
    if not isinstance(operation, dict):
        raise ParityError(f"missing operation: {method.upper()} {path}")
    return operation


def _json_schema_from_content(container: dict[str, Any], label: str) -> dict[str, Any]:
    content = container.get("content")
    if not isinstance(content, dict):
        raise ParityError(f"{label} has no content object")
    media = content.get("application/json")
    if not isinstance(media, dict):
        raise ParityError(f"{label} has no application/json content")
    value = media.get("schema")
    if not isinstance(value, dict):
        raise ParityError(f"{label} has no JSON schema")
    return value


def _ref_name(value: dict[str, Any], label: str) -> str:
    ref = value.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        raise ParityError(f"{label} must use a component schema reference")
    return ref.rsplit("/", 1)[-1]


def _request_ref(operation: dict[str, Any], label: str) -> str:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        raise ParityError(f"{label} has no request body")
    return _ref_name(_json_schema_from_content(body, f"{label} request"), label)


def _response_ref(operation: dict[str, Any], status: int, label: str) -> str:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        raise ParityError(f"{label} has no responses object")
    response = responses.get(str(status))
    if not isinstance(response, dict):
        raise ParityError(f"{label} is missing response {status}")
    return _ref_name(
        _json_schema_from_content(response, f"{label} response {status}"),
        label,
    )


def _require_status(operation: dict[str, Any], status: int, label: str) -> None:
    responses = operation.get("responses")
    if not isinstance(responses, dict) or str(status) not in responses:
        raise ParityError(f"{label} is missing response {status}")


def _require_bearer(operation: dict[str, Any], label: str) -> None:
    security = operation.get("security")
    if not isinstance(security, list):
        raise ParityError(f"{label} must declare security")
    for requirement in security:
        if isinstance(requirement, dict) and "DevForgeSession" in requirement:
            return
    raise ParityError(f"{label} must require DevForgeSession")


def _component(schema: dict[str, Any], name: str) -> dict[str, Any]:
    components = schema.get("components")
    if not isinstance(components, dict):
        raise ParityError("OpenAPI components object is missing")
    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        raise ParityError("OpenAPI component schemas are missing")
    value = schemas.get(name)
    if not isinstance(value, dict):
        raise ParityError(f"missing component schema: {name}")
    return value


def _properties(component: dict[str, Any], name: str) -> dict[str, Any]:
    properties = component.get("properties")
    if not isinstance(properties, dict):
        raise ParityError(f"{name} has no properties object")
    return properties


def _require_fields(component: dict[str, Any], name: str, expected: set[str]) -> None:
    required = component.get("required", [])
    if not isinstance(required, list):
        raise ParityError(f"{name}.required must be an array")
    missing = expected - set(required)
    if missing:
        raise ParityError(f"{name} is missing required fields: {sorted(missing)}")


def _string_schema(value: dict[str, Any], field: str) -> dict[str, Any]:
    if value.get("type") == "string":
        return value

    any_of = value.get("anyOf")
    if isinstance(any_of, list):
        string_variants = [
            variant
            for variant in any_of
            if isinstance(variant, dict) and variant.get("type") == "string"
        ]
        if len(string_variants) == 1:
            return string_variants[0]

    raise ParityError(f"{field} must include exactly one string schema")


def _require_string_bounds(
    properties: dict[str, Any],
    field: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> None:
    value = properties.get(field)
    if not isinstance(value, dict):
        raise ParityError(f"missing property: {field}")
    string_value = _string_schema(value, field)
    if minimum is not None and string_value.get("minLength") != minimum:
        raise ParityError(f"{field}.minLength changed from {minimum}")
    if maximum is not None and string_value.get("maxLength") != maximum:
        raise ParityError(f"{field}.maxLength changed from {maximum}")


def _verify_schema(schema: dict[str, Any]) -> None:
    openapi_version = schema.get("openapi")
    if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
        raise ParityError("expected an OpenAPI 3.x schema")

    components = schema.get("components")
    if not isinstance(components, dict):
        raise ParityError("OpenAPI components object is missing")
    security_schemes = components.get("securitySchemes")
    if not isinstance(security_schemes, dict):
        raise ParityError("securitySchemes are missing")
    bearer = security_schemes.get("DevForgeSession")
    if not isinstance(bearer, dict):
        raise ParityError("DevForgeSession security scheme is missing")
    if bearer.get("type") != "http" or str(bearer.get("scheme", "")).lower() != "bearer":
        raise ParityError("DevForgeSession must remain an HTTP bearer scheme")

    register = _operation(schema, "/api/v1/auth/register", "post")
    login = _operation(schema, "/api/v1/auth/session", "post")
    logout = _operation(schema, "/api/v1/auth/session", "delete")
    me = _operation(schema, "/api/v1/users/me", "get")
    update_profile = _operation(schema, "/api/v1/users/me/profile", "patch")

    if _request_ref(register, "register") != "RegisterRequest":
        raise ParityError("register request contract changed")
    if _response_ref(register, 201, "register") != "UserProfileResponse":
        raise ParityError("register response contract changed")
    if _request_ref(login, "login") != "LoginRequest":
        raise ParityError("login request contract changed")
    if _response_ref(login, 200, "login") != "SessionResponse":
        raise ParityError("login response contract changed")
    _require_status(logout, 204, "logout")
    if _response_ref(me, 200, "current profile") != "UserProfileResponse":
        raise ParityError("current-profile response contract changed")
    if _request_ref(update_profile, "update profile") != "UpdateProfileRequest":
        raise ParityError("profile-update request contract changed")
    if _response_ref(update_profile, 200, "update profile") != "UserProfileResponse":
        raise ParityError("profile-update response contract changed")

    for operation, label in (
        (logout, "logout"),
        (me, "current profile"),
        (update_profile, "update profile"),
    ):
        _require_bearer(operation, label)

    login_schema = _component(schema, "LoginRequest")
    _require_fields(login_schema, "LoginRequest", {"identifier", "password"})
    login_properties = _properties(login_schema, "LoginRequest")
    _require_string_bounds(login_properties, "identifier", minimum=1, maximum=320)
    _require_string_bounds(login_properties, "password", minimum=1, maximum=1024)

    register_schema = _component(schema, "RegisterRequest")
    _require_fields(register_schema, "RegisterRequest", {"email", "password"})
    register_properties = _properties(register_schema, "RegisterRequest")
    _require_string_bounds(register_properties, "email", minimum=3, maximum=320)
    _require_string_bounds(register_properties, "password", minimum=1, maximum=1024)
    _require_string_bounds(register_properties, "display_name", maximum=200)

    update_schema = _component(schema, "UpdateProfileRequest")
    update_properties = _properties(update_schema, "UpdateProfileRequest")
    _require_string_bounds(update_properties, "display_name", maximum=200)

    session_schema = _component(schema, "SessionResponse")
    _require_fields(
        session_schema,
        "SessionResponse",
        {"session_token", "expires_in_seconds"},
    )
    session_properties = _properties(session_schema, "SessionResponse")
    token_type = session_properties.get("token_type")
    if not isinstance(token_type, dict) or token_type.get("const") != "bearer":
        if not isinstance(token_type, dict) or token_type.get("enum") != ["bearer"]:
            raise ParityError("SessionResponse.token_type must remain bearer")
    expiry = session_properties.get("expires_in_seconds")
    if not isinstance(expiry, dict) or expiry.get("exclusiveMinimum") != 0:
        raise ParityError("SessionResponse.expires_in_seconds must remain > 0")

    profile_schema = _component(schema, "UserProfileResponse")
    _require_fields(
        profile_schema,
        "UserProfileResponse",
        {"user_id", "email", "display_name", "is_active"},
    )
    profile_properties = _properties(profile_schema, "UserProfileResponse")
    user_id = profile_properties.get("user_id")
    if not isinstance(user_id, dict) or user_id.get("format") != "uuid":
        raise ParityError("UserProfileResponse.user_id must remain a UUID")


def _verify_generated(generated: Path) -> None:
    pubspec = generated / "pubspec.yaml"
    lib_dir = generated / "lib"
    if not pubspec.is_file() or not lib_dir.is_dir():
        raise ParityError("generated Dart package is incomplete")

    dart_files = sorted(lib_dir.rglob("*.dart"))
    if not dart_files:
        raise ParityError("generated Dart package contains no library sources")

    corpus_parts: list[str] = []
    for path in dart_files:
        try:
            corpus_parts.append(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParityError(f"cannot read generated source: {path}") from exc
    corpus = "\n".join(corpus_parts)

    markers = (
        "/api/v1/auth/register",
        "/api/v1/auth/session",
        "/api/v1/users/me",
        "/api/v1/users/me/profile",
        "LoginRequest",
        "RegisterRequest",
        "SessionResponse",
        "UpdateProfileRequest",
        "UserProfileResponse",
    )
    missing = [marker for marker in markers if marker not in corpus]
    if missing:
        raise ParityError(f"generated Dart client is missing markers: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    args = parser.parse_args()

    try:
        schema = _load_json(args.schema)
        _verify_schema(schema)
        _verify_generated(args.generated)
    except ParityError as exc:
        raise SystemExit(f"OpenAPI Dart parity check failed: {exc}") from exc

    print("OpenAPI Dart parity check passed")


if __name__ == "__main__":
    main()

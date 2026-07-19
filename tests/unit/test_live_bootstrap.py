from __future__ import annotations

import json

import httpx
import pytest

from tests.live.bootstrap import BootstrapApiClient, SecretString, TestIdentity
from tests.live.exceptions import LiveSetupError


def test_secret_string_redacts_repr_and_str() -> None:
    secret = SecretString("super-secret-value")
    assert "super-secret-value" not in repr(secret)
    assert str(secret) == "***"
    assert secret.reveal() == "super-secret-value"


def test_test_identity_repr_redacts_secrets() -> None:
    identity = TestIdentity(
        email="user@localhost",
        user_id="user-1",
        pat=SecretString("pat-value"),
    )
    rendered = repr(identity)
    assert "pat-value" not in rendered
    assert "SecretString" in rendered


def _install_transport(monkeypatch: pytest.MonkeyPatch, transport: httpx.MockTransport) -> None:
    original_client = httpx.Client

    def factory(**kwargs: object) -> httpx.Client:
        return original_client(
            transport=transport,
            base_url=str(kwargs["base_url"]),
            timeout=kwargs.get("timeout", 5.0),  # type: ignore[arg-type]
        )

    monkeypatch.setattr("tests.live.bootstrap.httpx.Client", factory)


def test_bootstrap_sequence_and_status_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode()) if request.content else {}
        calls.append((request.method, request.url.path, payload))
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/auth/verify-code":
            return httpx.Response(200, json={"token": "jwt-secret", "user_id": "user-1"})
        if request.url.path == "/api/tokens":
            return httpx.Response(
                201, json={"token": "pat-secret", "id": "pat-1", "user_id": "user-1"}
            )
        if request.url.path == "/api/workspaces":
            slug = payload["slug"]
            return httpx.Response(
                201, json={"id": f"ws-{slug}", "name": payload["name"], "slug": slug}
            )
        raise AssertionError(request.url.path)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    secrets: list[str] = []
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", secrets)
    identity, primary, secondary = client.bootstrap()

    assert [path for _, path, _ in calls] == [
        "/auth/send-code",
        "/auth/verify-code",
        "/api/tokens",
        "/api/workspaces",
        "/api/workspaces",
    ]
    assert calls[1][2] == {"email": client.email, "code": "888888"}
    assert primary.id.startswith("ws-")
    assert secondary.id.startswith("ws-")
    assert "pat-secret" not in repr(identity)


def test_bootstrap_failure_redacts_secrets_in_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/auth/verify-code":
            return httpx.Response(200, json={"token": "jwt-secret"})
        if request.url.path == "/api/tokens":
            return httpx.Response(500, text="jwt-secret leaked")
        return httpx.Response(404)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    with pytest.raises(LiveSetupError) as exc:
        client.bootstrap()
    assert "jwt-secret" not in str(exc.value)


def test_bootstrap_uses_jwt_not_pat_for_workspace_create(monkeypatch: pytest.MonkeyPatch) -> None:
    auth_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/auth/verify-code":
            return httpx.Response(200, json={"token": "jwt-secret", "user_id": "user-1"})
        if request.url.path == "/api/tokens":
            return httpx.Response(201, json={"token": "pat-secret", "id": "pat-1"})
        if request.url.path == "/api/workspaces":
            auth_headers.append(request.headers.get("Authorization"))
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201, json={"id": "ws-1", "name": payload["name"], "slug": payload["slug"]}
            )
        raise AssertionError(request.url.path)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", ["pat-secret"])
    _, _, _ = client.bootstrap()
    assert auth_headers == ["Bearer jwt-secret", "Bearer jwt-secret"]
    assert all(header != "Bearer pat-secret" for header in auth_headers if header is not None)

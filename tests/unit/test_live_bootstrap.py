from __future__ import annotations

import json

import httpx
import pytest

from tests.live.backend import BootstrapApiClient
from tests.live.environment import LiveSetupError, ResourceAbsentError, SecretString, TestIdentity
from tests.live.resources import ResourceRegistry


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

    monkeypatch.setattr("tests.live.backend.httpx.Client", factory)


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
        "/auth/verify-code",
        "/api/tokens",
        "/api/workspaces",
        "/api/workspaces",
    ]
    assert calls[0][2] == {"email": client.email, "code": "888888"}
    assert identity.user_id == "user-1"
    assert primary.id.startswith("ws-")
    assert secondary is not None
    assert secondary.id.startswith("ws-")
    assert "pat-secret" not in repr(identity)


def test_bootstrap_falls_back_to_send_code_when_verify_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/auth/verify-code":
            if calls.count("/auth/verify-code") == 1:
                return httpx.Response(400, json={"error": "code not sent"})
            return httpx.Response(200, json={"token": "jwt-secret", "user_id": "user-1"})
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/api/tokens":
            return httpx.Response(
                201, json={"token": "pat-secret", "id": "pat-1", "user_id": "user-1"}
            )
        if request.url.path == "/api/workspaces":
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201,
                json={
                    "id": f"ws-{payload['slug']}",
                    "name": payload["name"],
                    "slug": payload["slug"],
                },
            )
        raise AssertionError(request.url.path)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    client.bootstrap()
    assert calls[:3] == ["/auth/verify-code", "/auth/send-code", "/auth/verify-code"]


def test_bootstrap_retries_send_code_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    send_attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal send_attempts
        if request.url.path == "/auth/verify-code":
            if send_attempts == 0:
                return httpx.Response(400, json={"error": "code not sent"})
            return httpx.Response(200, json={"token": "jwt-secret", "user_id": "user-1"})
        if request.url.path == "/auth/send-code":
            send_attempts += 1
            if send_attempts == 1:
                return httpx.Response(429, text="please wait before requesting another code")
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/api/tokens":
            return httpx.Response(
                201, json={"token": "pat-secret", "id": "pat-1", "user_id": "user-1"}
            )
        if request.url.path == "/api/workspaces":
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201,
                json={
                    "id": f"ws-{payload['slug']}",
                    "name": payload["name"],
                    "slug": payload["slug"],
                },
            )
        raise AssertionError(request.url.path)

    sleeps: list[float] = []
    monkeypatch.setattr("tests.live.backend.time.sleep", sleeps.append)
    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    client.bootstrap()
    assert send_attempts == 2
    assert len(sleeps) == 1


def test_bootstrap_send_code_honors_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    send_attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal send_attempts
        if request.url.path == "/auth/verify-code":
            if send_attempts == 0:
                return httpx.Response(400, json={"error": "code not sent"})
            return httpx.Response(200, json={"token": "jwt-secret", "user_id": "user-1"})
        if request.url.path == "/auth/send-code":
            send_attempts += 1
            if send_attempts == 1:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "3"},
                    text="please wait before requesting another code",
                )
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/api/tokens":
            return httpx.Response(
                201, json={"token": "pat-secret", "id": "pat-1", "user_id": "user-1"}
            )
        if request.url.path == "/api/workspaces":
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201,
                json={
                    "id": f"ws-{payload['slug']}",
                    "name": payload["name"],
                    "slug": payload["slug"],
                },
            )
        raise AssertionError(request.url.path)

    sleeps: list[float] = []
    monkeypatch.setattr("tests.live.backend.time.sleep", sleeps.append)
    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    client.bootstrap()
    assert send_attempts == 2
    assert sleeps[0] >= 3.0


def test_bootstrap_verify_without_token_falls_back_to_send_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/auth/verify-code":
            if calls.count("/auth/verify-code") == 1:
                return httpx.Response(200, json={"ok": True})
            return httpx.Response(200, json={"token": "jwt-secret", "user_id": "user-1"})
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/api/tokens":
            return httpx.Response(
                201, json={"token": "pat-secret", "id": "pat-1", "user_id": "user-1"}
            )
        if request.url.path == "/api/workspaces":
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201,
                json={
                    "id": f"ws-{payload['slug']}",
                    "name": payload["name"],
                    "slug": payload["slug"],
                },
            )
        raise AssertionError(request.url.path)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    client.bootstrap()
    assert calls[:3] == ["/auth/verify-code", "/auth/send-code", "/auth/verify-code"]


def test_bootstrap_resolves_user_id_from_nested_verify_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/auth/verify-code":
            return httpx.Response(
                200,
                json={"token": "jwt-secret", "user": {"id": "user-nested", "email": "a@b.c"}},
            )
        if request.url.path == "/api/tokens":
            return httpx.Response(201, json={"token": "pat-secret", "id": "pat-1"})
        if request.url.path == "/api/workspaces":
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201,
                json={
                    "id": f"ws-{payload['slug']}",
                    "name": payload["name"],
                    "slug": payload["slug"],
                },
            )
        raise AssertionError(request.url.path)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    identity, _, _ = client.bootstrap()
    assert identity.user_id == "user-nested"


def test_bootstrap_resolves_user_id_from_api_me_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/send-code":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/auth/verify-code":
            return httpx.Response(200, json={"token": "jwt-secret"})
        if request.url.path == "/api/tokens":
            return httpx.Response(201, json={"token": "pat-secret", "id": "pat-1"})
        if request.url.path == "/api/me":
            assert request.headers.get("Authorization") == "Bearer jwt-secret"
            return httpx.Response(200, json={"id": "user-from-me", "email": "a@b.c"})
        if request.url.path == "/api/workspaces":
            payload = json.loads(request.content.decode())
            return httpx.Response(
                201,
                json={
                    "id": f"ws-{payload['slug']}",
                    "name": payload["name"],
                    "slug": payload["slug"],
                },
            )
        raise AssertionError(request.url.path)

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    client = BootstrapApiClient("http://127.0.0.1:8080", "run123", [])
    identity, _, _ = client.bootstrap()
    assert identity.user_id == "user-from-me"


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


def test_cleanup_runs_in_reverse_registration_order() -> None:
    order: list[str] = []
    registry = ResourceRegistry()
    registry.defer(key="project", cleanup=lambda: order.append("project"))
    registry.defer(key="issue", cleanup=lambda: order.append("issue"))
    registry.cleanup_all()
    assert order == ["issue", "project"]


def test_already_absent_is_tolerated() -> None:
    registry = ResourceRegistry()
    registry.defer(
        key="label",
        cleanup=lambda: (_ for _ in ()).throw(ResourceAbsentError()),
    )
    assert registry.cleanup_all() == []


def test_partial_failure_is_recorded() -> None:
    registry = ResourceRegistry()
    registry.defer(
        key="a",
        cleanup=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    failures = registry.cleanup_all()
    assert len(failures) == 1
    assert failures[0]["key"] == "a"


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

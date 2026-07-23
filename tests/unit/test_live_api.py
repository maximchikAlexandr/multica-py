"""Unit tests for tests.live.api.LiveApiClient — request/status/shape/redaction/delete-idempotency."""

from __future__ import annotations

import json

import httpx
import pytest

from tests.live.api import LiveApiClient, bootstrap_api_client, request_json
from tools.live_support.environment import Environment


def _mock_client(handler: httpx.MockTransport, api_key: str = "test-key") -> LiveApiClient:
    client = LiveApiClient(
        base_url="https://api.test",
        env=Environment(api_key=api_key, workspace=None, profile="extended", extra={}),
    )
    client._client = httpx.Client(
        transport=handler, base_url="https://api.test", headers=client._client.headers
    )
    return client


def test_get_returns_response_status_and_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "id": "x1"})

    client = _mock_client(httpx.MockTransport(handler))
    response = client.get("/items/x1")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "id": "x1"}
    client.close()


def test_request_dispatches_all_methods() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.method)
        return httpx.Response(200, json={})

    client = _mock_client(httpx.MockTransport(handler))
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        client.request(method, f"/{method.lower()}")
    assert seen == ["GET", "POST", "PUT", "PATCH", "DELETE"]
    client.close()


def test_request_json_raises_on_non_200() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found: " * 50)

    client = _mock_client(httpx.MockTransport(handler))
    with pytest.raises(AssertionError, match="404"):
        request_json(client, "GET", "/missing")
    client.close()


def test_request_json_rejects_non_dict_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["a", "b", "c"])

    client = _mock_client(httpx.MockTransport(handler))
    with pytest.raises(AssertionError, match="expected dict body"):
        request_json(client, "GET", "/list")
    client.close()


def test_request_json_rejects_secret_leak() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text=json.dumps({"data": "ok", "token": "Bearer abc.defghijklmnopqrstuv"})
        )

    client = _mock_client(httpx.MockTransport(handler))
    with pytest.raises(AssertionError, match="secrets"):
        request_json(client, "GET", "/leak")
    client.close()


def test_delete_is_idempotent_no_second_call() -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(204)

    client = _mock_client(httpx.MockTransport(handler))
    assert client.delete("/items/abc").status_code == 204
    assert client.delete("/items/abc").status_code == 204
    assert call_count == 1
    client.close()


def test_delete_registers_only_on_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = _mock_client(httpx.MockTransport(handler))
    assert client.delete("/items/y").status_code == 500
    assert client.delete("/items/y").status_code == 500
    client.close()


def test_bootstrap_api_client_base_url_resolution() -> None:
    env_override = Environment(
        api_key="k",
        workspace=None,
        profile="extended",
        extra={"MULTICA_BASE_URL": "https://staging.test"},
    )
    client = bootstrap_api_client(env_override)
    assert client.base_url == "https://staging.test"
    client.close()
    env_default = Environment(api_key="k", workspace=None, profile="extended", extra={})
    client = bootstrap_api_client(env_default)
    assert client.base_url == "https://api.multica.ai"
    client.close()


def test_authorization_header_round_trip() -> None:
    seen_auth: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_auth.append(request.headers.get("Authorization", ""))
        return httpx.Response(200, json={})

    client = _mock_client(httpx.MockTransport(handler), api_key="my-secret")
    client.get("/whoami")
    assert seen_auth[0] == "Bearer my-secret"
    client.close()

from __future__ import annotations

import httpx
import pytest

from tools.live_support.environment import SecretString
from tools.live_support.oracle import DirectApiOracle

_PAT = SecretString("pat-secret")


def _install_transport(monkeypatch: pytest.MonkeyPatch, transport: httpx.MockTransport) -> None:
    original_client = httpx.Client

    def factory(**kwargs: object) -> httpx.Client:
        return original_client(
            transport=transport,
            base_url=str(kwargs["base_url"]),
            timeout=kwargs.get("timeout", 5.0),  # type: ignore[arg-type]
        )

    monkeypatch.setattr("tools.live_support.oracle.httpx.Client", factory)


def test_oracle_returns_raw_json_and_allowlisted_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer pat-secret"
        assert request.headers["X-Workspace-ID"] == "ws-1"
        return httpx.Response(
            200,
            json={"id": "lbl-1", "name": "bug"},
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer pat-secret",
                "X-Request-Id": "req-1",
            },
        )

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    with DirectApiOracle("http://127.0.0.1:8080", workspace_id="ws-1", pat=_PAT) as oracle:
        response = oracle.request("GET", "/api/labels/lbl-1")
        assert response.status_code == 200
        assert response.json_body == {"id": "lbl-1", "name": "bug"}
        assert "authorization" not in response.headers


def test_list_issues_page_requires_items_and_next_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"items": [{"id": "issue-1"}], "next_cursor": "cursor-2"},
        )

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    with DirectApiOracle("http://127.0.0.1:8080", workspace_id="ws-1", pat=_PAT) as oracle:
        items, next_cursor = oracle.list_issues_page(limit=10)
        assert items == [{"id": "issue-1"}]
        assert next_cursor == "cursor-2"


def test_list_issues_page_rejects_unpinned_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "issue-1"}])

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    with (
        DirectApiOracle("http://127.0.0.1:8080", workspace_id="ws-1", pat=_PAT) as oracle,
        pytest.raises(AssertionError, match="unexpected body"),
    ):
        oracle.list_issues_page(limit=10)


def test_list_comments_accepts_bare_array(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "c1", "content": "hello"}])

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    with DirectApiOracle("http://127.0.0.1:8080", workspace_id="ws-1", pat=_PAT) as oracle:
        assert oracle.list_comments("issue-1") == [{"id": "c1", "content": "hello"}]


def test_list_issue_labels_accepts_wrapped_object(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"labels": [{"id": "lbl-1", "name": "bug"}]})

    _install_transport(monkeypatch, httpx.MockTransport(handler))
    with DirectApiOracle("http://127.0.0.1:8080", workspace_id="ws-1", pat=_PAT) as oracle:
        assert oracle.list_issue_labels("issue-1") == [{"id": "lbl-1", "name": "bug"}]

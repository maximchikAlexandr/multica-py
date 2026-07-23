"""Direct HTTP oracle for live test assertions.

Migrated from ``tests.live.oracle`` per T068 (FR-022).  Owns the raw HTTP
client and response helpers that live tests use for arrange/assert/cleanup
without going through the SDK.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from urllib.parse import urlencode

import httpx

from tools.live_support.environment import SecretString

ALLOWLISTED_HEADERS = frozenset({"content-type", "x-request-id"})
JsonObject = dict[str, object]
JsonValue = object


class ResourceAbsentError(LookupError):
    """Deleted resource no longer exists — expected during cleanup."""


@dataclass(frozen=True, slots=True)
class OracleResponse:
    """Minimal raw HTTP response for oracle assertions."""

    status_code: int
    headers: dict[str, str]
    json_body: JsonValue | None
    text_excerpt: str | None


class DirectApiOracle:
    """Direct HTTP oracle for arrange, assert, and cleanup."""

    def __init__(
        self,
        server_url: str,
        *,
        workspace_id: str,
        pat: SecretString,
        timeout: float = 30.0,
    ) -> None:
        self._server_url = server_url.rstrip("/")
        self._workspace_id = workspace_id
        self._pat = pat
        self._timeout = timeout
        self._client = httpx.Client(base_url=self._server_url, timeout=self._timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> DirectApiOracle:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: JsonObject | None = None,
    ) -> OracleResponse:
        response = self._client.request(
            method,
            path,
            headers=self._json_headers(),
            json=json_body,
        )
        allowlisted = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in ALLOWLISTED_HEADERS
        }
        text_excerpt = None
        json_payload: JsonValue | None = None
        if response.content:
            text_excerpt = response.text[:240]
            content_type = cast("str", response.headers.get("content-type", ""))
            if "json" in content_type.lower():
                try:
                    json_payload = cast("JsonValue", response.json())
                except json.JSONDecodeError:
                    json_payload = None
        return OracleResponse(
            status_code=response.status_code,
            headers=allowlisted,
            json_body=json_payload,
            text_excerpt=text_excerpt,
        )

    def get(self, path: str) -> JsonObject:
        return _require_dict(self.request("GET", path), operation=f"GET {path}")

    def delete(self, path: str) -> OracleResponse:
        return self.request("DELETE", path)

    def assert_absent(self, path: str, resource: str) -> None:
        _assert_absent(self.request("GET", path), resource)

    def delete_callback(self, path: str, resource: str) -> Callable[[], None]:
        return _delete_callback(lambda: self.delete(path), resource)

    def create_label(self, name: str, *, color: str | None = None) -> JsonObject:
        body: JsonObject = {"name": name}
        if color is not None:
            body["color"] = color
        response = self.request("POST", "/api/labels", json_body=body)
        return _require_dict(response, operation="create label")

    def get_label(self, label_id: str) -> JsonObject:
        return self.get(f"/api/labels/{label_id}")

    def create_project(
        self,
        title: str,
        *,
        description: str | None = None,
    ) -> JsonObject:
        body: JsonObject = {"title": title}
        if description is not None:
            body["description"] = description
        response = self.request("POST", "/api/projects", json_body=body)
        created = _require_dict(response, operation="create project")
        if "title" not in created and "name" in created:
            created = {**created, "title": created["name"]}
        return created

    def get_project(self, project_id: str) -> JsonObject:
        return self.get(f"/api/projects/{project_id}")

    def update_project(self, project_id: str, body: JsonObject) -> JsonObject:
        response = self.request("PUT", f"/api/projects/{project_id}", json_body=body)
        return _require_dict(response, operation="update project")

    def project_title(self, body: JsonObject) -> str:
        for key in ("title", "name"):
            value = body.get(key)
            if isinstance(value, str):
                return value
        msg = "project response missing title/name"
        raise KeyError(msg)

    def project_description(self, body: JsonObject) -> object:
        if "description" not in body:
            msg = "project response missing description"
            raise KeyError(msg)
        return body["description"]

    def issue_project_id(self, body: JsonObject) -> str | None:
        project_id = body.get("project_id")
        if isinstance(project_id, str):
            return project_id
        project = body.get("project")
        if isinstance(project, dict):
            value = project.get("id")
            if isinstance(value, str):
                return value
        return None

    def create_issue(
        self,
        title: str,
        *,
        description: str | None = None,
        project_id: str | None = None,
    ) -> JsonObject:
        body: JsonObject = {"title": title}
        if description is not None:
            body["description"] = description
        if project_id is not None:
            body["project_id"] = project_id
        response = self.request("POST", "/api/issues", json_body=body)
        return _require_dict(response, operation="create issue")

    def get_issue(self, issue_id: str) -> JsonObject:
        return self.get(f"/api/issues/{issue_id}")

    def list_issues_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        status: str | None = None,
        label_id: str | None = None,
    ) -> tuple[list[JsonObject], str | None]:
        offset = int(cursor) if cursor is not None and cursor.isdigit() else 0
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset:
            query["offset"] = str(offset)
        if status is not None:
            query["status"] = status
        if label_id is not None:
            query["label"] = label_id
        path = "/api/issues/"
        if query:
            path = f"{path}?{urlencode(query)}"
        return _parse_issue_list_page(self.request("GET", path), limit=limit, offset=offset)

    def list_issue_labels(self, issue_id: str) -> list[JsonObject]:
        response = self.request("GET", f"/api/issues/{issue_id}/labels")
        return _require_object_list(response, key="labels", operation="list issue labels")

    def list_comments(self, issue_id: str) -> list[JsonObject]:
        response = self.request("GET", f"/api/issues/{issue_id}/comments")
        return _require_object_list(response, key="comments", operation="list comments")

    def assert_comment_removed_from_issue(self, issue_id: str, comment_id: str) -> None:
        for entry in self.list_comments(issue_id):
            if entry.get("id") == comment_id:
                msg = f"expected comment {comment_id} to be absent from issue {issue_id}"
                raise AssertionError(msg)

    def upload_attachment(
        self,
        issue_id: str,
        *,
        filename: str,
        content: bytes,
    ) -> JsonObject:
        response = self._client.post(
            "/api/upload-file",
            headers=self._auth_headers(),
            files={"file": (filename, content, "application/octet-stream")},
            data=cast("dict[str, str]", {"issue_id": issue_id}),
        )
        return _require_dict(
            OracleResponse(
                status_code=response.status_code,
                headers={},
                json_body=cast("JsonValue", response.json()) if response.content else None,
                text_excerpt=response.text[:240] if response.content else None,
            ),
            operation="upload attachment",
        )

    def get_attachment(self, attachment_id: str) -> JsonObject:
        return self.get(f"/api/attachments/{attachment_id}")

    def download_attachment_content(self, attachment_id: str) -> bytes:
        response = self._client.get(
            f"/api/attachments/{attachment_id}/download",
            headers=self._auth_headers(),
        )
        if response.status_code != 200:
            msg = (
                "download attachment content failed: "
                f"status={response.status_code} body={response.text[:240]}"
            )
            raise AssertionError(msg)
        return response.content

    def list_runtimes_raw(self) -> list[JsonObject]:
        response = self.request("GET", "/api/runtimes")
        if response.status_code != 200:
            return []
        body = response.json_body
        if isinstance(body, list):
            return [entry for entry in body if isinstance(entry, dict)]
        if isinstance(body, dict):
            nested = body.get("runtimes")
            if isinstance(nested, list):
                return [entry for entry in nested if isinstance(entry, dict)]
        return []

    def find_online_opencode_runtime(self, daemon_id: str) -> str | None:
        matches = [
            entry
            for entry in self.list_runtimes_raw()
            if str(entry.get("provider")) == "opencode"
            and str(entry.get("daemon_id")) == daemon_id
            and str(entry.get("status", "")).lower() in {"online", "ready", "active"}
        ]
        if len(matches) != 1:
            return None
        runtime_id = matches[0].get("id")
        return None if runtime_id is None else str(runtime_id)

    def runtime_absent_or_non_routable(
        self,
        daemon_id: str,
        runtime_id: str | None,
    ) -> bool:
        runtimes = self.list_runtimes_raw()
        for entry in runtimes:
            entry_id = str(entry.get("id", ""))
            entry_daemon = str(entry.get("daemon_id", ""))
            if runtime_id is not None and entry_id == runtime_id:
                status = str(entry.get("status", "")).lower()
                routable = entry.get("routable")
                return routable is False or status in {"offline", "stopped", "inactive"}
            if entry_daemon == daemon_id:
                status = str(entry.get("status", "")).lower()
                routable = entry.get("routable")
                if routable is False or status in {"offline", "stopped", "inactive"}:
                    continue
                return False
        return True

    def get_runtime_raw(self, runtime_id: str) -> JsonObject | None:
        response = self.request("GET", f"/api/runtimes/{runtime_id}")
        if response.status_code == 404:
            return None
        if response.status_code != 200 or not isinstance(response.json_body, dict):
            return None
        return response.json_body

    def get_agent_raw(self, agent_id: str) -> JsonObject | None:
        response = self.request("GET", f"/api/agents/{agent_id}")
        if response.status_code == 404:
            return None
        if response.status_code != 200 or not isinstance(response.json_body, dict):
            return None
        return response.json_body

    def assert_agent_non_routable(self, agent_id: str) -> None:
        payload = self.get_agent_raw(agent_id)
        if payload is None:
            return
        routable = payload.get("routable")
        if routable is False:
            return
        status = str(payload.get("status", "")).lower()
        if status in {"archived", "inactive"}:
            return
        msg = f"expected agent {agent_id} to be non-routable, got {payload!r}"
        raise AssertionError(msg)

    def assert_workspace_absent(self, workspace_id: str, pat: str) -> None:
        response = self._client.get(
            f"/api/workspaces/{workspace_id}",
            headers={
                "Authorization": f"Bearer {pat}",
            },
        )
        if response.status_code == 404:
            return
        msg = f"expected workspace {workspace_id} to be absent, got {response.status_code}"
        raise AssertionError(msg)

    def list_project_resources_raw(self, project_id: str) -> list[JsonObject]:
        response = self.request("GET", f"/api/projects/{project_id}/resources")
        if response.status_code != 200:
            return []
        body = response.json_body
        if isinstance(body, list):
            return [entry for entry in body if isinstance(entry, dict)]
        if isinstance(body, dict):
            nested = body.get("resources")
            if isinstance(nested, list):
                return [entry for entry in nested if isinstance(entry, dict)]
        return []

    def assert_project_resource_absent(self, project_id: str, resource_id: str) -> None:
        for entry in self.list_project_resources_raw(project_id):
            if str(entry.get("id")) == resource_id:
                msg = f"expected project resource {resource_id} to be absent"
                raise AssertionError(msg)

    def issue_assignee_id(self, body: JsonObject) -> str | None:
        assignee = body.get("assignee")
        if isinstance(assignee, dict):
            value = assignee.get("id")
            if isinstance(value, str):
                return value
        assignee_id = body.get("assignee_id")
        return None if assignee_id is None else str(assignee_id)

    def list_issue_attachments(self, issue_id: str) -> list[JsonObject]:
        response = self.request("GET", f"/api/issues/{issue_id}/attachments")
        return _require_object_list(response, key="attachments", operation="list issue attachments")

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._pat.reveal()}",
            "X-Workspace-ID": self._workspace_id,
        }

    def _json_headers(self) -> dict[str, str]:
        return {**self._auth_headers(), "Content-Type": "application/json"}


def _require_dict(response: OracleResponse, *, operation: str) -> JsonObject:
    if response.status_code not in (200, 201) or not isinstance(response.json_body, dict):
        msg = f"{operation} failed: status={response.status_code} body={response.text_excerpt}"
        raise AssertionError(msg)
    return response.json_body


def _require_object_list(
    response: OracleResponse,
    *,
    key: str,
    operation: str,
) -> list[JsonObject]:
    if response.status_code != 200:
        msg = f"{operation} failed: status={response.status_code} body={response.text_excerpt}"
        raise AssertionError(msg)
    body = response.json_body
    nested: object
    if isinstance(body, list):
        nested = body
    elif isinstance(body, dict):
        nested = body.get(key)
    else:
        nested = None
    if not isinstance(nested, list):
        msg = (
            f"{operation} failed: expected a list or object with {key!r} list: "
            f"{response.text_excerpt}"
        )
        raise AssertionError(msg)
    return [entry for entry in nested if isinstance(entry, dict)]


def _parse_issue_list_page(
    response: OracleResponse,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[JsonObject], str | None]:
    if response.status_code != 200:
        msg = f"list issues failed: status={response.status_code} body={response.text_excerpt}"
        raise AssertionError(msg)
    body = response.json_body
    if not isinstance(body, dict):
        msg = f"list issues returned unexpected body: {response.text_excerpt}"
        raise AssertionError(msg)
    items_value = body.get("issues")
    if not isinstance(items_value, list):
        items_value = body.get("items")
    if not isinstance(items_value, list):
        msg = f"list issues returned unexpected body: {response.text_excerpt}"
        raise AssertionError(msg)
    items = [entry for entry in items_value if isinstance(entry, dict)]
    next_cursor = body.get("next_cursor")
    if next_cursor is not None and not isinstance(next_cursor, str):
        msg = f"list issues returned unexpected next_cursor: {response.text_excerpt}"
        raise AssertionError(msg)
    if next_cursor is None:
        total = body.get("total")
        if isinstance(total, int) and limit is not None and items:
            next_offset = offset + len(items)
            if next_offset < total:
                next_cursor = str(next_offset)
    return items, next_cursor or None


def _assert_absent(response: OracleResponse, resource: str) -> None:
    if response.status_code == 404:
        return
    msg = f"expected absent {resource}, got status={response.status_code} body={response.text_excerpt}"
    raise AssertionError(msg)


def _delete_callback(
    delete_fn: Callable[[], OracleResponse],
    resource: str,
) -> Callable[[], None]:
    def _cleanup() -> None:
        response = delete_fn()
        if response.status_code == 404:
            raise ResourceAbsentError()
        if response.status_code not in (200, 204):
            msg = f"delete {resource} failed: status={response.status_code} body={response.text_excerpt}"
            raise RuntimeError(msg)

    return _cleanup

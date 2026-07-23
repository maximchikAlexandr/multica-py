"""Single HTTP client for live tests.

Exports:
  - LiveApiClient: typed wrapper over httpx.Client with auth, redaction,
    and idempotent delete.
  - bootstrap_api_client(env) -> LiveApiClient: factory from Environment.
  - request_json(client, method, path, **kwargs) -> dict: typed request helper.
"""

from __future__ import annotations

import contextlib
import json
from typing import Any

import httpx

from tools.live_support.diagnostics import scan_for_secrets
from tools.live_support.environment import Environment


class LiveApiClient:
    """One HTTP client shared across all live tests in a session.

    Replaces ad-hoc httpx.Client usage. Idempotent delete prevents double-cleanup
    when a test re-runs after a partial teardown.
    """

    def __init__(
        self,
        base_url: str,
        env: Environment,
        *,
        timeout: float = 30.0,
    ) -> None:
        headers: dict[str, str] = {}
        if env.api_key:
            headers["Authorization"] = f"Bearer {env.api_key}"
        self._client = httpx.Client(base_url=base_url, headers=headers, timeout=timeout)
        self._base_url = base_url
        self._env = env
        self._deleted_ids: set[str] = set()

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Issue a request, returning the raw httpx.Response."""
        return self._client.request(method, path, **kwargs)

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Idempotent delete: returns 204 if path was already deleted."""
        path_id = path.rstrip("/").split("/")[-1]
        if path_id in self._deleted_ids:
            return httpx.Response(204, content=b"")
        response = self.request("DELETE", path, **kwargs)
        if response.status_code in (200, 204):
            self._deleted_ids.add(path_id)
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LiveApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def env(self) -> Environment:
        return self._env


def bootstrap_api_client(env: Environment) -> LiveApiClient:
    """Build a LiveApiClient from a parsed Environment."""
    base_url = env.extra.get("MULTICA_BASE_URL", "https://api.multica.ai")
    # ponytail: URL is a trust decision; warn if non-default + API key set
    if base_url != "https://api.multica.ai" and "MULTICA_API_KEY" in env.extra:
        import warnings

        warnings.warn(
            f"MULTICA_BASE_URL={base_url!r} differs from default "
            f"but MULTICA_API_KEY is set — key will be sent to {base_url}"
        )
    return LiveApiClient(base_url=base_url, env=env)


def request_json(client: LiveApiClient, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    """Issue a request and parse the JSON body, asserting no secrets leak."""
    response = client.request(method, path, **kwargs)
    assert response.status_code == 200, (
        f"{method} {path} -> {response.status_code}: {response.text[:200]}"
    )
    assert scan_for_secrets(response.text) == [], (
        f"response contains secrets: {scan_for_secrets(response.text)}"
    )
    body = response.json()
    assert isinstance(body, dict), f"expected dict body, got {type(body).__name__}"
    return body

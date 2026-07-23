from __future__ import annotations

import json
import os
import pathlib
import random
import time
from dataclasses import dataclass
from typing import ClassVar

import httpx

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from tests.live._live_helpers import (
    TestIdentity,
    WorkspaceContext,
    bootstrap_email,
    profile_name_for_run,
    workspace_slug,
    write_cli_profile,
)
from tests.live.diagnostics import VERIFICATION_CODE
from tools.live_support.environment import LiveSetupError, SecretString
from tools.live_support.oracle import DirectApiOracle


class BootstrapApiClient:
    """HTTP bootstrap client for development-mode Multica backends.

    A process-level ``_IDENTITY_BY_RUN_ID`` cache lets repeated calls for
    the same ``run_id`` (CI smoke + agent-sandbox within one run) reuse
    the JWT/identity from the first bootstrap. The dev backend
    rate-limits ``/auth/send-code`` on the CI runner IP, so the second
    call would otherwise hit 429 within seconds of the first.
    """

    # Class-level cache, keyed by run_id. One CI run = one run_id = one identity.
    _IDENTITY_BY_RUN_ID: ClassVar[dict[str, tuple[SecretString, SecretString, str]]] = {}

    def __init__(
        self,
        server_url: str,
        run_id: str,
        diagnostics_secrets: list[str],
        *,
        profile_name: str | None = None,
    ) -> None:
        self._server_url = server_url.rstrip("/")
        self._run_id = run_id
        self._email = bootstrap_email(run_id)
        self._profile_name = profile_name or profile_name_for_run(run_id)
        self._secrets = diagnostics_secrets

    @property
    def email(self) -> str:
        return self._email

    def bootstrap(
        self, *, secondary: bool = True
    ) -> tuple[TestIdentity, WorkspaceContext, WorkspaceContext | None]:
        with httpx.Client(base_url=self._server_url, timeout=30.0) as client:
            cached = self._IDENTITY_BY_RUN_ID.get(self._run_id)
            if cached is not None:
                jwt, pat, user_id = cached
            else:
                jwt, pat, user_id = self._authenticate(client)
                self._IDENTITY_BY_RUN_ID[self._run_id] = (jwt, pat, user_id)
            jwt_value = jwt.reveal()
            if secondary:
                primary = self._create_workspace(client, jwt_value, suffix="a", label="Primary")
                secondary_workspace = self._create_workspace(
                    client, jwt_value, suffix="b", label="Secondary"
                )
            else:
                primary = self._create_workspace(client, jwt_value, suffix="sb", label="Sandbox")
                secondary_workspace = None
        identity = TestIdentity(email=self._email, user_id=user_id, pat=pat)
        return identity, primary, secondary_workspace

    def _authenticate(self, client: httpx.Client) -> tuple[SecretString, SecretString, str]:
        verify_payload = self._try_verify_code(client)
        if verify_payload is None:
            self._send_code_with_retry(client)
            verify_payload = self._post_json(
                client,
                "/auth/verify-code",
                {"email": self._email, "code": VERIFICATION_CODE},
                auth=None,
                expected_statuses={200, 201},
                stage="bootstrap",
            )
        jwt_value = str(verify_payload["token"])
        self._secrets.append(jwt_value)
        token_payload = self._post_json(
            client,
            "/api/tokens",
            {"name": f"multica-py-live-{self._run_id}", "expires_in_days": 1},
            auth=f"Bearer {jwt_value}",
            expected_statuses={201},
            stage="bootstrap",
        )
        pat_value = str(token_payload["token"])
        pat = SecretString(pat_value)
        self._secrets.append(pat_value)
        user_id = _user_id_from_payloads(token_payload, verify_payload)
        if not user_id:
            me_payload = self._get_json(
                client,
                "/api/me",
                auth=f"Bearer {jwt_value}",
                expected_statuses={200},
                stage="bootstrap",
            )
            user_id = _user_id_from_payloads(me_payload, allow_id=True)
        if not user_id:
            raise LiveSetupError(
                "bootstrap",
                "could not resolve user id from verify-code, token response, or /api/me",
            )
        return SecretString(jwt_value), pat, user_id

    def delete_workspace(self, workspace_id: str, pat: str) -> None:
        with httpx.Client(base_url=self._server_url, timeout=30.0) as client:
            response = client.delete(
                f"/api/workspaces/{workspace_id}",
                headers={"Authorization": f"Bearer {pat}"},
            )
        if response.status_code in {200, 204, 404}:
            return
        excerpt = _redacted_excerpt(response.text, self._secrets)
        raise LiveSetupError(
            "bootstrap",
            f"delete workspace returned {response.status_code}: {excerpt}",
        )

    def _create_workspace(
        self,
        client: httpx.Client,
        jwt_value: str,
        *,
        suffix: str,
        label: str,
    ) -> WorkspaceContext:
        slug = workspace_slug(self._run_id, suffix)
        payload = self._post_json(
            client,
            "/api/workspaces",
            {"name": f"{label} {self._run_id}", "slug": slug},
            auth=f"Bearer {jwt_value}",
            expected_statuses={200, 201},
            stage="bootstrap",
        )
        workspace_id = str(payload["id"])
        return WorkspaceContext(
            id=workspace_id,
            name=str(payload.get("name") or label),
            slug=slug,
            profile_name=self._profile_name,
        )

    def _try_verify_code(self, client: httpx.Client) -> dict[str, object] | None:
        response = client.post(
            "/auth/verify-code",
            json={"email": self._email, "code": VERIFICATION_CODE},
        )
        if response.status_code not in {200, 201}:
            return None
        if not response.content:
            return None
        payload = response.json()
        if not isinstance(payload, dict):
            raise LiveSetupError("bootstrap", "/auth/verify-code returned non-object JSON")
        if payload.get("token") in {None, ""}:
            return None
        return payload

    def _send_code_with_retry(self, client: httpx.Client) -> None:
        max_attempts = _send_code_max_attempts()
        for attempt in range(max_attempts):
            response = client.post("/auth/send-code", json={"email": self._email})
            if response.status_code in {200, 201, 202, 204}:
                return
            if response.status_code == 429 and attempt + 1 < max_attempts:
                detail = _http_response_excerpt(response, self._secrets)
                import sys

                sys.stderr.write(
                    f"bootstrap: /auth/send-code rate limited (attempt {attempt + 1}/"
                    f"{max_attempts}): {detail}\n"
                )
                time.sleep(_send_code_retry_delay(attempt, response))
                continue
            detail = _http_response_excerpt(response, self._secrets)
            raise LiveSetupError(
                "bootstrap",
                f"/auth/send-code returned {response.status_code}: {detail}",
            )

    def _request_json(
        self,
        client: httpx.Client,
        method: str,
        path: str,
        *,
        body: dict[str, object] | None = None,
        auth: str | None,
        expected_statuses: set[int],
        stage: str,
    ) -> dict[str, object]:
        headers: dict[str, str] = {}
        content: str | None = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            content = json.dumps(body)
        if auth is not None:
            headers["Authorization"] = auth
        response = client.request(method, path, headers=headers, content=content)
        if response.status_code not in expected_statuses:
            excerpt = _redacted_excerpt(response.text, self._secrets)
            raise LiveSetupError(
                stage,
                f"{path} returned {response.status_code}: {excerpt}",
            )
        if not response.content:
            return {}
        payload = response.json()
        if not isinstance(payload, dict):
            raise LiveSetupError(stage, f"{path} returned non-object JSON")
        return payload

    def _get_json(
        self,
        client: httpx.Client,
        path: str,
        *,
        auth: str,
        expected_statuses: set[int],
        stage: str,
    ) -> dict[str, object]:
        return self._request_json(
            client,
            "GET",
            path,
            auth=auth,
            expected_statuses=expected_statuses,
            stage=stage,
        )

    def _post_json(
        self,
        client: httpx.Client,
        path: str,
        body: dict[str, object],
        *,
        auth: str | None,
        expected_statuses: set[int],
        stage: str,
    ) -> dict[str, object]:
        return self._request_json(
            client,
            "POST",
            path,
            body=body,
            auth=auth,
            expected_statuses=expected_statuses,
            stage=stage,
        )


@dataclass(frozen=True, slots=True)
class SandboxSession:
    """Authenticated live session with SDK client and HTTP oracle."""

    identity: TestIdentity
    workspace: WorkspaceContext
    client: MulticaClient
    oracle: DirectApiOracle
    bootstrap_client: BootstrapApiClient
    secondary_workspace: WorkspaceContext | None = None


def setup_sandbox_session(
    *,
    server_url: str,
    run_id: str,
    cli_executable: pathlib.Path,
    home_dir: pathlib.Path,
    profile_name: str,
    secret_values: list[str] | None = None,
    sandbox_bootstrap: bool = False,
) -> SandboxSession:
    secrets = secret_values if secret_values is not None else []
    bootstrap_client = BootstrapApiClient(
        server_url,
        run_id,
        secrets,
        profile_name=profile_name,
    )
    identity, workspace, secondary = bootstrap_client.bootstrap(secondary=not sandbox_bootstrap)
    write_cli_profile(
        home_dir,
        profile_name,
        server_url=server_url,
        app_url=server_url,
        workspace_id=workspace.id,
        token=identity.pat.reveal(),
    )
    client = MulticaClient(
        ClientConfig(
            executable=str(cli_executable),
            server_url=server_url,
            workspace_id=workspace.id,
            profile=profile_name,
            environment=(("HOME", str(home_dir)),),
        )
    )
    oracle = DirectApiOracle(
        server_url,
        workspace_id=workspace.id,
        pat=identity.pat,
    )
    return SandboxSession(
        identity=identity,
        workspace=workspace,
        client=client,
        oracle=oracle,
        bootstrap_client=bootstrap_client,
        secondary_workspace=secondary,
    )


def _user_id_from_payloads(*payloads: dict[str, object], allow_id: bool = False) -> str:
    for payload in payloads:
        direct = payload.get("user_id")
        if direct:
            return str(direct)
        if allow_id:
            top_level_id = payload.get("id")
            if top_level_id:
                return str(top_level_id)
        user = payload.get("user")
        if isinstance(user, dict):
            nested_id = user.get("id")
            if nested_id:
                return str(nested_id)
    return ""


def _redacted_excerpt(text: str, secrets: list[str]) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "***")
    if len(redacted) > 240:
        return redacted[:240] + "..."
    return redacted


def _parse_retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    value = raw.strip()
    if value.isdigit():
        return float(value)
    return None


def _http_response_excerpt(response: httpx.Response, secrets: list[str]) -> str:
    header_parts = [f"{name}={value}" for name, value in response.headers.items()]
    headers = _redacted_excerpt("; ".join(header_parts), secrets)
    body = _redacted_excerpt(response.text, secrets)
    return f"headers=[{headers}] body={body}"


def _send_code_retry_delay(attempt: int, response: httpx.Response) -> float:
    retry_after = _parse_retry_after(response)
    if retry_after is not None:
        return retry_after + random.uniform(0.0, 0.5)
    return min(2**attempt, 5.0) + random.uniform(0.0, 1.0)


def _send_code_max_attempts() -> int:
    raw = os.environ.get("MULTICA_LIVE_SEND_CODE_MAX_ATTEMPTS", "3")
    try:
        attempts = int(raw)
    except ValueError:
        return 3
    return max(1, attempts)

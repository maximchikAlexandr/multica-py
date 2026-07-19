from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from tests.live.exceptions import LiveSetupError
from tests.live.settings import bootstrap_email, profile_name_for_run, workspace_slug


class SecretString:
    """Wrapper that redacts secret values from repr and str."""

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        """Return the underlying secret value."""
        return self._value

    def __repr__(self) -> str:
        return "SecretString(***)"

    def __str__(self) -> str:
        return "***"


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    """Workspace created during bootstrap."""

    id: str
    name: str
    slug: str
    profile_name: str


@dataclass(slots=True)
class TestIdentity:
    """Authenticated test identity with redacted secrets."""

    __test__ = False

    email: str
    user_id: str
    pat: SecretString

    def __repr__(self) -> str:
        return (
            f"TestIdentity(email={self.email!r}, user_id={self.user_id!r}, pat=SecretString(***))"
        )


class BootstrapApiClient:
    """HTTP bootstrap client for development-mode Multica backends."""

    def __init__(self, server_url: str, run_id: str, diagnostics_secrets: list[str]) -> None:
        self._server_url = server_url.rstrip("/")
        self._run_id = run_id
        self._email = bootstrap_email(run_id)
        self._profile_name = profile_name_for_run(run_id)
        self._secrets = diagnostics_secrets

    @property
    def email(self) -> str:
        """Return the bootstrap email address."""
        return self._email

    def bootstrap(self) -> tuple[TestIdentity, WorkspaceContext, WorkspaceContext]:
        """Run the canonical bootstrap HTTP sequence.

        Returns:
            Test identity and primary/secondary workspace contexts.

        Raises:
            LiveSetupError: If any bootstrap step fails.
        """
        with httpx.Client(base_url=self._server_url, timeout=30.0) as client:
            self._post_json(
                client,
                "/auth/send-code",
                {"email": self._email},
                auth=None,
                expected_statuses={200, 201, 202, 204},
                stage="bootstrap",
            )
            verify_payload = self._post_json(
                client,
                "/auth/verify-code",
                {"email": self._email, "code": "888888"},
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
            primary = self._create_workspace(client, jwt_value, suffix="a", label="Primary")
            secondary = self._create_workspace(client, jwt_value, suffix="b", label="Secondary")
        identity = TestIdentity(
            email=self._email,
            user_id=user_id,
            pat=pat,
        )
        return identity, primary, secondary

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

    def _get_json(
        self,
        client: httpx.Client,
        path: str,
        *,
        auth: str,
        expected_statuses: set[int],
        stage: str,
    ) -> dict[str, object]:
        response = client.get(path, headers={"Authorization": auth})
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
        headers = {"Content-Type": "application/json"}
        if auth is not None:
            headers["Authorization"] = auth
        response = client.post(path, headers=headers, content=json.dumps(body))
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

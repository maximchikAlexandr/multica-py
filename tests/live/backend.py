from __future__ import annotations

import json
import os
import pathlib
import platform
import secrets as secrets_module
import shutil
import socket
import subprocess
import textwrap
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from tests.live.diagnostics import DiagnosticCollector
from tests.live.environment import (
    CompatibilityTarget,
    LiveSettings,
    LiveSetupError,
    LiveTestEnvironment,
    LiveTestRun,
    SecretString,
    TestIdentity,
    WorkspaceContext,
    bootstrap_email,
    profile_name_for_run,
    workspace_slug,
    write_cli_profile,
)
from tests.live.oracle import DirectApiOracle


class BootstrapApiClient:
    """HTTP bootstrap client for development-mode Multica backends."""

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
            jwt_value, pat, user_id = self._authenticate(client)
            primary = self._create_workspace(client, jwt_value, suffix="a", label="Primary")
            secondary = self._create_workspace(client, jwt_value, suffix="b", label="Secondary")
        identity = TestIdentity(
            email=self._email,
            user_id=user_id,
            pat=pat,
        )
        return identity, primary, secondary

    def bootstrap_sandbox(self) -> tuple[TestIdentity, WorkspaceContext]:
        """Run bootstrap for one isolated sandbox workspace.

        Returns:
            Test identity and sandbox workspace context.

        Raises:
            LiveSetupError: If any bootstrap step fails.
        """
        with httpx.Client(base_url=self._server_url, timeout=30.0) as client:
            jwt_value, pat, user_id = self._authenticate(client)
            workspace = self._create_workspace(client, jwt_value, suffix="sb", label="Sandbox")
        identity = TestIdentity(email=self._email, user_id=user_id, pat=pat)
        return identity, workspace

    def _authenticate(self, client: httpx.Client) -> tuple[str, SecretString, str]:
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
        return jwt_value, pat, user_id

    def delete_workspace(self, workspace_id: str, pat: str) -> None:
        """Delete one workspace through the bootstrap HTTP API.

        Args:
            workspace_id: Workspace identifier to delete.
            pat: Personal access token for authorization.

        Raises:
            LiveSetupError: If workspace deletion fails unexpectedly.
        """
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
    """Bootstrap identity, write CLI profile, and build SDK client plus oracle.

    Args:
        server_url: Backend server URL.
        run_id: Unique 32-character lowercase hex run identifier.
        cli_executable: Resolved Multica CLI executable path.
        home_dir: Temporary HOME directory for the session.
        profile_name: CLI profile directory name.
        secret_values: Optional list mutated with bootstrap secrets for diagnostics.
        sandbox_bootstrap: When true, create a single sandbox workspace only.

    Returns:
        Initialized sandbox session with client and oracle.
    """
    secrets = secret_values if secret_values is not None else []
    bootstrap_client = BootstrapApiClient(
        server_url,
        run_id,
        secrets,
        profile_name=profile_name,
    )
    secondary: WorkspaceContext | None = None
    if sandbox_bootstrap:
        identity, workspace = bootstrap_client.bootstrap_sandbox()
    else:
        identity, workspace, secondary = bootstrap_client.bootstrap()
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
        pat=identity.pat.reveal(),
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


READINESS_INTERVALS = (0.5, 1.0, 2.0)
COMPOSE_ENV_KEYS = (
    "APP_ENV",
    "MULTICA_DEV_VERIFICATION_CODE",
    "JWT_SECRET",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "MULTICA_BACKEND_IMAGE",
    "MULTICA_IMAGE_TAG",
    "BACKEND_PORT",
    "APP_URL",
)


@dataclass(frozen=True, slots=True)
class ImagePolicy:
    """Resolved backend image selection policy for compose startup."""

    blocking: bool
    backend_image: str
    backend_tag: str

    @classmethod
    def resolve(cls, settings: LiveSettings, target: CompatibilityTarget) -> ImagePolicy:
        """Build image policy from live settings and compatibility target."""
        if (
            os.environ.get("MULTICA_LIVE_ALLOW_IMAGE_OVERRIDE") == "1"
            or settings.existing_url is not None
        ):
            blocking = False
        elif os.environ.get("CI") or settings.suite_profile == "smoke":
            blocking = True
        else:
            blocking = target.cli_source == "release"
        if blocking:
            return cls(
                blocking=True, backend_image=target.backend_image, backend_tag=target.backend_tag
            )
        return cls(
            blocking=False,
            backend_image=os.environ.get("MULTICA_LIVE_BACKEND_IMAGE", target.backend_image),
            backend_tag=os.environ.get("MULTICA_LIVE_IMAGE_TAG", target.backend_tag),
        )


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    """Last observed readiness probe result."""

    status_code: int | None
    json_body: dict[str, object] | None
    body_excerpt: str


class ComposeLifecycle:
    """Manage Docker Compose lifecycle for live tests."""

    def __init__(
        self,
        settings: LiveSettings,
        target: CompatibilityTarget,
        run: LiveTestRun,
        diagnostics: DiagnosticCollector,
    ) -> None:
        self._settings = settings
        self._target = target
        self._run = run
        self._diagnostics = diagnostics
        self._backend_port = allocate_loopback_port()
        self._server_url = f"http://127.0.0.1:{self._backend_port}"
        self._image_policy = ImagePolicy.resolve(settings, target)
        self._compose_file: pathlib.Path | None = None
        self._compose_override: pathlib.Path | None = None
        self._env_file: pathlib.Path | None = None
        self._started = False

    @property
    def server_url(self) -> str:
        """Return the backend server URL for this lifecycle."""
        return self._server_url

    @property
    def compose_file(self) -> pathlib.Path:
        """Return the resolved compose file path."""
        return self._require_compose_file()

    @property
    def env_file(self) -> pathlib.Path:
        """Return the generated compose env file path."""
        return self._require_env_file()

    def write_env_file(self, secrets: dict[str, str]) -> pathlib.Path:
        """Write the allowlisted Compose env file outside artifact uploads.

        Args:
            secrets: Generated secret values keyed by env var name.

        Returns:
            Path to the written env file.
        """
        lines = [f"{key}={secrets[key]}" for key in COMPOSE_ENV_KEYS]
        secrets_dir = self._ensure_secrets_dir()
        env_path = secrets_dir / "compose.env"
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        env_path.chmod(0o600)
        self._env_file = env_path
        return env_path

    def write_compose_override(self, digest: str) -> pathlib.Path:
        """Write a digest-pinned compose override for the backend service.

        Args:
            digest: Expected backend image digest such as ``sha256:abc...``.

        Returns:
            Path to the generated override file.
        """
        override_path = self._ensure_secrets_dir() / "compose.override.yml"
        image_ref = f"{self._target.backend_image}@{digest}"
        override_path.write_text(
            f"services:\n  backend:\n    image: {image_ref}\n",
            encoding="utf-8",
        )
        override_path.chmod(0o600)
        self._compose_override = override_path
        return override_path

    def generate_compose_secrets(self) -> dict[str, str]:
        """Generate allowlisted Compose environment values.

        Returns:
            Mapping of env var names to generated values.
        """
        return {
            "APP_ENV": "development",
            "MULTICA_DEV_VERIFICATION_CODE": "888888",
            "JWT_SECRET": secrets_module.token_urlsafe(32),
            "POSTGRES_DB": "multica",
            "POSTGRES_USER": "multica",
            "POSTGRES_PASSWORD": secrets_module.token_urlsafe(24),
            "MULTICA_BACKEND_IMAGE": self._image_policy.backend_image,
            "MULTICA_IMAGE_TAG": self._image_policy.backend_tag,
            "BACKEND_PORT": str(self._backend_port),
            "APP_URL": self._server_url,
        }

    def start(self) -> None:
        """Start postgres and backend services via Docker Compose."""
        if self._settings.existing_url is not None:
            return
        upstream = self._settings.upstream_dir
        if upstream is None:
            raise LiveSetupError("compose", "MULTICA_LIVE_UPSTREAM_DIR is required")
        compose_file = _resolve_compose_file(upstream, self._target.compose_file)
        self._compose_file = compose_file
        digest = self._platform_digest()
        self.write_compose_override(digest)
        self._pull_backend_image(digest)
        secrets = self.generate_compose_secrets()
        self._diagnostics.register_secret(secrets["JWT_SECRET"])
        self._diagnostics.register_secret(secrets["POSTGRES_PASSWORD"])
        self.write_env_file(secrets)
        argv = compose_up_argv(
            self._compose_files(),
            self._run.compose_project,
            self._require_env_file(),
        )
        self._run_command(argv, stage="compose")
        self._verify_running_backend_digest(digest)
        self._started = True

    def wait_ready(self) -> ReadinessResult:
        """Poll ``/readyz`` until success or timeout.

        Returns:
            Last readiness probe result.

        Raises:
            LiveSetupError: If readiness is not reached before timeout.
        """
        endpoint = f"{self.server_url}/readyz"
        timeout = self._settings.ready_timeout_seconds
        deadline = time.monotonic() + timeout
        last = ReadinessResult(status_code=None, json_body=None, body_excerpt="")
        interval_index = 0
        while time.monotonic() < deadline:
            last = probe_readiness(endpoint)
            if is_ready(last):
                return last
            sleep_seconds = READINESS_INTERVALS[min(interval_index, len(READINESS_INTERVALS) - 1)]
            interval_index += 1
            time.sleep(sleep_seconds)
        self.capture_diagnostics()
        raise LiveSetupError(
            "readyz",
            f"backend not ready within {timeout}s; last status={last.status_code}",
        )

    def capture_diagnostics(self) -> None:
        """Capture compose status and service logs into diagnostics."""
        if self._compose_file is None:
            return
        compose_files: tuple[pathlib.Path, ...] = (self._compose_file,)
        if self._compose_override is not None:
            compose_files = (*compose_files, self._compose_override)
        capture_compose_diagnostics(
            compose_files=compose_files,
            compose_project=self._run.compose_project,
            diagnostics=self._diagnostics,
        )

    def teardown(self) -> list[dict[str, str]]:
        """Destroy compose resources unless keep-env mode is enabled.

        Returns:
            Cleanup failure records for compose teardown or secrets removal.
        """
        failures: list[dict[str, str]] = []
        if self._settings.existing_url is not None or not self._started:
            return failures
        if self._settings.keep_env:
            return failures
        completed = self._run_command(
            compose_down_argv(self._compose_files(), self._run.compose_project),
            stage="compose",
            check=False,
        )
        if completed.returncode != 0:
            detail = textwrap.shorten(
                (completed.stderr or completed.stdout or "").strip(),
                width=240,
                placeholder="...",
            )
            failures.append(
                {
                    "key": "compose-down",
                    "message": f"docker compose down exited {completed.returncode}: {detail}",
                }
            )
        try:
            self._remove_secrets_dir()
        except OSError as exc:
            failures.append({"key": "compose-secrets", "message": str(exc)})
        return failures

    def _ensure_secrets_dir(self) -> pathlib.Path:
        secrets_dir = self._run.secrets_dir
        secrets_dir.mkdir(parents=True, exist_ok=True)
        secrets_dir.chmod(0o700)
        return secrets_dir

    def _remove_secrets_dir(self) -> None:
        secrets_dir = self._run.secrets_dir
        if secrets_dir.is_dir():
            shutil.rmtree(secrets_dir)

    def _platform_digest(self) -> str:
        system = platform.system().lower()
        machine = platform.machine().lower()
        if system == "linux" and machine in {"x86_64", "amd64"}:
            digest = self._target.backend_digest_linux_amd64
        else:
            digest = self._target.backend_digest
        if digest is None or not digest.startswith("sha256:"):
            raise LiveSetupError(
                "compose", "concrete backend digest is required for compose startup"
            )
        return digest

    def _pull_backend_image(self, digest: str) -> None:
        image_ref = f"{self._target.backend_image}@{digest}"
        self._run_command(["docker", "pull", image_ref], stage="compose")

    def _verify_running_backend_digest(self, digest: str) -> None:
        if not self._image_policy.blocking and os.environ.get("CI") != "true":
            return
        if self._target.cli_source != "release" and not os.environ.get("CI"):
            return
        container_id = self._run_command(
            compose_argv(self._compose_files(), self._run.compose_project, "ps", "-q", "backend"),
            stage="compose",
        ).stdout.strip()
        if not container_id:
            raise LiveSetupError(
                "compose", "backend container id not found for digest verification"
            )
        image_id = self._run_command(
            ["docker", "inspect", "--format", "{{.Image}}", container_id.splitlines()[0]],
            stage="compose",
        ).stdout.strip()
        repo_digests = self._run_command(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                "{{range .RepoDigests}}{{println .}}{{end}}",
                image_id,
            ],
            stage="compose",
        ).stdout
        expected = digest.removeprefix("sha256:")
        if expected not in repo_digests and expected not in image_id:
            raise LiveSetupError(
                "compose",
                "backend image digest mismatch: "
                f"expected {digest}, image={image_id}, repo_digests={repo_digests.strip()!r}",
            )

    def _compose_files(self) -> tuple[pathlib.Path, ...]:
        compose_file = self._require_compose_file()
        if self._compose_override is None:
            return (compose_file,)
        return (compose_file, self._compose_override)

    def _require_compose_file(self) -> pathlib.Path:
        if self._compose_file is None:
            raise LiveSetupError("compose", "compose lifecycle has no compose file")
        return self._compose_file

    def _require_env_file(self) -> pathlib.Path:
        if self._env_file is None:
            raise LiveSetupError("compose", "compose lifecycle has no env file")
        return self._env_file

    def _run_command(
        self,
        argv: list[str],
        *,
        stage: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        try:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except FileNotFoundError as exc:
            raise LiveSetupError(stage, "docker compose is unavailable") from exc
        except subprocess.SubprocessError as exc:
            raise LiveSetupError(stage, f"docker compose command failed: {exc}") from exc
        if check and completed.returncode != 0:
            detail = textwrap.shorten(
                (completed.stderr or completed.stdout or "").strip(),
                width=240,
                placeholder="...",
            )
            raise LiveSetupError(stage, f"docker compose exited {completed.returncode}: {detail}")
        return completed


def capture_compose_diagnostics(
    *,
    compose_files: tuple[pathlib.Path, ...],
    compose_project: str,
    diagnostics: DiagnosticCollector,
) -> None:
    """Capture compose status and service logs into diagnostics.

    Args:
        compose_files: Compose file paths for the live project.
        compose_project: Docker Compose project name.
        diagnostics: Diagnostic collector receiving captured output.
    """
    if not compose_files:
        return
    ps = subprocess.run(
        compose_argv(compose_files, compose_project, "ps", "-a"),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    diagnostics.write_text("compose-ps.txt", ps.stdout)
    for service, filename in (("backend", "backend.log"), ("postgres", "postgres.log")):
        logs = subprocess.run(
            compose_argv(compose_files, compose_project, "logs", "--no-color", service),
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        diagnostics.write_log(filename, logs.stdout)


def capture_compose_diagnostics_from_environment(
    live_environment: LiveTestEnvironment,
    diagnostics: DiagnosticCollector,
) -> None:
    """Capture compose diagnostics for a started live test environment.

    Args:
        live_environment: Started live backend environment metadata.
        diagnostics: Diagnostic collector receiving captured output.
    """
    if not live_environment.managed_compose or not live_environment.compose_files:
        return
    capture_compose_diagnostics(
        compose_files=live_environment.compose_files,
        compose_project=live_environment.compose_project,
        diagnostics=diagnostics,
    )


def _resolve_compose_file(upstream: pathlib.Path, compose_file: str) -> pathlib.Path:
    candidate = (upstream / compose_file).resolve()
    upstream_root = upstream.resolve()
    if not candidate.is_file():
        raise LiveSetupError("compose", f"compose file not found: {candidate}")
    if not candidate.is_relative_to(upstream_root):
        raise LiveSetupError("compose", f"compose file escapes upstream checkout: {candidate}")
    return candidate


def compose_up_argv(
    compose_files: tuple[pathlib.Path, ...],
    compose_project: str,
    env_file: pathlib.Path,
) -> list[str]:
    """Build argv for ``docker compose up`` without invoking a shell."""
    argv = compose_argv(compose_files, compose_project, "up", "-d", "postgres", "backend")
    project_index = argv.index(compose_project)
    insert_at = project_index + 1
    return [*argv[:insert_at], "--env-file", str(env_file), *argv[insert_at:]]


def compose_down_argv(
    compose_files: tuple[pathlib.Path, ...],
    compose_project: str,
) -> list[str]:
    """Build argv for ``docker compose down`` without invoking a shell."""
    return compose_argv(compose_files, compose_project, "down", "-v", "--remove-orphans")


def compose_argv(
    compose_files: tuple[pathlib.Path, ...],
    compose_project: str,
    *subcommand: str,
) -> list[str]:
    """Build argv for docker compose against one or more compose files.

    Args:
        compose_files: Compose file paths for the live project.
        compose_project: Docker Compose project name.
        subcommand: Compose subcommand tokens.

    Returns:
        Argument vector for subprocess execution.
    """
    argv = ["docker", "compose"]
    for compose_file in compose_files:
        argv.extend(["-f", str(compose_file)])
    argv.extend(["-p", compose_project, *subcommand])
    return argv


def allocate_loopback_port() -> int:
    """Allocate a free loopback TCP port.

    Returns:
        Ephemeral port number bound on ``127.0.0.1``.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def probe_readiness(endpoint: str) -> ReadinessResult:
    """Perform one readiness HTTP probe.

    Args:
        endpoint: Full readiness URL.

    Returns:
        Observed status code and body excerpt.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(endpoint)
    except httpx.HTTPError as exc:
        return ReadinessResult(status_code=None, json_body=None, body_excerpt=str(exc))
    json_body: dict[str, object] | None = None
    try:
        payload = response.json()
        if isinstance(payload, dict):
            json_body = payload
    except ValueError:
        json_body = None
    excerpt = textwrap.shorten(response.text, width=240, placeholder="...")
    return ReadinessResult(
        status_code=response.status_code, json_body=json_body, body_excerpt=excerpt
    )


def is_ready(result: ReadinessResult) -> bool:
    """Return whether a readiness probe indicates backend readiness.

    Args:
        result: Last readiness probe result.

    Returns:
        True when HTTP 200 and required JSON checks are ok.
    """
    if result.status_code != 200 or result.json_body is None:
        return False
    checks = result.json_body.get("checks")
    if not isinstance(checks, dict):
        return False
    return (
        result.json_body.get("status") == "ok"
        and checks.get("db") == "ok"
        and checks.get("migrations") == "ok"
    )


DAEMON_READY_TIMEOUT_SECONDS = 10.0
RUNTIME_READY_TIMEOUT_SECONDS = 60.0
RUNTIME_DEREGISTER_TIMEOUT_SECONDS = 30.0
RUNTIME_POLL_INTERVAL_SECONDS = 1.0
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "cancelled", "timed_out", "canceled"})


@dataclass(slots=True)
class DaemonLifecycle:
    """Foreground daemon process lifecycle for agent sandbox tests."""

    cli_executable: pathlib.Path
    home_dir: pathlib.Path
    profile_name: str
    daemon_id: str
    workspaces_root: pathlib.Path
    opencode_path: pathlib.Path
    opencode_model: str
    agent_mode: str
    diagnostics: DiagnosticCollector
    _process: subprocess.Popen[str] | None = None
    _log_path: pathlib.Path | None = None

    def start(self) -> None:
        """Start the foreground daemon subprocess with isolated environment."""
        if self._process is not None and self._process.poll() is None:
            return
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces_root.mkdir(parents=True, exist_ok=True)
        log_path = self.home_dir / "daemon.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_path = log_path
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home_dir),
                "MULTICA_PROFILE": self.profile_name,
                "MULTICA_DAEMON_ID": self.daemon_id,
                "MULTICA_WORKSPACES_ROOT": str(self.workspaces_root),
                "MULTICA_OPENCODE_PATH": str(self.opencode_path.resolve()),
                "MULTICA_OPENCODE_MODEL": self.opencode_model,
                "MULTICA_DAEMON_POLL_INTERVAL": "1s",
                "MULTICA_DAEMON_HEARTBEAT_INTERVAL": "2s",
                "MULTICA_TEST_AGENT_MODE": self.agent_mode,
            }
        )
        log_handle = log_path.open("a", encoding="utf-8")
        try:
            self._process = subprocess.Popen(
                [str(self.cli_executable), "daemon", "start", "--foreground"],
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except OSError as exc:
            log_handle.close()
            raise LiveSetupError("daemon", f"failed to start daemon subprocess: {exc}") from exc
        deadline = time.monotonic() + DAEMON_READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise LiveSetupError(
                    "daemon",
                    f"daemon exited before ready with code {self._process.returncode}",
                )
            if self._daemon_status_running():
                return
            time.sleep(0.5)
        raise LiveSetupError("daemon", "daemon status did not report running within 10 seconds")

    def stop(self) -> None:
        """Stop the daemon with graceful CLI stop and process escalation."""
        self._run_daemon_cli(["daemon", "stop"], check=False)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if self._process is None or self._process.poll() is not None:
                return
            if not self._daemon_status_running():
                self._terminate_process(timeout=5.0)
                return
            time.sleep(0.5)
        self._terminate_process(timeout=5.0)

    def capture_status(self) -> dict[str, object]:
        """Return daemon status JSON or subprocess exit metadata."""
        if self._process is not None and self._process.poll() is not None:
            return {
                "running": False,
                "exit_code": self._process.returncode,
                "pid": self._process.pid,
            }
        completed = self._run_daemon_cli(["daemon", "status", "--output", "json"], check=False)
        if completed.returncode == 0 and completed.stdout.strip():
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError:
                payload = {"raw_stdout": completed.stdout}
            if isinstance(payload, dict):
                return payload
        return {
            "running": self._process is not None and self._process.poll() is None,
            "exit_code": None if self._process is None else self._process.returncode,
            "pid": None if self._process is None else self._process.pid,
            "status_exit_code": completed.returncode,
            "status_stderr": completed.stderr,
        }

    def daemon_log_tail(self, *, lines: int = 200) -> str:
        """Return the last lines of the daemon log file."""
        if self._log_path is None or not self._log_path.is_file():
            return ""
        content = self._log_path.read_text(encoding="utf-8", errors="replace")
        tail = content.splitlines()[-lines:]
        return "\n".join(tail) + ("\n" if tail else "")

    @property
    def is_running(self) -> bool:
        """Return whether the daemon subprocess is still running."""
        return self._process is not None and self._process.poll() is None

    @property
    def pid(self) -> int | None:
        """Return the daemon subprocess pid when running."""
        return None if self._process is None else self._process.pid

    def _daemon_status_running(self) -> bool:
        completed = self._run_daemon_cli(["daemon", "status", "--output", "json"], check=False)
        if completed.returncode != 0 or not completed.stdout.strip():
            return False
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return False
        return isinstance(payload, dict) and payload.get("running") is True

    def _run_daemon_cli(self, args: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        env["MULTICA_PROFILE"] = self.profile_name
        completed = subprocess.run(
            [str(self.cli_executable), *args],
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check and completed.returncode != 0:
            detail = textwrap.shorten(
                (completed.stderr or completed.stdout or "").strip(),
                width=240,
                placeholder="...",
            )
            raise LiveSetupError("daemon", f"daemon command failed: {detail}")
        return completed

    def _terminate_process(self, *, timeout: float) -> None:
        if self._process is None or self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5.0)


def _poll_until(
    *,
    deadline_seconds: float,
    interval_seconds: float,
    ready: Callable[[], bool],
) -> bool:
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if ready():
            return True
        time.sleep(interval_seconds)
    return False


def poll_runtime_online(
    oracle: DirectApiOracle,
    *,
    daemon_id: str,
    deadline_seconds: float = RUNTIME_READY_TIMEOUT_SECONDS,
) -> str:
    """Poll until exactly one online OpenCode runtime exists for a daemon."""
    runtime_id: str | None = None

    def _ready() -> bool:
        nonlocal runtime_id
        runtime_id = oracle.find_online_opencode_runtime(daemon_id)
        if runtime_id is None:
            return False
        online_matches = [
            entry
            for entry in oracle.list_runtimes_raw()
            if str(entry.get("daemon_id")) == daemon_id
            and str(entry.get("status", "")).lower() in {"online", "ready", "active"}
        ]
        return len(online_matches) == 1

    if not _poll_until(
        deadline_seconds=deadline_seconds,
        interval_seconds=RUNTIME_POLL_INTERVAL_SECONDS,
        ready=_ready,
    ):
        raise LiveSetupError("runtime", f"runtime not ready within {deadline_seconds}s")
    assert runtime_id is not None
    return runtime_id


def poll_runtime_deregistered(
    oracle: DirectApiOracle,
    *,
    daemon_id: str,
    runtime_id: str | None,
    deadline_seconds: float = RUNTIME_DEREGISTER_TIMEOUT_SECONDS,
) -> None:
    """Poll until a runtime is absent or explicitly non-routable."""
    if _poll_until(
        deadline_seconds=deadline_seconds,
        interval_seconds=RUNTIME_POLL_INTERVAL_SECONDS,
        ready=lambda: oracle.runtime_absent_or_non_routable(daemon_id, runtime_id),
    ):
        return
    raise LiveSetupError(
        "runtime",
        f"runtime still routable after {deadline_seconds}s for daemon {daemon_id}",
    )

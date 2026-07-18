from __future__ import annotations

import os
import pathlib
import platform
import secrets as secrets_module
import shutil
import socket
import subprocess
import textwrap
import time
from dataclasses import dataclass

import httpx

from tests.live.diagnostics import DiagnosticCollector
from tests.live.exceptions import LiveSetupError
from tests.live.settings import CompatibilityTarget, LiveSettings, LiveTestEnvironment, LiveTestRun

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
        backend_image, image_tag = self._resolve_backend_image_refs()
        return {
            "APP_ENV": "development",
            "MULTICA_DEV_VERIFICATION_CODE": "888888",
            "JWT_SECRET": secrets_module.token_urlsafe(32),
            "POSTGRES_DB": "multica",
            "POSTGRES_USER": "multica",
            "POSTGRES_PASSWORD": secrets_module.token_urlsafe(24),
            "MULTICA_BACKEND_IMAGE": backend_image,
            "MULTICA_IMAGE_TAG": image_tag,
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

    def _blocking_image_policy(self) -> bool:
        if os.environ.get("MULTICA_LIVE_ALLOW_IMAGE_OVERRIDE") == "1":
            return False
        if self._settings.existing_url is not None:
            return False
        if os.environ.get("CI"):
            return True
        if self._settings.suite_profile == "smoke":
            return True
        return self._target.cli_source == "release"

    def _resolve_backend_image_refs(self) -> tuple[str, str]:
        if self._blocking_image_policy():
            return self._target.backend_image, self._target.backend_tag
        return (
            os.environ.get("MULTICA_LIVE_BACKEND_IMAGE", self._target.backend_image),
            os.environ.get("MULTICA_LIVE_IMAGE_TAG", self._target.backend_tag),
        )

    def _platform_digest(self) -> str:
        system = platform.system().lower()
        machine = platform.machine().lower()
        if system == "linux" and machine in {"x86_64", "amd64"}:
            digest = self._target.backend_digest_linux_amd64
        else:
            digest = self._target.backend_digest
        if digest is None or not digest.startswith("sha256:"):
            raise LiveSetupError("compose", "concrete backend digest is required for compose startup")
        return digest

    def _pull_backend_image(self, digest: str) -> None:
        image_ref = f"{self._target.backend_image}@{digest}"
        self._run_command(["docker", "pull", image_ref], stage="compose")

    def _verify_running_backend_digest(self, digest: str) -> None:
        if not self._blocking_image_policy() and os.environ.get("CI") != "true":
            return
        if self._target.cli_source != "release" and not os.environ.get("CI"):
            return
        container_id = self._run_command(
            compose_argv(self._compose_files(), self._run.compose_project, "ps", "-q", "backend"),
            stage="compose",
        ).stdout.strip()
        if not container_id:
            raise LiveSetupError("compose", "backend container id not found for digest verification")
        inspect = self._run_command(
            ["docker", "inspect", "--format", "{{.Image}}", container_id.splitlines()[0]],
            stage="compose",
        ).stdout.strip()
        expected = digest.removeprefix("sha256:")
        if expected not in inspect:
            raise LiveSetupError(
                "compose",
                f"backend image digest mismatch: expected {digest}, got {inspect}",
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
    return ReadinessResult(status_code=response.status_code, json_body=json_body, body_excerpt=excerpt)


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

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import tempfile
import tomllib
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlparse

from multica_py.client import MulticaClient

if TYPE_CHECKING:
    from tests.live.oracle import DirectApiOracle


class LiveSetupError(RuntimeError):
    """Raised when live test environment setup fails."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


class ResourceAbsentError(Exception):
    """Raised when cleanup finds an already absent resource."""


DEFAULT_TARGET_FILE = "contracts/multica-live-target.toml"
PLACEHOLDER_PATTERNS = (
    re.compile(r"^latest$", re.IGNORECASE),
    re.compile(r"^X\.Y\.Z$", re.IGNORECASE),
    re.compile(r"^sha256:\.\.\.$"),
)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SuiteProfile = Literal["smoke", "extended"]
CliSource = Literal["release", "source-build", "local"]


@dataclass(frozen=True, slots=True)
class CompatibilityTarget:
    """Pinned Multica CLI and backend compatibility target."""

    name: str
    upstream_ref: str
    upstream_commit: str
    compose_file: str
    backend_image: str
    backend_tag: str
    backend_digest: str
    backend_digest_linux_amd64: str | None
    cli_source: CliSource
    cli_version_expected: str
    cli_release_sha256_linux_amd64: str | None
    cli_release_sha256_darwin_arm64: str | None
    cli_release_sha256_darwin_amd64: str | None
    verified_at: str


@dataclass(frozen=True, slots=True)
class LiveSettings:
    """Validated live test configuration."""

    target_file: pathlib.Path
    cli_executable: pathlib.Path | None
    resolve_cli: bool
    upstream_dir: pathlib.Path | None
    artifact_dir: pathlib.Path
    suite_profile: SuiteProfile
    existing_url: str | None
    keep_env: bool
    ready_timeout_seconds: float


@dataclass(frozen=True, slots=True)
class LiveTestRun:
    """Metadata for one live pytest session."""

    run_id: str
    suite_profile: SuiteProfile
    started_at: datetime.datetime
    target: CompatibilityTarget
    compose_project: str
    artifact_dir: pathlib.Path
    secrets_dir: pathlib.Path


@dataclass(frozen=True, slots=True)
class LiveTestEnvironment:
    """Started live backend environment."""

    server_url: str
    compose_project: str
    compose_files: tuple[pathlib.Path, ...]
    home_dir: pathlib.Path
    profile_name: str
    cli_executable: pathlib.Path
    readiness_endpoint: str
    readiness_timeout_seconds: float
    managed_compose: bool


def generate_run_id() -> str:
    """Return a unique 32-character lowercase hex run id."""
    return uuid.uuid4().hex


def validate_run_id(run_id: str) -> None:
    """Raise LiveSetupError when run_id is not 32 lowercase hex characters."""
    if not RUN_ID_PATTERN.match(run_id):
        raise LiveSetupError("run_id", "run_id must be 32 lowercase hex characters")


def live_run_prefix(run_id: str) -> str:
    """Return the canonical live run prefix for one run id."""
    validate_run_id(run_id)
    return f"multica-py-live-{run_id}"


def compose_project_name(run_id: str) -> str:
    """Return the Docker Compose project name for one run id."""
    return live_run_prefix(run_id)


def profile_name_for_run(run_id: str) -> str:
    """Return the CLI profile directory name for one run id."""
    return f"live-{run_id}"


def bootstrap_email(run_id: str) -> str:
    """Return the development bootstrap email for one run id."""
    return f"multica-py-live+{run_id}@localhost"


def workspace_slug(run_id: str, suffix: str) -> str:
    """Return a workspace slug within upstream length limits."""
    base = f"mpy-{run_id}-{suffix}"
    return _truncate_with_hash(base, max_len=48)


def resource_prefix(run_id: str, test_fragment: str) -> str:
    """Return a unique resource name prefix for one test."""
    base = f"mpy-live-{run_id}-{test_fragment}"
    return _truncate_with_hash(base, max_len=64)


MAX_LABEL_NAME_LEN = 32


def label_name(prefix: str, suffix: str = "") -> str:
    """Return a label name within the pinned upstream max length."""
    tail = f"-{suffix}" if suffix else ""
    if len(tail) >= MAX_LABEL_NAME_LEN:
        return _truncate_with_hash(tail.lstrip("-"), max_len=MAX_LABEL_NAME_LEN)
    return f"{_truncate_with_hash(prefix, max_len=MAX_LABEL_NAME_LEN - len(tail))}{tail}"


def _truncate_with_hash(value: str, *, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    digest = hashlib.sha256(value.encode()).hexdigest()[:8]
    keep = max_len - 9
    return f"{value[:keep]}-{digest}"


def _reject_placeholder(field: str, value: str) -> None:
    if not value.strip():
        raise LiveSetupError("target", f"{field} must not be empty")
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.match(value.strip()):
            raise LiveSetupError("target", f"{field} contains forbidden placeholder {value!r}")


def load_compatibility_target(path: pathlib.Path) -> CompatibilityTarget:
    """Load and validate a compatibility target manifest.

    Args:
        path: Path to the target TOML manifest.

    Returns:
        Validated compatibility target.

    Raises:
        LiveSetupError: If the manifest is missing or invalid.
    """
    if not path.is_file():
        raise LiveSetupError("target", f"target manifest not found: {path}")
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    schema_version = raw.get("schema_version")
    if schema_version != 1:
        raise LiveSetupError("target", f"unsupported schema_version: {schema_version!r}")
    fields = {
        "name": str(raw["name"]),
        "upstream_ref": str(raw["upstream_ref"]),
        "upstream_commit": str(raw["upstream_commit"]),
        "compose_file": str(raw["compose_file"]),
        "backend_image": str(raw["backend_image"]),
        "backend_tag": str(raw["backend_tag"]),
        "backend_digest": str(raw["backend_digest"]),
        "cli_source": str(raw["cli_source"]),
        "cli_version_expected": str(raw["cli_version_expected"]),
        "verified_at": str(raw["verified_at"]),
    }
    for key, value in fields.items():
        _reject_placeholder(key, value)
    if not COMMIT_PATTERN.match(fields["upstream_commit"]):
        raise LiveSetupError("target", "upstream_commit must be a full 40-char SHA")
    if fields["cli_source"] not in {"release", "source-build", "local"}:
        raise LiveSetupError("target", f"unsupported cli_source: {fields['cli_source']!r}")
    if not DIGEST_PATTERN.match(fields["backend_digest"]):
        raise LiveSetupError("target", "backend_digest must be a concrete sha256 digest")
    digest_amd64_raw = raw.get("backend_digest_linux_amd64")
    digest_amd64 = None if digest_amd64_raw is None else str(digest_amd64_raw)
    if digest_amd64 is not None:
        if not DIGEST_PATTERN.match(digest_amd64):
            raise LiveSetupError("target", "backend_digest_linux_amd64 must be a concrete digest")
    checksum_fields: dict[str, object | None] = {
        "cli_release_sha256_linux_amd64": raw.get("cli_release_sha256_linux_amd64"),
        "cli_release_sha256_darwin_arm64": raw.get("cli_release_sha256_darwin_arm64"),
        "cli_release_sha256_darwin_amd64": raw.get("cli_release_sha256_darwin_amd64"),
    }
    checksums: dict[str, str | None] = {}
    for checksum_key, checksum_raw in checksum_fields.items():
        if checksum_raw is None:
            checksums[checksum_key] = None
            continue
        checksum = str(checksum_raw)
        if not SHA256_PATTERN.match(checksum):
            raise LiveSetupError(
                "target", f"{checksum_key} must be a 64-char lowercase sha256 hex digest"
            )
        checksums[checksum_key] = checksum
    if fields["cli_source"] == "release" and not any(checksums.values()):
        raise LiveSetupError(
            "target",
            "cli_release_sha256_* is required in the target manifest for cli_source=release",
        )
    return CompatibilityTarget(
        name=fields["name"],
        upstream_ref=fields["upstream_ref"],
        upstream_commit=fields["upstream_commit"],
        compose_file=fields["compose_file"],
        backend_image=fields["backend_image"],
        backend_tag=fields["backend_tag"],
        backend_digest=fields["backend_digest"],
        backend_digest_linux_amd64=digest_amd64,
        cli_source=fields["cli_source"],  # type: ignore[arg-type]
        cli_version_expected=fields["cli_version_expected"],
        cli_release_sha256_linux_amd64=checksums["cli_release_sha256_linux_amd64"],
        cli_release_sha256_darwin_arm64=checksums["cli_release_sha256_darwin_arm64"],
        cli_release_sha256_darwin_amd64=checksums["cli_release_sha256_darwin_amd64"],
        verified_at=fields["verified_at"],
    )


def _parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip() in {"1", "true", "True", "yes", "YES"}


def _parse_keep_env() -> bool:
    raw = os.environ.get("MULTICA_LIVE_KEEP_ENV")
    if raw is None or raw == "":
        return False
    if os.environ.get("CI"):
        raise LiveSetupError(
            "target",
            "MULTICA_LIVE_KEEP_ENV is forbidden in CI",
        )
    if raw.strip() != "1":
        raise LiveSetupError(
            "target",
            "MULTICA_LIVE_KEEP_ENV must be exactly 1 when set locally",
        )
    return True


def _parse_ready_timeout() -> float:
    raw = os.environ.get("MULTICA_LIVE_READY_TIMEOUT")
    if raw is None or raw == "":
        return 120.0
    try:
        value = float(raw)
    except ValueError as exc:
        raise LiveSetupError("target", "MULTICA_LIVE_READY_TIMEOUT must be numeric") from exc
    if value < 10 or value > 600:
        raise LiveSetupError("target", "MULTICA_LIVE_READY_TIMEOUT must be between 10 and 600")
    return value


def _validate_loopback_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"}:
        raise LiveSetupError("target", "MULTICA_LIVE_EXISTING_URL must use http or https")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise LiveSetupError("target", "MULTICA_LIVE_EXISTING_URL must be loopback-only")
    return url.rstrip("/")


def load_live_settings(
    *,
    resolve_cli: bool | None = None,
    repo_root: pathlib.Path | None = None,
) -> LiveSettings:
    """Load live settings from environment variables.

    Args:
        resolve_cli: Override resolver mode; defaults to env flag.
        repo_root: Repository root for default target path resolution.

    Returns:
        Validated live settings.

    Raises:
        LiveSetupError: If required inputs are missing or invalid.
    """
    root = repo_root or pathlib.Path.cwd()
    target_raw = os.environ.get("MULTICA_LIVE_TARGET_FILE", DEFAULT_TARGET_FILE)
    target_file = pathlib.Path(target_raw)
    if not target_file.is_absolute():
        target_file = root / target_file
    resolve = (
        resolve_cli if resolve_cli is not None else _parse_bool_env("MULTICA_LIVE_RESOLVE_CLI")
    )
    cli_raw = os.environ.get("MULTICA_LIVE_CLI")
    cli_executable = None if not cli_raw else pathlib.Path(cli_raw)
    if cli_executable is not None and not cli_executable.is_absolute():
        raise LiveSetupError("target", "MULTICA_LIVE_CLI must be an absolute path")
    upstream_raw = os.environ.get("MULTICA_LIVE_UPSTREAM_DIR")
    upstream_dir = None if not upstream_raw else pathlib.Path(upstream_raw)
    if upstream_dir is not None and not upstream_dir.is_absolute():
        raise LiveSetupError("target", "MULTICA_LIVE_UPSTREAM_DIR must be an absolute path")
    artifact_raw = os.environ.get("MULTICA_LIVE_ARTIFACT_DIR")
    if artifact_raw:
        artifact_dir = pathlib.Path(artifact_raw)
        if not artifact_dir.is_absolute():
            raise LiveSetupError("target", "MULTICA_LIVE_ARTIFACT_DIR must be absolute")
    else:
        artifact_dir = pathlib.Path(temp_artifact_dir())
    mode_raw = os.environ.get("MULTICA_LIVE_MODE", "smoke")
    if mode_raw not in {"smoke", "extended"}:
        raise LiveSetupError("target", "MULTICA_LIVE_MODE must be smoke or extended")
    existing_raw = os.environ.get("MULTICA_LIVE_EXISTING_URL")
    existing_url = None if not existing_raw else _validate_loopback_url(existing_raw)
    if cli_executable is None and not resolve:
        raise LiveSetupError(
            "target", "MULTICA_LIVE_CLI is required unless resolver mode is enabled"
        )
    if existing_url is None and upstream_dir is None:
        raise LiveSetupError("target", "MULTICA_LIVE_UPSTREAM_DIR is required for compose mode")
    if cli_executable is not None and not os.access(cli_executable, os.X_OK):
        raise LiveSetupError("target", f"MULTICA_LIVE_CLI is not executable: {cli_executable}")
    return LiveSettings(
        target_file=target_file,
        cli_executable=cli_executable,
        resolve_cli=resolve,
        upstream_dir=upstream_dir,
        artifact_dir=artifact_dir,
        suite_profile=mode_raw,  # type: ignore[arg-type]
        existing_url=existing_url,
        keep_env=_parse_keep_env(),
        ready_timeout_seconds=_parse_ready_timeout(),
    )


def temp_artifact_dir() -> str:
    """Return a default temporary artifact directory path."""
    return str(pathlib.Path(tempfile.gettempdir()) / "multica-py-live-artifacts")


def resolve_secrets_base_dir(artifact_root: pathlib.Path) -> pathlib.Path:
    """Return a secrets directory root outside published artifact uploads.

    Args:
        artifact_root: Diagnostic artifact upload root.

    Returns:
        Absolute secrets base directory with restrictive permissions.

    Raises:
        LiveSetupError: If the secrets path is missing, relative, or under artifacts.
    """
    raw = os.environ.get("MULTICA_LIVE_SECRETS_DIR")
    if raw:
        base = pathlib.Path(raw)
        if not base.is_absolute():
            raise LiveSetupError("target", "MULTICA_LIVE_SECRETS_DIR must be absolute")
    else:
        base = pathlib.Path(tempfile.gettempdir()) / "multica-py-live-secrets"
    resolved_base = base.resolve()
    resolved_artifacts = artifact_root.resolve()
    if resolved_base == resolved_artifacts or resolved_base.is_relative_to(resolved_artifacts):
        raise LiveSetupError(
            "target",
            "MULTICA_LIVE_SECRETS_DIR must be outside MULTICA_LIVE_ARTIFACT_DIR",
        )
    resolved_base.mkdir(parents=True, exist_ok=True)
    resolved_base.chmod(0o700)
    return resolved_base


def create_live_test_run(
    target: CompatibilityTarget,
    settings: LiveSettings,
    *,
    run_id: str | None = None,
) -> LiveTestRun:
    """Create a new live test run record.

    Args:
        target: Verified compatibility target.
        settings: Live settings for the session.
        run_id: Optional explicit run id.

    Returns:
        Initialized live test run metadata.
    """
    resolved_run_id = run_id or generate_run_id()
    validate_run_id(resolved_run_id)
    artifact_dir = settings.artifact_dir / resolved_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    secrets_dir = resolve_secrets_base_dir(settings.artifact_dir) / resolved_run_id
    secrets_dir.mkdir(parents=True, exist_ok=True)
    secrets_dir.chmod(0o700)
    return LiveTestRun(
        run_id=resolved_run_id,
        suite_profile=settings.suite_profile,
        started_at=datetime.datetime.now(tz=datetime.UTC),
        target=target,
        compose_project=compose_project_name(resolved_run_id),
        artifact_dir=artifact_dir,
        secrets_dir=secrets_dir,
    )


def write_cli_profile(
    home_dir: pathlib.Path,
    profile_name: str,
    *,
    server_url: str,
    app_url: str,
    workspace_id: str,
    token: str,
) -> pathlib.Path:
    """Write an isolated Multica CLI profile config file.

    Args:
        home_dir: Temporary HOME directory for the live session.
        profile_name: Profile directory name such as ``live-<run-id>``.
        server_url: Backend server URL.
        app_url: Application URL for the profile.
        workspace_id: Primary workspace identifier.
        token: Personal access token for CLI authentication.

    Returns:
        Path to the written ``config.json`` file.

    Raises:
        LiveSetupError: If the profile would be written outside the temp HOME.
    """
    validate_not_real_home(home_dir)
    profile_dir = home_dir.resolve() / ".multica" / "profiles" / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    config_path = profile_dir / "config.json"
    payload = {
        "server_url": server_url,
        "app_url": app_url,
        "workspace_id": workspace_id,
        "token": token,
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    config_path.chmod(0o600)
    return config_path


def profile_config_path(home_dir: pathlib.Path, profile_name: str) -> pathlib.Path:
    """Return the expected CLI profile config path.

    Args:
        home_dir: Temporary HOME directory for the live session.
        profile_name: Profile directory name.

    Returns:
        Expected ``config.json`` path under the temp HOME.
    """
    return home_dir / ".multica" / "profiles" / profile_name / "config.json"


def ensure_temp_home(base_dir: pathlib.Path, run_id: str) -> pathlib.Path:
    """Create a temporary HOME directory for a live session.

    Args:
        base_dir: Parent directory for temp homes.
        run_id: Unique run identifier.

    Returns:
        Created HOME directory path.
    """
    home_dir = base_dir / f"home-{run_id}"
    home_dir.mkdir(parents=True, exist_ok=False)
    validate_not_real_home(home_dir)
    return home_dir


def remove_temp_home(home_dir: pathlib.Path) -> None:
    """Remove a temporary HOME directory tree.

    Args:
        home_dir: Temporary HOME directory to remove.
    """
    if home_dir.exists():
        shutil.rmtree(home_dir, ignore_errors=True)


def validate_not_real_home(home_dir: pathlib.Path) -> None:
    """Fail closed when a path resolves to the real HOME directory.

    Args:
        home_dir: Candidate HOME directory.

    Raises:
        LiveSetupError: If the path equals the real HOME directory.
    """
    if home_dir.resolve() == pathlib.Path.home().resolve():
        raise LiveSetupError("profile", "live session HOME must not equal real HOME")


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


@dataclass(frozen=True, slots=True)
class LiveContext:
    """Context passed to every LiveOperation.invoke and CRUD round-trip.

    Attributes:
        client: Live SDK client bound to the primary workspace.
        oracle: Direct HTTP oracle for arrange/assert/cleanup.
        register_resource: Registers created resources for teardown.
        identity: Authenticated test identity with redacted secrets.
    """

    client: MulticaClient
    oracle: DirectApiOracle
    register_resource: Callable[..., None]
    identity: TestIdentity


_ALLOWED_AGENT_MODES = frozenset({"success", "error", "timeout", "wrong-edit"})
_ALLOWED_CLEANUP_INJECTIONS = frozenset({"remove-resource"})


@dataclass(frozen=True, slots=True)
class AgentSandboxSettings:
    """Validated deterministic agent sandbox configuration."""

    agent_mode: str
    inject_cleanup_failure: str | None
    opencode_path: pathlib.Path
    opencode_model: str


@dataclass(frozen=True, slots=True)
class LiveRunContext:
    """Immutable paths and identifiers for one agent sandbox run."""

    run_id: str
    prefix: str
    temp_root: pathlib.Path
    home: pathlib.Path
    workspaces_root: pathlib.Path
    sandbox_dir: pathlib.Path
    profile_name: str
    daemon_id: str
    artifact_dir: pathlib.Path
    workspace_id: str | None = None
    project_id: str | None = None
    resource_id: str | None = None
    runtime_id: str | None = None
    agent_id: str | None = None
    issue_id: str | None = None
    run_execution_id: str | None = None

    def diagnostics_payload(self) -> dict[str, object]:
        """Return a redaction-safe snapshot for diagnostic bundles."""
        return {
            key: str(value) if isinstance(value, pathlib.Path) else value
            for key, value in asdict(self).items()
        }


def load_agent_sandbox_settings(*, repo_root: pathlib.Path | None = None) -> AgentSandboxSettings:
    """Load and validate agent sandbox settings from the environment.

    Args:
        repo_root: Repository root for default fake OpenCode path resolution.

    Returns:
        Validated agent sandbox settings.

    Raises:
        LiveSetupError: If required settings are missing or invalid.
    """
    root = repo_root or pathlib.Path.cwd()
    raw_mode = os.environ.get("MULTICA_TEST_AGENT_MODE")
    agent_mode = "success" if raw_mode in {None, ""} else raw_mode.strip()
    if agent_mode not in _ALLOWED_AGENT_MODES:
        raise LiveSetupError(
            "sandbox",
            f"MULTICA_TEST_AGENT_MODE must be one of {sorted(_ALLOWED_AGENT_MODES)}",
        )
    inject_raw = os.environ.get("MULTICA_TEST_INJECT_CLEANUP_FAILURE")
    inject_cleanup_failure = None if not inject_raw else inject_raw.strip()
    if (
        inject_cleanup_failure is not None
        and inject_cleanup_failure not in _ALLOWED_CLEANUP_INJECTIONS
    ):
        raise LiveSetupError(
            "sandbox",
            f"MULTICA_TEST_INJECT_CLEANUP_FAILURE must be one of {sorted(_ALLOWED_CLEANUP_INJECTIONS)}",
        )
    opencode_raw = os.environ.get("MULTICA_TEST_OPENCODE_PATH")
    if opencode_raw:
        opencode_path = pathlib.Path(opencode_raw)
    else:
        opencode_path = root / "tests" / "fixtures" / "fake_opencode.py"
    if not opencode_path.is_absolute():
        raise LiveSetupError("sandbox", "MULTICA_TEST_OPENCODE_PATH must be absolute when set")
    if not opencode_path.is_file():
        raise LiveSetupError("sandbox", f"OpenCode executable not found: {opencode_path}")
    if not os.access(opencode_path, os.X_OK):
        raise LiveSetupError("sandbox", f"OpenCode executable is not executable: {opencode_path}")
    return AgentSandboxSettings(
        agent_mode=agent_mode,
        inject_cleanup_failure=inject_cleanup_failure,
        opencode_path=opencode_path,
        opencode_model="multica-test/fake",
    )


def create_live_run_context(
    *,
    run_id: str,
    artifact_root: pathlib.Path,
    temp_parent: pathlib.Path | None = None,
) -> LiveRunContext:
    """Create isolated directories for one agent sandbox run.

    Args:
        run_id: Unique 32-character lowercase hex run identifier.
        artifact_root: Root directory for diagnostic artifacts.
        temp_parent: Optional parent directory for temp roots.

    Returns:
        Initialized live run context with canonical paths.

    Raises:
        LiveSetupError: If path validation fails.
    """
    validate_run_id(run_id)
    prefix = live_run_prefix(run_id)
    parent = temp_parent or pathlib.Path(tempfile.gettempdir())
    temp_root = parent / prefix
    if temp_root.exists():
        shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=False)
    home = temp_root / "home"
    workspaces_root = temp_root / "workspaces"
    sandbox_dir = temp_root / "sandbox" / "project"
    home.mkdir(parents=True, exist_ok=False)
    workspaces_root.mkdir(parents=True, exist_ok=False)
    sandbox_dir.mkdir(parents=True, exist_ok=False)
    validate_not_real_home(home)
    artifact_dir = artifact_root / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return LiveRunContext(
        run_id=run_id,
        prefix=prefix,
        temp_root=temp_root,
        home=home,
        workspaces_root=workspaces_root,
        sandbox_dir=sandbox_dir.resolve(),
        profile_name=prefix,
        daemon_id=prefix,
        artifact_dir=artifact_dir,
    )


def remove_live_run_context(run_context: LiveRunContext) -> None:
    """Remove temporary directories owned by one live run context.

    Args:
        run_context: Live run context whose temp root should be removed.
    """
    if run_context.temp_root.exists():
        shutil.rmtree(run_context.temp_root, ignore_errors=True)


CANARY_ENV_OPENCODE_PATH = "MULTICA_CANARY_OPENCODE_PATH"
CANARY_ENV_MODEL = "MULTICA_CANARY_MODEL"
CANARY_ENV_SECRET_NAMES = "MULTICA_CANARY_SECRET_NAMES"
CANARY_REQUIRED_VARIABLES = (
    CANARY_ENV_OPENCODE_PATH,
    CANARY_ENV_MODEL,
    CANARY_ENV_SECRET_NAMES,
)
CANARY_COST_CEILING_USD = 0.10


@dataclass(frozen=True, slots=True)
class OpenCodeCanarySettings:
    """Validated real OpenCode canary configuration."""

    opencode_path: pathlib.Path
    model: str
    secret_names: tuple[str, ...]

    def secret_values(self) -> dict[str, str]:
        """Return configured secret values keyed by environment variable name."""
        return {name: os.environ[name] for name in self.secret_names}

    def to_sandbox_settings(self) -> AgentSandboxSettings:
        """Map canary settings to daemon sandbox settings."""
        return AgentSandboxSettings(
            agent_mode="success",
            inject_cleanup_failure=None,
            opencode_path=self.opencode_path,
            opencode_model=self.model,
        )


def _parse_canary_secret_names(raw: str) -> tuple[str, ...] | None:
    names = tuple(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))
    return names or None


def collect_missing_canary_variables(
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Return every missing or invalid canary environment variable name.

    Args:
        environ: Environment mapping; defaults to ``os.environ``.

    Returns:
        Sorted unique variable names that block canary execution.
    """
    source = os.environ if environ is None else environ
    missing: list[str] = []
    raw_opencode = source.get(CANARY_ENV_OPENCODE_PATH)
    opencode_path = (
        pathlib.Path(raw_opencode.strip()) if raw_opencode and raw_opencode.strip() else None
    )
    if (
        opencode_path is None
        or not opencode_path.is_absolute()
        or not opencode_path.is_file()
        or not os.access(opencode_path, os.X_OK)
    ):
        missing.append(CANARY_ENV_OPENCODE_PATH)
    model_raw = source.get(CANARY_ENV_MODEL)
    if model_raw is None or not model_raw.strip():
        missing.append(CANARY_ENV_MODEL)
    secret_names_raw = source.get(CANARY_ENV_SECRET_NAMES)
    if secret_names_raw is None or not secret_names_raw.strip():
        missing.append(CANARY_ENV_SECRET_NAMES)
        return tuple(sorted(set(missing)))
    secret_names = _parse_canary_secret_names(secret_names_raw)
    if secret_names is None:
        missing.append(CANARY_ENV_SECRET_NAMES)
        return tuple(sorted(set(missing)))
    for secret_name in secret_names:
        secret_value = source.get(secret_name)
        if secret_value is None or not secret_value.strip():
            missing.append(secret_name)
    return tuple(sorted(set(missing)))


def load_opencode_canary_settings(
    environ: Mapping[str, str] | None = None,
) -> OpenCodeCanarySettings:
    """Load validated canary settings from the environment.

    Args:
        environ: Environment mapping; defaults to ``os.environ``.

    Returns:
        Validated canary settings.

    Raises:
        LiveSetupError: If required canary variables are missing or invalid.
    """
    missing = collect_missing_canary_variables(environ)
    if missing:
        raise LiveSetupError(
            "canary",
            f"canary environment incomplete: missing {', '.join(missing)}",
        )
    source = os.environ if environ is None else environ
    opencode_path = pathlib.Path(source[CANARY_ENV_OPENCODE_PATH].strip())
    secret_names = _parse_canary_secret_names(source[CANARY_ENV_SECRET_NAMES])
    assert secret_names is not None
    return OpenCodeCanarySettings(
        opencode_path=opencode_path,
        model=source[CANARY_ENV_MODEL].strip(),
        secret_names=secret_names,
    )


def skip_if_canary_environment_incomplete(
    environ: Mapping[str, str] | None = None,
) -> None:
    """Skip the current test session when canary configuration is incomplete.

    Args:
        environ: Environment mapping; defaults to ``os.environ``.
    """
    import pytest

    missing = collect_missing_canary_variables(environ)
    if missing:
        pytest.skip(f"canary environment incomplete: missing {', '.join(missing)}")

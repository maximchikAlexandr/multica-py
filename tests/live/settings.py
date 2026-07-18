from __future__ import annotations

import datetime
import hashlib
import os
import pathlib
import re
import tempfile
import tomllib
import uuid
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from tests.live.exceptions import LiveSetupError

DEFAULT_TARGET_FILE = "contracts/multica-live-target.toml"
PLACEHOLDER_PATTERNS = (
    re.compile(r"^latest$", re.IGNORECASE),
    re.compile(r"^X\.Y\.Z$", re.IGNORECASE),
    re.compile(r"^sha256:\.\.\.$"),
)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
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
    """Return a filesystem-safe unique run identifier.

    Returns:
        A short unique run id suitable for compose project names.
    """
    return uuid.uuid4().hex[:12]


def compose_project_name(run_id: str) -> str:
    """Build the Docker Compose project name for a run.

    Args:
        run_id: Unique run identifier.

    Returns:
        Compose project name prefixed with ``multica-py-live-``.
    """
    return f"multica-py-live-{run_id}"


def profile_name_for_run(run_id: str) -> str:
    """Build the CLI profile name for a run.

    Args:
        run_id: Unique run identifier.

    Returns:
        Profile directory name ``live-<run-id>``.
    """
    return f"live-{run_id}"


def bootstrap_email(run_id: str) -> str:
    """Build the bootstrap email address for a run.

    Args:
        run_id: Unique run identifier.

    Returns:
        Development bootstrap email for the run.
    """
    return f"multica-py-live+{run_id}@localhost"


def workspace_slug(run_id: str, suffix: str) -> str:
    """Build a workspace slug with upstream length limits.

    Args:
        run_id: Unique run identifier.
        suffix: Workspace suffix such as ``a`` or ``b``.

    Returns:
        Truncated slug with optional hash suffix.
    """
    base = f"mpy-{run_id}-{suffix}"
    return _truncate_with_hash(base, max_len=48)


def resource_prefix(run_id: str, test_fragment: str) -> str:
    """Build a unique resource name prefix for a test.

    Args:
        run_id: Unique run identifier.
        test_fragment: Short test-specific fragment.

    Returns:
        Truncated prefix with optional hash suffix.
    """
    base = f"mpy-live-{run_id}-{test_fragment}"
    return _truncate_with_hash(base, max_len=64)


MAX_LABEL_NAME_LEN = 32


def label_name(prefix: str, suffix: str = "") -> str:
    """Build a label name within the pinned upstream max length.

    Args:
        prefix: Unique resource prefix from ``resource_name``.
        suffix: Optional short suffix such as ``crud`` or ``a``.

    Returns:
        Name of at most ``MAX_LABEL_NAME_LEN`` characters.
    """
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
    checksum_fields = {
        "cli_release_sha256_linux_amd64": raw.get("cli_release_sha256_linux_amd64"),
        "cli_release_sha256_darwin_arm64": raw.get("cli_release_sha256_darwin_arm64"),
        "cli_release_sha256_darwin_amd64": raw.get("cli_release_sha256_darwin_amd64"),
    }
    checksums: dict[str, str | None] = {}
    for key, value in checksum_fields.items():
        if value is None:
            checksums[key] = None
            continue
        checksum = str(value)
        if not SHA256_PATTERN.match(checksum):
            raise LiveSetupError("target", f"{key} must be a 64-char lowercase sha256 hex digest")
        checksums[key] = checksum
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
    resolve = resolve_cli if resolve_cli is not None else _parse_bool_env("MULTICA_LIVE_RESOLVE_CLI")
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
        raise LiveSetupError("target", "MULTICA_LIVE_CLI is required unless resolver mode is enabled")
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

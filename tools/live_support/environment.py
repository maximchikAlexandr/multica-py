"""Canonical environment/target models and parsers for multica-py scripts.

This module is the shared canonical home for environment, target, and settings
models that both scripts and live tests rely on. The canonical definitions live
here so the ``tools/`` layer never depends on ``tests/`` (spec FR-022).

Exports:
  - DEFAULT_TARGET_FILE: relative path to the canonical multica-live target.
  - LiveTarget: declarative description of where to find a multica binary.
  - Environment: declarative description of the current live test env.
  - LiveSetupError: exception class for live environment setup failures.
  - CompatibilityTarget, LiveSettings, SuiteProfile, CliSource: pinned
    compatibility target and live settings models.
  - ResourceAbsentError, SecretString, AgentSandboxSettings,
    OpenCodeCanarySettings: shared operational data types.
  - CANARY_ENV_*, collect_missing_canary_variables, load_opencode_canary_settings:
    canary environment checking utilities.
  - parse_target(spec: str) -> LiveTarget: parse "kind:path" or "path".
  - parse_environment(env: Mapping[str, str] | None) -> Environment.
  - load_compatibility_target(path: pathlib.Path) -> CompatibilityTarget.
  - load_live_settings(...) -> LiveSettings.
"""

from __future__ import annotations

import os
import pathlib
import re
import tempfile
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast
from urllib.parse import urlparse

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


class LiveSetupError(RuntimeError):
    """Raised when live test environment setup fails."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


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
    raw = cast("dict[str, object]", tomllib.loads(path.read_text(encoding="utf-8")))
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
    cli_source = cast("CliSource", fields["cli_source"])
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
        cli_source=cli_source,
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
        artifact_dir = pathlib.Path(tempfile.gettempdir()) / "multica-py-live-artifacts"
    mode_raw = os.environ.get("MULTICA_LIVE_MODE", "smoke")
    if mode_raw not in {"smoke", "extended"}:
        raise LiveSetupError("target", "MULTICA_LIVE_MODE must be smoke or extended")
    suite_profile = cast("SuiteProfile", mode_raw)
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
        suite_profile=suite_profile,
        existing_url=existing_url,
        keep_env=_parse_keep_env(),
        ready_timeout_seconds=_parse_ready_timeout(),
    )


@dataclass(frozen=True)
class LiveTarget:
    """Declarative description of where to find a multica binary.

    Attributes:
        kind: "binary" for a path to a ready executable, "repo" for a path
            to a Go source tree that should be built on demand.
        path: Filesystem path to the binary or repository root.
    """

    kind: str
    path: pathlib.Path

    def resolve(self) -> pathlib.Path:
        """Return the absolute path to the multica executable.

        For "repo" targets, the binary lives at ``path/multica``. For
        "binary" targets, ``path`` is already the executable.

        Raises:
            ValueError: If the kind has no canonical resolution.
        """
        if self.kind == "binary":
            return self.path
        if self.kind == "repo":
            return self.path / "multica"
        msg = f"cannot resolve target of kind {self.kind!r}"
        raise ValueError(msg)


@dataclass(frozen=True)
class Environment:
    """Declarative description of the current live test environment.

    Attributes:
        api_key: Optional Multica API key, if set in the environment.
        workspace: Optional default workspace slug, if set.
        profile: Live suite profile; one of "smoke", "extended".
        extra: Any other ``MULTICA_*`` environment variables.
    """

    api_key: str | None
    workspace: str | None
    profile: str
    extra: dict[str, str]

    @property
    def profile_name(self) -> str:
        """Return a stable, log-safe profile name for diagnostics."""
        return self.profile


def parse_target(spec: str) -> LiveTarget:
    """Parse a target spec like ``binary:/usr/local/bin/multica`` or ``./multica``.

    Args:
        spec: Target spec. If it contains a colon, the part before the colon
            is the kind ("binary" or "repo") and the part after is the path.
            Otherwise the whole spec is treated as a binary path.

    Returns:
        A ``LiveTarget`` with the parsed kind and absolute path.
    """
    if ":" in spec:
        kind, path_str = spec.split(":", 1)
    else:
        kind, path_str = "binary", spec
    return LiveTarget(kind=kind, path=pathlib.Path(path_str))


def parse_environment(env: Mapping[str, str] | None = None) -> Environment:
    """Parse a live environment mapping into a typed ``Environment`` object.

    Args:
        env: Environment mapping; defaults to ``os.environ``.

    Returns:
        Validated ``Environment`` with api_key, workspace, profile and any
        additional ``MULTICA_*`` variables preserved in ``extra``.
    """
    source: dict[str, str] = (
        dict(env) if env is not None else cast("dict[str, str]", dict(os.environ))
    )
    reserved = {"MULTICA_API_KEY", "MULTICA_WORKSPACE", "MULTICA_PROFILE"}
    extra = {
        key: value
        for key, value in source.items()
        if key.startswith("MULTICA_") and key not in reserved
    }
    profile = source.get("MULTICA_PROFILE", "extended")
    return Environment(
        api_key=source.get("MULTICA_API_KEY"),
        workspace=source.get("MULTICA_WORKSPACE"),
        profile=profile,
        extra=extra,
    )


class ResourceAbsentError(Exception):
    """Raised when cleanup finds an already absent resource."""


class SecretString:
    """Wrapper that redacts secret values from repr and str."""

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretString(***)"

    def __str__(self) -> str:
        return "***"


@dataclass(frozen=True, slots=True)
class AgentSandboxSettings:
    """Validated deterministic agent sandbox configuration."""

    agent_mode: str
    inject_cleanup_failure: str | None
    opencode_path: pathlib.Path
    opencode_model: str


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
        return {name: os.environ[name] for name in self.secret_names}

    def to_sandbox_settings(self) -> AgentSandboxSettings:
        return AgentSandboxSettings(
            agent_mode="success",
            inject_cleanup_failure=None,
            opencode_path=self.opencode_path,
            opencode_model=self.model,
        )


def _parse_canary_secret_names(raw: str) -> tuple[str, ...] | None:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    seen: dict[str, None] = dict.fromkeys(parts)
    return tuple(seen) or None


def collect_missing_canary_variables(
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
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
    source = os.environ if environ is None else environ
    missing = collect_missing_canary_variables(source)
    if missing:
        raise LiveSetupError(
            "canary",
            f"canary environment incomplete: missing {', '.join(missing)}",
        )
    opencode_path = pathlib.Path(source[CANARY_ENV_OPENCODE_PATH].strip())
    secret_names = _parse_canary_secret_names(source[CANARY_ENV_SECRET_NAMES])
    assert secret_names is not None
    return OpenCodeCanarySettings(
        opencode_path=opencode_path,
        model=source[CANARY_ENV_MODEL].strip(),
        secret_names=secret_names,
    )


__all__ = [
    "CANARY_COST_CEILING_USD",
    "CANARY_ENV_MODEL",
    "CANARY_ENV_OPENCODE_PATH",
    "CANARY_ENV_SECRET_NAMES",
    "CANARY_REQUIRED_VARIABLES",
    "DEFAULT_TARGET_FILE",
    "AgentSandboxSettings",
    "CliSource",
    "CompatibilityTarget",
    "Environment",
    "LiveSettings",
    "LiveSetupError",
    "LiveTarget",
    "OpenCodeCanarySettings",
    "ResourceAbsentError",
    "SecretString",
    "SuiteProfile",
    "collect_missing_canary_variables",
    "load_compatibility_target",
    "load_live_settings",
    "load_opencode_canary_settings",
    "parse_environment",
    "parse_target",
]

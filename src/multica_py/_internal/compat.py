from __future__ import annotations

import re
import warnings

import msgspec

from multica_py._internal.upstream_contract.models import CliCompatMatrix
from multica_py._internal.upstream_contract.paths import DEFAULT_STATE_PATH
from multica_py.compatibility import CliVersion
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import UnsupportedCliVersionError

COMPATIBILITY_SCHEMA_VERSION = 1

_SEMVER_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")
_WARNED_NEWER = False


class _CliVersionPayload(msgspec.Struct, frozen=True):
    version: str = "0.0.0"
    commit: str = ""
    buildDate: str = ""
    goVersion: str = ""
    os: str = ""
    arch: str = ""


def parse_cli_version(raw_output: str) -> CliVersion | None:
    try:
        data = msgspec.json.decode(
            raw_output.encode("utf-8"),
            type=_CliVersionPayload,
            strict=False,
        )
        return CliVersion(
            version=data.version,
            commit=data.commit,
            build_date=data.buildDate,
            go_version=data.goVersion,
            os=data.os,
            arch=data.arch,
            raw_output=raw_output,
        )
    except (msgspec.DecodeError, msgspec.ValidationError):
        return None


def _parse_semver(version: str) -> tuple[int, int, int] | None:
    match = _SEMVER_PATTERN.match(version)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _bump_patch_version(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return version
    major, minor, patch = (int(part) for part in parts)
    return f"{major}.{minor}.{patch + 1}"


def _load_supported_bounds() -> tuple[str, str]:
    if not DEFAULT_STATE_PATH.exists():
        return "0.0.0", "0.0.0"
    raw: object = msgspec.json.decode(DEFAULT_STATE_PATH.read_bytes())
    if not isinstance(raw, dict):
        return "0.0.0", "0.0.0"
    supported_obj = raw.get("supported")
    if not isinstance(supported_obj, dict):
        return "0.0.0", "0.0.0"
    version_obj = supported_obj.get("version")
    min_version = str(version_obj) if version_obj else "0.0.0"
    return min_version, _bump_patch_version(min_version)


def default_policy(sdk_version: str) -> CliCompatMatrix:
    min_version, max_version = _load_supported_bounds()
    return CliCompatMatrix(
        schema_version=COMPATIBILITY_SCHEMA_VERSION,
        sdk_version=sdk_version,
        min_cli_version=min_version,
        max_cli_version=max_version,
    )


def supported_range_text(policy: CliCompatMatrix) -> str:
    return f"{policy.min_cli_version} <= cli < {policy.max_cli_version}"


def _check_supported_version_text(
    version: str, policy: CompatibilityPolicy
) -> tuple[int, int, int]:
    parsed = _parse_semver(version)
    if parsed is not None:
        return parsed
    message = f"CLI version {version!r} is not a supported semantic version"
    if policy == CompatibilityPolicy.warn:
        warnings.warn(message, stacklevel=2)
        return (0, 0, 0)
    raise UnsupportedCliVersionError(message)


def _warn_newer_untested_once(version: str, max_version: str) -> None:
    global _WARNED_NEWER
    parsed = _parse_semver(version)
    max_parsed = _parse_semver(max_version)
    if parsed is None or max_parsed is None:
        return
    if parsed < max_parsed:
        return
    if _WARNED_NEWER:
        return
    _WARNED_NEWER = True
    message = f"CLI version {version} is newer than the SDK-tested range (< {max_version})"
    warnings.warn(message, UserWarning, stacklevel=2)


def check_version(
    detected: CliVersion,
    policy: CompatibilityPolicy,
    min_version: str | None = None,
    max_version: str | None = None,
) -> None:
    if policy == CompatibilityPolicy.ignore:
        return

    detected_semver = _check_supported_version_text(detected.version, policy)
    min_semver = _parse_semver(min_version) if min_version is not None else None
    max_semver = _parse_semver(max_version) if max_version is not None else None

    if policy == CompatibilityPolicy.warn:
        if min_semver is not None and detected_semver < min_semver:
            warnings.warn(
                f"CLI version {detected.version} is below minimum {min_version}",
                stacklevel=2,
            )
        if max_semver is not None and detected_semver >= max_semver:
            _warn_newer_untested_once(detected.version, max_version or detected.version)
        return

    if policy == CompatibilityPolicy.strict:
        if min_semver is not None and detected_semver < min_semver:
            raise UnsupportedCliVersionError(
                f"CLI version {detected.version} is below minimum {min_version}"
            )
        if max_semver is not None and detected_semver >= max_semver:
            raise UnsupportedCliVersionError(
                f"CLI version {detected.version} exceeds maximum {max_version}"
            )


def check_version_from_config(
    detected: CliVersion | None,
    config: ClientConfig,
    pinned_version: str | None = None,
) -> None:
    if config.compatibility == CompatibilityPolicy.ignore:
        return
    if detected is None:
        message = "Failed to parse CLI version output"
        if config.compatibility == CompatibilityPolicy.warn:
            warnings.warn(message, stacklevel=2)
            return
        raise UnsupportedCliVersionError(message)
    default_min, default_max = _load_supported_bounds()
    min_version = config.min_cli_version or pinned_version or default_min
    max_version = config.max_cli_version or default_max
    check_version(
        detected,
        config.compatibility,
        min_version=min_version,
        max_version=max_version,
    )

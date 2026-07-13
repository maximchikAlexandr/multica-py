from __future__ import annotations

import re
import warnings

import msgspec

from multica_py.compatibility import CliVersion
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import UnsupportedCliVersionError

_SEMVER_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


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
        if max_semver is not None and detected_semver > max_semver:
            warnings.warn(
                f"CLI version {detected.version} exceeds maximum {max_version}",
                stacklevel=2,
            )
        return

    if policy == CompatibilityPolicy.strict:
        if min_semver is not None and detected_semver < min_semver:
            raise UnsupportedCliVersionError(
                f"CLI version {detected.version} is below minimum {min_version}"
            )
        if max_semver is not None and detected_semver > max_semver:
            raise UnsupportedCliVersionError(
                f"CLI version {detected.version} exceeds maximum {max_version}"
            )


def check_version_from_config(
    detected: CliVersion | None,
    config: ClientConfig,
    pinned_version: str = "0.1.0",
) -> None:
    if config.compatibility == CompatibilityPolicy.ignore:
        return
    if detected is None:
        message = "Failed to parse CLI version output"
        if config.compatibility == CompatibilityPolicy.warn:
            warnings.warn(message, stacklevel=2)
            return
        raise UnsupportedCliVersionError(message)
    check_version(
        detected,
        config.compatibility,
        min_version=pinned_version,
        max_version=None,
    )

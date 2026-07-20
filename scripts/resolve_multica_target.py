from __future__ import annotations

import hashlib
import http.client
import json
import os
import pathlib
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import cast

from tests.live.environment import CompatibilityTarget, LiveSetupError, load_compatibility_target

GITHUB_RELEASE_BASE = "https://github.com/multica-ai/multica/releases/download"


@dataclass(frozen=True, slots=True)
class PlatformReleaseSpec:
    """Release asset and checksum field for one platform."""

    asset_suffix: str
    checksum_field: str


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """Compatibility target with a verified CLI executable."""

    target: CompatibilityTarget
    cli_executable: pathlib.Path
    cli_version_actual: str


_PLATFORM_RELEASES: dict[tuple[str, str], PlatformReleaseSpec] = {
    ("linux", "x86_64"): PlatformReleaseSpec("linux-amd64", "cli_release_sha256_linux_amd64"),
    ("linux", "amd64"): PlatformReleaseSpec("linux-amd64", "cli_release_sha256_linux_amd64"),
    ("darwin", "arm64"): PlatformReleaseSpec("darwin-arm64", "cli_release_sha256_darwin_arm64"),
    ("darwin", "x86_64"): PlatformReleaseSpec("darwin-amd64", "cli_release_sha256_darwin_amd64"),
}


def _platform_release_spec() -> PlatformReleaseSpec:
    system = platform.system().lower()
    machine = platform.machine().lower()
    spec = _PLATFORM_RELEASES.get((system, machine))
    if spec is None:
        raise LiveSetupError(
            "target",
            f"unsupported platform for release resolver: {system}/{machine}",
        )
    return spec


def _platform_asset_name(version: str) -> str:
    spec = _platform_release_spec()
    return f"multica-cli-{version}-{spec.asset_suffix}.tar.gz"


def _expected_release_sha256(target: CompatibilityTarget) -> str:
    spec = _platform_release_spec()
    checksum_by_field = {
        "cli_release_sha256_linux_amd64": target.cli_release_sha256_linux_amd64,
        "cli_release_sha256_darwin_arm64": target.cli_release_sha256_darwin_arm64,
        "cli_release_sha256_darwin_amd64": target.cli_release_sha256_darwin_amd64,
    }
    checksum_value = checksum_by_field[spec.checksum_field]
    if not isinstance(checksum_value, str):
        raise LiveSetupError(
            "target", f"{spec.checksum_field} is required for release mode on this platform"
        )
    return checksum_value


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_release_cli(target: CompatibilityTarget, destination: pathlib.Path) -> pathlib.Path:
    version = target.cli_version_expected
    tag = target.upstream_ref
    asset_name = _platform_asset_name(version)
    expected_sha256 = _expected_release_sha256(target)
    url = f"{GITHUB_RELEASE_BASE}/{tag}/{asset_name}"
    archive_path = destination / asset_name
    try:
        raw_response = urllib.request.urlopen(url, timeout=120)
    except urllib.error.URLError as exc:
        raise LiveSetupError("target", f"failed to download CLI release asset: {exc}") from exc
    response = cast("http.client.HTTPResponse", raw_response)
    try:
        archive_path.write_bytes(response.read())
    finally:
        response.close()
    actual_sha256 = _sha256_file(archive_path)
    if actual_sha256 != expected_sha256:
        raise LiveSetupError(
            "target",
            f"CLI release checksum mismatch for {asset_name}: expected {expected_sha256}, got {actual_sha256}",
        )
    extract_dir = destination / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(extract_dir, filter="data")
    candidates = list(extract_dir.rglob("multica"))
    executables = [path for path in candidates if path.is_file()]
    if not executables:
        raise LiveSetupError("target", f"multica executable not found in {asset_name}")
    cli_path = executables[0]
    cli_path.chmod(cli_path.stat().st_mode | 0o111)
    final_path = destination / "multica"
    shutil.copy2(cli_path, final_path)
    final_path.chmod(final_path.stat().st_mode | 0o111)
    return final_path


def resolve_cli_from_upstream(
    upstream_dir: pathlib.Path, destination: pathlib.Path
) -> pathlib.Path:
    """Build the Multica CLI from an upstream checkout.

    Args:
        upstream_dir: Checkout containing Multica source.
        destination: Directory for the built executable.

    Returns:
        Absolute path to the built CLI executable.

    Raises:
        LiveSetupError: If the checkout is invalid or the build fails.
    """
    if not upstream_dir.is_dir():
        raise LiveSetupError("target", f"upstream checkout not found: {upstream_dir}")
    if not (upstream_dir / "go.mod").is_file():
        raise LiveSetupError("target", f"upstream checkout missing go.mod: {upstream_dir}")
    destination.mkdir(parents=True, exist_ok=True)
    cli_path = destination / "multica"
    try:
        completed = subprocess.run(
            ["go", "build", "-o", str(cli_path), "./cmd/multica"],
            cwd=upstream_dir,
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LiveSetupError("target", f"failed to build CLI from upstream source: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise LiveSetupError("target", f"go build failed: {detail}")
    cli_path.chmod(cli_path.stat().st_mode | 0o111)
    return cli_path.resolve()


def read_cli_version(cli_executable: pathlib.Path) -> str:
    """Read the Multica CLI version from a real executable.

    Args:
        cli_executable: Path to the multica binary.

    Returns:
        Semantic version string such as ``0.3.35``.

    Raises:
        LiveSetupError: If version discovery fails.
    """
    try:
        completed = subprocess.run(
            [str(cli_executable), "version", "--output", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LiveSetupError("target", f"failed to run CLI version command: {exc}") from exc
    if completed.returncode != 0:
        raise LiveSetupError(
            "target",
            f"CLI version command failed with exit code {completed.returncode}",
        )
    try:
        payload = cast("dict[str, object]", json.loads(completed.stdout))
    except json.JSONDecodeError as exc:
        raise LiveSetupError("target", "CLI version output is not valid JSON") from exc
    version = payload.get("version")
    if not isinstance(version, str) or not version:
        raise LiveSetupError("target", "CLI version JSON missing version field")
    return version


def verify_cli_version(cli_executable: pathlib.Path, expected: str) -> str:
    """Verify that a CLI executable matches the expected version.

    Args:
        cli_executable: Path to the multica binary.
        expected: Expected semantic version from the target manifest.

    Returns:
        Actual CLI version string.

    Raises:
        LiveSetupError: If the executable is missing or the version mismatches.
    """
    if not cli_executable.is_file() or not os.access(cli_executable, os.X_OK):
        raise LiveSetupError("target", f"CLI executable is not runnable: {cli_executable}")
    actual = read_cli_version(cli_executable)
    if actual != expected:
        raise LiveSetupError(
            "target",
            f"CLI version mismatch: expected {expected!r}, got {actual!r}",
        )
    return actual


def resolve_cli_executable(
    target: CompatibilityTarget,
    settings_cli: pathlib.Path | None,
    *,
    cache_dir: pathlib.Path | None = None,
    upstream_dir: pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve the Multica CLI executable for a compatibility target.

    Args:
        target: Validated compatibility target.
        settings_cli: Optional explicit CLI path from settings.
        cache_dir: Optional directory for downloaded release artifacts.
        upstream_dir: Optional upstream checkout for source-build resolution.

    Returns:
        Absolute path to a verified CLI executable.

    Raises:
        LiveSetupError: If CLI resolution or version verification fails.
    """
    if settings_cli is not None:
        if os.environ.get("MULTICA_LIVE_CLI_SOURCE") == "upstream":
            return settings_cli.resolve()
        verify_cli_version(settings_cli, target.cli_version_expected)
        return settings_cli.resolve()
    if os.environ.get("MULTICA_LIVE_CLI_SOURCE") == "upstream":
        if upstream_dir is None:
            raise LiveSetupError(
                "target", "MULTICA_LIVE_UPSTREAM_DIR is required for upstream CLI build"
            )
        destination = cache_dir or pathlib.Path(tempfile.mkdtemp(prefix="multica-live-cli-"))
        return resolve_cli_from_upstream(upstream_dir, destination)
    if target.cli_source == "local":
        raise LiveSetupError("target", "MULTICA_LIVE_CLI is required for cli_source=local")
    destination = cache_dir or pathlib.Path(tempfile.mkdtemp(prefix="multica-live-cli-"))
    destination.mkdir(parents=True, exist_ok=True)
    cli_path = _download_release_cli(target, destination)
    verify_cli_version(cli_path, target.cli_version_expected)
    return cli_path.resolve()


def resolve_target(
    target_file: pathlib.Path,
    settings_cli: pathlib.Path | None,
    *,
    cache_dir: pathlib.Path | None = None,
    upstream_dir: pathlib.Path | None = None,
) -> ResolvedTarget:
    """Load, resolve, and verify a compatibility target.

    Args:
        target_file: Path to the target manifest.
        settings_cli: Optional explicit CLI path from settings.
        cache_dir: Optional directory for downloaded release artifacts.
        upstream_dir: Optional upstream checkout for source-build resolution.

    Returns:
        Resolved target with verified CLI executable.

    Raises:
        LiveSetupError: If target loading or CLI verification fails.
    """
    target = load_compatibility_target(target_file)
    cli_executable = resolve_cli_executable(
        target,
        settings_cli,
        cache_dir=cache_dir,
        upstream_dir=upstream_dir,
    )
    if os.environ.get("MULTICA_LIVE_CLI_SOURCE") == "upstream":
        actual = read_cli_version(cli_executable)
    else:
        actual = verify_cli_version(cli_executable, target.cli_version_expected)
    return ResolvedTarget(
        target=target,
        cli_executable=cli_executable,
        cli_version_actual=actual,
    )


def build_version_report(resolved: ResolvedTarget) -> dict[str, str]:
    """Build a redaction-safe version report for diagnostics.

    Args:
        resolved: Resolved compatibility target.

    Returns:
        Allowlisted metadata mapping for ``target.json``.
    """
    target = resolved.target
    return {
        "name": target.name,
        "upstream_ref": target.upstream_ref,
        "upstream_commit": target.upstream_commit,
        "backend_image": target.backend_image,
        "backend_tag": target.backend_tag,
        "backend_digest": target.backend_digest,
        "cli_source": target.cli_source,
        "cli_version_expected": target.cli_version_expected,
        "cli_version_actual": resolved.cli_version_actual,
        "verified_at": target.verified_at,
    }


def load_pinned_target(target_file: pathlib.Path) -> CompatibilityTarget:
    """Load the pinned compatibility target manifest."""
    return load_compatibility_target(target_file)


def workflow_backend_digest(target: CompatibilityTarget) -> str:
    """Return the digest CI should pull on Linux runners."""
    if target.backend_digest_linux_amd64:
        return target.backend_digest_linux_amd64
    return target.backend_digest

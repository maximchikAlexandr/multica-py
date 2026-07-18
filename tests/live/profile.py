from __future__ import annotations

import json
import pathlib
import shutil

from tests.live.exceptions import LiveSetupError


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
    real_home = pathlib.Path.home().resolve()
    resolved_home = home_dir.resolve()
    if resolved_home == real_home:
        raise LiveSetupError("profile", "refusing to write profile into the real HOME directory")
    profile_dir = resolved_home / ".multica" / "profiles" / profile_name
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
    if home_dir.resolve() == pathlib.Path.home().resolve():
        raise LiveSetupError("profile", "temp HOME resolved to the real HOME directory")
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

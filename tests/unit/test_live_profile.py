from __future__ import annotations

import json
import os
import pathlib
import stat

import pytest

from tests.live.exceptions import LiveSetupError
from tests.live.profile import (
    ensure_temp_home,
    profile_config_path,
    remove_temp_home,
    validate_not_real_home,
    write_cli_profile,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HOME_BASE = REPO_ROOT / "tests" / "live" / ".live-home"


def test_profile_path_and_exact_json_keys(tmp_path: pathlib.Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    config_path = write_cli_profile(
        home_dir,
        "live-run123",
        server_url="http://127.0.0.1:8080",
        app_url="http://127.0.0.1:8080",
        workspace_id="ws-123",
        token="pat-token",
    )
    assert config_path == profile_config_path(home_dir, "live-run123")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert set(payload) == {"server_url", "app_url", "workspace_id", "token"}
    assert payload["server_url"] == "http://127.0.0.1:8080"


def test_profile_mode_is_0600(tmp_path: pathlib.Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    config_path = write_cli_profile(
        home_dir,
        "live-run123",
        server_url="http://127.0.0.1:8080",
        app_url="http://127.0.0.1:8080",
        workspace_id="ws-123",
        token="pat-token",
    )
    mode = stat.S_IMODE(config_path.stat().st_mode)
    assert mode == 0o600


def test_refuses_real_home(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_home = pathlib.Path.home()
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: real_home))
    with pytest.raises(LiveSetupError, match="real HOME"):
        write_cli_profile(
            real_home,
            "live-run123",
            server_url="http://127.0.0.1:8080",
            app_url="http://127.0.0.1:8080",
            workspace_id="ws-123",
            token="pat-token",
        )


def test_temp_home_lifecycle() -> None:
    run_id = "unit-profile-test"
    home_dir = ensure_temp_home(HOME_BASE, run_id)
    try:
        validate_not_real_home(home_dir)
        assert home_dir.exists()
    finally:
        remove_temp_home(home_dir)
        assert not home_dir.exists()

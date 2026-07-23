from __future__ import annotations

import pathlib

import pytest

from tests.live._live_helpers import skip_if_canary_environment_incomplete
from tools.live_support.environment import (
    CANARY_ENV_MODEL,
    CANARY_ENV_OPENCODE_PATH,
    CANARY_ENV_SECRET_NAMES,
    LiveSetupError,
    collect_missing_canary_variables,
    load_opencode_canary_settings,
)


def _complete_environ(tmp_path: pathlib.Path) -> dict[str, str]:
    opencode = tmp_path / "opencode"
    opencode.write_text("#!/bin/sh\n", encoding="utf-8")
    opencode.chmod(0o755)
    return {
        CANARY_ENV_OPENCODE_PATH: str(opencode.resolve()),
        CANARY_ENV_MODEL: "provider/model",
        CANARY_ENV_SECRET_NAMES: "PROVIDER_API_KEY, OTHER_SECRET",
        "PROVIDER_API_KEY": "provider-secret",
        "OTHER_SECRET": "other-secret",
    }


def test_collect_missing_reports_all_required_variables() -> None:
    missing = collect_missing_canary_variables({})
    assert CANARY_ENV_OPENCODE_PATH in missing
    assert CANARY_ENV_MODEL in missing
    assert CANARY_ENV_SECRET_NAMES in missing


def test_collect_missing_reports_named_secrets(tmp_path: pathlib.Path) -> None:
    opencode = tmp_path / "opencode"
    opencode.write_text("#!/bin/sh\n", encoding="utf-8")
    opencode.chmod(0o755)
    environ = {
        CANARY_ENV_OPENCODE_PATH: str(opencode.resolve()),
        CANARY_ENV_MODEL: "provider/model",
        CANARY_ENV_SECRET_NAMES: "PROVIDER_API_KEY, OTHER_SECRET",
        "PROVIDER_API_KEY": "provider-secret",
    }
    missing = collect_missing_canary_variables(environ)
    assert missing == ("OTHER_SECRET",)


def test_rejects_empty_secret_values(tmp_path: pathlib.Path) -> None:
    opencode = tmp_path / "opencode"
    opencode.write_text("#!/bin/sh\n", encoding="utf-8")
    opencode.chmod(0o755)
    environ = {
        CANARY_ENV_OPENCODE_PATH: str(opencode.resolve()),
        CANARY_ENV_MODEL: "provider/model",
        CANARY_ENV_SECRET_NAMES: "PROVIDER_API_KEY",
        "PROVIDER_API_KEY": "   ",
    }
    assert collect_missing_canary_variables(environ) == ("PROVIDER_API_KEY",)


def test_trims_and_deduplicates_secret_names(tmp_path: pathlib.Path) -> None:
    environ = _complete_environ(tmp_path)
    environ[CANARY_ENV_SECRET_NAMES] = " PROVIDER_API_KEY , PROVIDER_API_KEY , OTHER_SECRET "
    settings = load_opencode_canary_settings(environ)
    assert settings.secret_names == ("PROVIDER_API_KEY", "OTHER_SECRET")


def test_skip_if_canary_environment_incomplete(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        CANARY_ENV_OPENCODE_PATH,
        CANARY_ENV_MODEL,
        CANARY_ENV_SECRET_NAMES,
        "PROVIDER_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(pytest.skip.Exception, match="canary environment incomplete") as exc:
        skip_if_canary_environment_incomplete()
    message = exc.value.msg or ""
    assert CANARY_ENV_OPENCODE_PATH in message
    assert CANARY_ENV_MODEL in message
    assert CANARY_ENV_SECRET_NAMES in message


def test_load_rejects_invalid_opencode_path(tmp_path: pathlib.Path) -> None:
    environ = _complete_environ(tmp_path)
    environ[CANARY_ENV_OPENCODE_PATH] = "relative/opencode"
    with pytest.raises(LiveSetupError, match="canary environment incomplete"):
        load_opencode_canary_settings(environ)


def test_no_infrastructure_startup_on_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(CANARY_ENV_OPENCODE_PATH, raising=False)
    monkeypatch.delenv(CANARY_ENV_MODEL, raising=False)
    monkeypatch.delenv(CANARY_ENV_SECRET_NAMES, raising=False)
    with pytest.raises(pytest.skip.Exception):
        skip_if_canary_environment_incomplete()

from __future__ import annotations

import warnings

from multica_py._internal.compat import check_version_from_config
from multica_py._internal.compat import (
    default_policy,
    supported_range_text,
)
from multica_py.compatibility import CliVersion
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy as _EnumPolicy


def test_cli_version_creation():
    ver = CliVersion(
        version="0.1.0",
        commit="abc1234",
        build_date="2026-01-01",
        go_version="go1.22",
        os="linux",
        arch="amd64",
        raw_output='{"version":"0.1.0"}',
    )
    assert ver.version == "0.1.0"
    assert ver.commit == "abc1234"


def test_compatibility_policy_values():
    assert _EnumPolicy.strict.value == "strict"
    assert _EnumPolicy.warn.value == "warn"
    assert _EnumPolicy.ignore.value == "ignore"


def test_default_policy_uses_supported_state_bounds():
    policy = default_policy("0.1.0")
    assert policy.min_cli_version == "0.4.2"
    assert policy.max_cli_version == "0.4.3"
    assert "0.4.2" in supported_range_text(policy)


def test_check_version_from_config_warns_once_for_newer_cli():
    import multica_py._internal.compat as compat_module

    compat_module._WARNED_NEWER = False
    config = ClientConfig(
        compatibility=_EnumPolicy.warn,
        min_cli_version="0.4.2",
        max_cli_version="0.4.3",
    )
    detected = CliVersion(
        version="0.4.9",
        commit="",
        build_date="",
        go_version="",
        os="",
        arch="",
        raw_output="",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_version_from_config(detected, config)
        check_version_from_config(detected, config)
    assert len(caught) == 1

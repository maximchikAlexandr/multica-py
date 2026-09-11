from __future__ import annotations

import pytest

from multica_py._internal.compat import (
    check_version,
    check_version_from_config,
    parse_cli_version,
)
from multica_py.compatibility import CliVersion
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import UnsupportedCliVersionError


def _make_ver(version: str) -> CliVersion:
    return CliVersion(
        version=version,
        commit="",
        build_date="",
        go_version="",
        os="",
        arch="",
        raw_output="",
    )


def test_strict_policy_rejects_older():
    with pytest.raises(UnsupportedCliVersionError):
        check_version(_make_ver("0.0.9"), CompatibilityPolicy.strict, min_version="0.1.0")


def test_strict_policy_allows_newer():
    check_version(
        _make_ver("0.2.0"), CompatibilityPolicy.strict, min_version="0.1.0", max_version="0.3.0"
    )


def test_strict_policy_rejects_newer():
    with pytest.raises(UnsupportedCliVersionError):
        check_version(_make_ver("0.4.0"), CompatibilityPolicy.strict, max_version="0.3.0")


def test_warn_policy_emits_warning():
    with pytest.warns(UserWarning, match="below minimum"):
        check_version(_make_ver("0.0.9"), CompatibilityPolicy.warn, min_version="0.1.0")


def test_ignore_policy_never_raises():
    check_version(_make_ver("0.0.1"), CompatibilityPolicy.ignore, min_version="0.1.0")


def test_parse_cli_version_maps_current_json_envelope_and_ignores_additive_keys():
    raw = '{"arch":"arm64","commit":"47dc75741","date":"2026-09-02T09:52:29Z","go":"go1.26.7","os":"darwin","version":"0.4.38","extra":true}'
    ver = parse_cli_version(raw)
    assert ver is not None
    assert ver.version == "0.4.38"
    assert ver.commit == "47dc75741"
    assert ver.build_date == "2026-09-02T09:52:29Z"
    assert ver.go_version == "go1.26.7"
    assert ver.os == "darwin"
    assert ver.arch == "arm64"


def test_parse_cli_version_invalid():
    assert parse_cli_version("not json") is None


@pytest.mark.parametrize(
    "raw",
    (
        "{}",
        '{"version":""}',
        '{"version":"not-semver"}',
        '{"version":0}',
        '{"version":null}',
    ),
)
def test_parse_cli_version_rejects_invalid_version_envelopes(raw: str) -> None:
    assert parse_cli_version(raw) is None


def test_check_version_from_config():
    config = ClientConfig(compatibility=CompatibilityPolicy.strict)
    with pytest.raises(UnsupportedCliVersionError):
        check_version_from_config(_make_ver("0.0.1"), config, pinned_version="0.1.0")


def test_semver_comparison_is_numeric_not_lexicographic():
    check_version(_make_ver("0.10.0"), CompatibilityPolicy.strict, min_version="0.2.0")


def test_warn_policy_warns_on_unparseable_detected_version():
    config = ClientConfig(compatibility=CompatibilityPolicy.warn)
    with pytest.warns(UserWarning, match="Failed to parse CLI version output"):
        check_version_from_config(None, config, pinned_version="0.1.0")


def test_strict_policy_rejects_unparseable_detected_version():
    config = ClientConfig(compatibility=CompatibilityPolicy.strict)
    with pytest.raises(UnsupportedCliVersionError, match="Failed to parse CLI version output"):
        check_version_from_config(None, config, pinned_version="0.1.0")

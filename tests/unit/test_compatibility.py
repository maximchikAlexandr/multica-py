from __future__ import annotations

from multica_py.compatibility import CliVersion
from multica_py.enums import CompatibilityPolicy


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
    assert CompatibilityPolicy.strict.value == "strict"
    assert CompatibilityPolicy.warn.value == "warn"
    assert CompatibilityPolicy.ignore.value == "ignore"

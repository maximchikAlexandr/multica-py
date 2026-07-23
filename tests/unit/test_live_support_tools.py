"""Tests for canonical live support helpers in tools/live_support/.

Also keeps the SC-002 mutation patch anchor check that lived in
``tests/unit/test_live_mutation_cases.py`` so the live support test
consolidation does not lose coverage.
"""

from __future__ import annotations

import pathlib

from scripts.run_live_tests import MUTATION_CASES, REPO_ROOT
from tools.live_support.diagnostics import (
    VERIFICATION_CODE,
    is_canary_response,
    redact,
    scan_for_secrets,
)
from tools.live_support.environment import (
    Environment,
    LiveTarget,
    parse_environment,
    parse_target,
)


def test_parse_target_defaults_to_binary_kind() -> None:
    target = parse_target("/usr/local/bin/multica")
    assert target == LiveTarget(kind="binary", path=pathlib.Path("/usr/local/bin/multica"))


def test_parse_target_explicit_kind_and_path() -> None:
    target = parse_target("repo:./multica")
    assert target == LiveTarget(kind="repo", path=pathlib.Path("./multica"))


def test_parse_target_docker_kind() -> None:
    target = parse_target("docker:multica/cli:0.3.10")
    assert target.kind == "docker"
    assert target.path == pathlib.Path("multica/cli:0.3.10")


def test_live_target_resolve_binary() -> None:
    target = LiveTarget(kind="binary", path=pathlib.Path("/opt/multica"))
    assert target.resolve() == pathlib.Path("/opt/multica")


def test_live_target_resolve_repo_appends_multica() -> None:
    target = LiveTarget(kind="repo", path=pathlib.Path("./checkout"))
    assert target.resolve() == pathlib.Path("./checkout/multica")


def test_live_target_resolve_unknown_kind_fails_closed() -> None:
    target = LiveTarget(kind="docker", path=pathlib.Path("x"))
    try:
        target.resolve()
    except ValueError as exc:
        assert "docker" in str(exc)
    else:
        raise AssertionError("expected ValueError for unresolved kind")


def test_parse_environment_extracts_api_key_workspace_profile() -> None:
    env = parse_environment(
        {
            "MULTICA_API_KEY": "secret-1234567890",
            "MULTICA_WORKSPACE": "ws-1",
            "MULTICA_PROFILE": "smoke",
            "MULTICA_RESOLVE_CLI": "1",
            "PATH": "/usr/bin",
        }
    )
    assert env.api_key == "secret-1234567890"
    assert env.workspace == "ws-1"
    assert env.profile == "smoke"
    assert env.extra == {"MULTICA_RESOLVE_CLI": "1"}
    assert env.profile_name == "smoke"


def test_parse_environment_defaults_profile_to_extended() -> None:
    env = parse_environment({"PATH": "/usr/bin"})
    assert env.profile == "extended"
    assert env.api_key is None
    assert env.workspace is None
    assert env.extra == {}


def test_parse_environment_explicit_mapping_does_not_touch_os() -> None:
    env = parse_environment({})
    assert env == Environment(api_key=None, workspace=None, profile="extended", extra={})


def test_redact_strips_api_key_assignment() -> None:
    redacted = redact("config MULTICA_API_KEY=abcd1234abcd1234 tail")
    assert "abcd1234abcd1234" not in redacted
    assert "***" in redacted


def test_redact_strips_authorization_bearer() -> None:
    redacted = redact("Authorization: Bearer abcdefghijklmnopqrst")
    assert "abcdefghijklmnopqrst" not in redacted
    assert "***" in redacted


def test_redact_strips_generic_api_key() -> None:
    redacted = redact('"api_key":"abcdefghij1234567890"')
    assert "abcdefghij1234567890" not in redacted
    assert "***" in redacted


def test_redact_preserves_unrelated_text() -> None:
    text = "no secrets here"
    assert redact(text) == text


def test_scan_for_secrets_detects_api_key() -> None:
    findings = scan_for_secrets("MULTICA_API_KEY=abcdef0123456789")
    assert "api-key" in findings


def test_scan_for_secrets_detects_bearer() -> None:
    findings = scan_for_secrets("Authorization: Bearer abcdefghijklmnopqrstuvwxyz")
    assert "bearer-token" in findings


def test_scan_for_secrets_detects_openai_style_key() -> None:
    findings = scan_for_secrets("sk-abcdefghijklmnopqrstuv")
    assert "openai-key" in findings


def test_scan_for_secrets_returns_empty_for_clean_text() -> None:
    assert scan_for_secrets("nothing to see here") == []


def test_is_canary_response_true_when_verification_code_present() -> None:
    assert is_canary_response(f"output: {VERIFICATION_CODE}\n") is True


def test_is_canary_response_false_when_absent() -> None:
    assert is_canary_response("no canary") is False


def test_verification_code_constant_is_stable() -> None:
    assert VERIFICATION_CODE == "888888"


def test_mutation_case_originals_exist_in_pinned_sources() -> None:
    """Each mutation original fragment must remain present for --mutation-check."""
    for case in MUTATION_CASES:
        source = (REPO_ROOT / case.path).read_text(encoding="utf-8")
        assert case.original in source, f"{case.name}: original fragment missing in {case.path}"

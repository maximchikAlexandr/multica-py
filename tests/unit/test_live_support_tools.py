"""Tests for canonical live support helpers in tools/live_support/.

Also keeps the SC-002 mutation patch anchor check that lived in
``tests/unit/test_live_mutation_cases.py`` so the live support test
consolidation does not lose coverage.
"""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

import msgspec
import pytest

from scripts.run_live_tests import (
    MUTATION_CASES,
    REPO_ROOT,
    UNIT_MUTATION_CASES,
    MutationCase,
    _mutated_context,
    run_mutation_check,
)
from tools.live_support.diagnostics import (
    VERIFICATION_CODE,
    is_canary_response,
    redact,
    scan_for_secrets,
)
from tools.live_support.environment import (
    Environment,
    LiveSettings,
    LiveSetupError,
    LiveTarget,
    categorize_outcome_by_readiness,
    check_opencode_available,
    parse_environment,
    parse_target,
)
from tools.live_support.outcomes import (
    JUnitCounts,
    OutcomeCategory,
    compare_candidate_to_control,
    normalize_message,
    parse_junit,
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


# ---------------------------------------------------------------------------
# JUnit parsing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JunitCase:
    xml: str
    expected: JUnitCounts


JUNIT_CASES = (
    JunitCase(
        '<testsuite name="s" tests="10" failures="2" errors="1" skipped="0"/>',
        JUnitCounts(tests=10, failures=2, errors=1, skipped=0),
    ),
    JunitCase(
        '<testsuite name="s" tests="0" failures="0" errors="0" skipped="0"/>',
        JUnitCounts(tests=0, failures=0, errors=0, skipped=0),
    ),
    JunitCase(
        "<testsuites>"
        '<testsuite name="a" tests="5" failures="1" errors="0" skipped="0"/>'
        '<testsuite name="b" tests="3" failures="0" errors="1" skipped="1"/>'
        "</testsuites>",
        JUnitCounts(tests=8, failures=1, errors=1, skipped=1),
    ),
)


@pytest.mark.parametrize("case", JUNIT_CASES, ids=["single", "empty", "multi-suite"])
def test_parse_junit(tmp_path: pathlib.Path, case: JunitCase) -> None:
    path = tmp_path / "junit.xml"
    path.write_text(case.xml, encoding="utf-8")
    result = parse_junit(path)
    assert result == case.expected


# ---------------------------------------------------------------------------
# Count comparison
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompareCase:
    control: JUnitCounts
    candidate: JUnitCounts
    expected: bool


COMPARE_CASES = (
    CompareCase(
        JUnitCounts(tests=10, failures=0, errors=0, skipped=0),
        JUnitCounts(tests=10, failures=0, errors=0, skipped=0),
        True,
    ),
    CompareCase(
        JUnitCounts(tests=10, failures=2, errors=1, skipped=0),
        JUnitCounts(tests=10, failures=3, errors=1, skipped=0),
        False,
    ),
    CompareCase(
        JUnitCounts(tests=10, failures=2, errors=1, skipped=0),
        JUnitCounts(tests=10, failures=1, errors=0, skipped=0),
        True,
    ),
    CompareCase(
        JUnitCounts(tests=10, failures=0, errors=1, skipped=0),
        JUnitCounts(tests=10, failures=0, errors=2, skipped=0),
        False,
    ),
)


@pytest.mark.parametrize(
    "case", COMPARE_CASES, ids=["no-change", "more-failures", "fewer-failures", "more-errors"]
)
def test_compare_candidate_to_control(case: CompareCase) -> None:
    assert compare_candidate_to_control(case.control, case.candidate) == case.expected


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalizeCase:
    input: str
    expected_substring: str


NORMALIZE_CASES = (
    NormalizeCase("error at /tmp/foo/bar", "<path>"),
    NormalizeCase("finished in 1.234s", "<duration>"),
    NormalizeCase("at 2024-01-15T10:30:00", "<timestamp>"),
    NormalizeCase("api_key=abcdef1234567890abcdef1234567890", "***"),
    NormalizeCase("plain text no redaction", "plain text no redaction"),
)


@pytest.mark.parametrize(
    "case", NORMALIZE_CASES, ids=["path", "duration", "timestamp", "secret", "plain"]
)
def test_normalize_message(case: NormalizeCase) -> None:
    result = normalize_message(case.input)
    assert case.expected_substring in result
    if case.expected_substring == case.input:
        assert result == case.input


# ---------------------------------------------------------------------------
# categorize_outcome_by_readiness
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadinessCase:
    cli: str | None
    resolve: bool
    url: str | None
    expected: OutcomeCategory


READINESS_CASES = (
    ReadinessCase(None, True, "http://127.0.0.1:8080", OutcomeCategory.passed),
    ReadinessCase("/bin/multica", False, "http://127.0.0.1:8080", OutcomeCategory.passed),
    ReadinessCase(None, False, "http://127.0.0.1:8080", OutcomeCategory.unrunnable),
    ReadinessCase(None, True, None, OutcomeCategory.unrunnable),
)


@pytest.mark.parametrize(
    "case",
    READINESS_CASES,
    ids=["cli-resolved", "cli-provided", "no-cli", "no-url"],
)
def test_categorize_outcome_by_readiness(case: ReadinessCase) -> None:
    settings = LiveSettings(
        target_file=pathlib.Path("target.toml"),
        cli_executable=pathlib.Path(case.cli) if case.cli else None,
        resolve_cli=case.resolve,
        upstream_dir=None,
        artifact_dir=pathlib.Path("/tmp/artifacts"),
        suite_profile="smoke",
        existing_url=case.url,
        keep_env=False,
        ready_timeout_seconds=120.0,
    )
    result = categorize_outcome_by_readiness(settings, OutcomeCategory.passed)
    assert result == case.expected


# ---------------------------------------------------------------------------
# Outcome struct construction
# ---------------------------------------------------------------------------


def test_check_opencode_available_present(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    original = shutil.which

    def _mock_which(name: str) -> str | None:
        return "/usr/local/bin/opencode" if name == "opencode" else original(name)

    monkeypatch.setattr(shutil, "which", _mock_which)
    assert check_opencode_available() == 1


def test_check_opencode_available_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    def _mock_which(name: str) -> str | None:
        return None

    monkeypatch.setattr(shutil, "which", _mock_which)
    with pytest.raises(LiveSetupError, match="opencode"):
        check_opencode_available()


# ---------------------------------------------------------------------------
# Mutation infrastructure tests (T049)
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _noop_context(*args: object, **kwargs: object) -> Iterator[None]:
    yield


def test_mutation_clean_control(tmp_path: pathlib.Path) -> None:
    f = tmp_path / "source.py"
    f.write_text("hello world")
    with _mutated_context(f, "hello", "goodbye"):
        assert f.read_text() == "goodbye world"
    assert f.read_text() == "hello world"


def test_mutation_wrong_node(tmp_path: pathlib.Path) -> None:
    f = tmp_path / "source.py"
    f.write_text("no anchor here")
    with (
        pytest.raises(SystemExit, match="mutation anchor not found"),
        _mutated_context(f, "missing", "replacement"),
    ):
        pass


@pytest.mark.parametrize(
    "exit_code,expected_killed",
    [
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (0, False),
    ],
)
def test_mutation_pytest_exit_code(
    exit_code: int,
    expected_killed: bool,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    def _mock(pytest_args: list[str]) -> int:
        for i, a in enumerate(pytest_args):
            if a == "--junitxml" and i + 1 < len(pytest_args):
                pathlib.Path(pytest_args[i + 1]).write_text(
                    '<testsuite name="s" tests="1" failures="0" errors="0" skipped="0"/>'
                )
        return exit_code

    monkeypatch.setattr("scripts.run_live_tests._run_pytest", _mock)
    monkeypatch.setattr("scripts.run_live_tests._mutated_context", _noop_context)
    results_file = tmp_path / "results.json"
    args = argparse.Namespace(
        mutation_check=True,
        resolve_cli=False,
        mutation_scope="unit",
        mutation_results=results_file,
    )
    result = run_mutation_check(args)
    if expected_killed:
        assert result == 0
    else:
        assert result == 1


def test_mutation_missing_junit(tmp_path: pathlib.Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_junit(tmp_path / "nonexistent.xml")


def test_mutation_survivor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    def _mock(pytest_args: list[str]) -> int:
        for i, a in enumerate(pytest_args):
            if a == "--junitxml" and i + 1 < len(pytest_args):
                pathlib.Path(pytest_args[i + 1]).write_text(
                    '<testsuite name="s" tests="1" failures="0" errors="0" skipped="0"/>'
                )
        return 0

    monkeypatch.setattr("scripts.run_live_tests._run_pytest", _mock)
    monkeypatch.setattr("scripts.run_live_tests._mutated_context", _noop_context)
    results_file = tmp_path / "results.json"
    args = argparse.Namespace(
        mutation_check=True,
        resolve_cli=False,
        mutation_scope="unit",
        mutation_results=results_file,
    )
    result = run_mutation_check(args)
    assert result == 1
    assert results_file.exists()
    raw = msgspec.json.decode(results_file.read_bytes())
    assert all(not r["killed"] for r in raw)


@pytest.mark.parametrize(
    "cases,label",
    [(MUTATION_CASES, "pinned"), (UNIT_MUTATION_CASES, "unit")],
    ids=["pinned", "unit"],
)
def test_mutation_cases_anchors_exist(cases: tuple[MutationCase, ...], label: str) -> None:
    for case in cases:
        source = (REPO_ROOT / case.path).read_text(encoding="utf-8")
        assert case.original in source, f"{case.name}: original fragment missing in {case.path}"

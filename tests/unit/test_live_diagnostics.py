from __future__ import annotations

import pathlib

import pytest

from scripts.scan_live_artifacts import scan_text_content
from tests.live.diagnostics import DiagnosticCollector, truncate_log


def test_redaction_positive_and_negative(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("pat-secret-value")
    redacted = collector.redact("prefix pat-secret-value suffix")
    assert "pat-secret-value" not in redacted
    assert "***" in redacted
    assert collector.scan_text("nothing sensitive") == 0
    assert not collector.has_secret_leak("nothing sensitive")


def test_log_truncation_marks_start_and_end() -> None:
    text = "a" * 300000
    truncated = truncate_log(text, limit=100)
    assert "... [truncated] ..." in truncated
    assert len(truncated.encode("utf-8")) <= 100 + 32


def test_primary_and_cleanup_failures_are_separate(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.record_failure(stage="test", exc_type="AssertionError", message="primary")
    collector.record_cleanup({"failures": [{"key": "label", "message": "cleanup failed"}]})
    assert collector.primary_failure is not None
    assert collector.cleanup_failure is not None
    assert collector.primary_failure["message"] == "primary"
    cleanup_failure = collector.cleanup_failure
    assert cleanup_failure is not None
    failures = cleanup_failure.get("failures")
    assert isinstance(failures, list) and failures
    first_failure = failures[0]
    assert isinstance(first_failure, dict)
    assert first_failure["key"] == "label"


def test_write_json_redacts_before_persisting(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("jwt-secret")
    collector.write_json("target.json", {"message": "jwt-secret leaked"})
    content = (tmp_path / "target.json").read_text(encoding="utf-8")
    assert "jwt-secret" not in content
    assert collector.scan_text(content) == 0
    assert not collector.has_secret_leak(content)


def test_write_text_redacts_before_persisting(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("jwt-secret")
    collector.write_text("failure.json", '{"message":"jwt-secret leaked"}')
    content = (tmp_path / "failure.json").read_text(encoding="utf-8")
    assert "jwt-secret" not in content
    assert collector.scan_text(content) == 0
    assert not collector.has_secret_leak(content)


def test_scan_text_reports_leak_count_without_returning_secrets(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("pat-secret-value")
    assert collector.scan_text("prefix pat-secret-value suffix") == 1
    assert collector.has_secret_leak("prefix pat-secret-value suffix")


def test_assert_no_secret_leak_raises_without_echoing_secret(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("pat-secret-value")
    with pytest.raises(AssertionError, match="registered secret value leaked"):
        collector.assert_no_secret_leak("pat-secret-value")


def test_rejects_path_traversal_filenames(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    with pytest.raises(ValueError, match="invalid artifact filename"):
        collector.write_text("../escape.txt", "x")
    with pytest.raises(ValueError, match="invalid artifact filename"):
        collector.write_text("nested/escape.txt", "x")


def test_redacts_provider_api_key_and_canary_secret(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("sk-provider-key-12345")
    redacted = collector.redact("Authorization: sk-provider-key-12345")
    assert "sk-provider-key-12345" not in redacted
    assert "***" in redacted


def test_redacts_jwt_and_pat_tokens(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
    collector.register_secret(jwt)
    collector.register_secret("mpat_live_token_value")
    payload = f'{{"token":"mpat_live_token_value","jwt":"{jwt}"}}'
    redacted = collector.redact(payload)
    assert jwt not in redacted
    assert "mpat_live_token_value" not in redacted


def test_scan_text_detects_database_password_and_bearer_token() -> None:
    findings = scan_text_content(
        "POSTGRES_PASSWORD=super-secret-db\nAuthorization: Bearer live-bearer-token",
        "compose.env",
    )
    assert any("POSTGRES_PASSWORD" in item for item in findings)
    assert any("bearer token" in item for item in findings)


def test_scan_text_detects_unredacted_token_field() -> None:
    findings = scan_text_content('{"token":"actual-live-token"}', "profile.json")
    assert any("token field not redacted" in item for item in findings)


def test_artifact_dir_scan_flags_configured_canary_secret(tmp_path: pathlib.Path) -> None:
    collector = DiagnosticCollector(tmp_path, "run1")
    collector.register_secret("canary-provider-secret")
    (tmp_path / "leak.txt").write_text("provider=canary-provider-secret", encoding="utf-8")
    assert collector.scan_artifact_dir() == 1
    with pytest.raises(AssertionError, match="registered secret value leaked"):
        collector.assert_no_secret_leak()

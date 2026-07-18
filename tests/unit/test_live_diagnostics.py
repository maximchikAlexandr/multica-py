from __future__ import annotations

import pathlib

import pytest

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
    assert collector.cleanup_failure["failures"][0]["key"] == "label"


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

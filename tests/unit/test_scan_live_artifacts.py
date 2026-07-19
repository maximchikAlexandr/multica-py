from __future__ import annotations

import json
import pathlib

from scripts.scan_live_artifacts import (
    scan_artifact_directory,
    scan_extra_paths,
    scan_live_artifacts,
)


def test_scan_fails_on_unredacted_env_values(tmp_path: pathlib.Path) -> None:
    artifact_dir = tmp_path / "run-1"
    artifact_dir.mkdir()
    (artifact_dir / "failure.json").write_text('JWT_SECRET="real-secret"\n', encoding="utf-8")
    findings = scan_artifact_directory(artifact_dir)
    assert findings


def test_scan_passes_on_redacted_values(tmp_path: pathlib.Path) -> None:
    artifact_dir = tmp_path / "run-1"
    artifact_dir.mkdir()
    (artifact_dir / "failure.json").write_text("JWT_SECRET=***\n", encoding="utf-8")
    (artifact_dir / "secret-scan.json").write_text(
        json.dumps({"finding_count": 0, "registered_findings": []}),
        encoding="utf-8",
    )
    assert scan_artifact_directory(artifact_dir) == []


def test_scan_fails_on_token_substring_bypass(tmp_path: pathlib.Path) -> None:
    artifact_dir = tmp_path / "run-1"
    artifact_dir.mkdir()
    (artifact_dir / "failure.json").write_text('"token":"***real"\n', encoding="utf-8")
    findings = scan_artifact_directory(artifact_dir)
    assert any("token field not redacted" in item for item in findings)


def test_scan_fails_on_bearer_substring_bypass(tmp_path: pathlib.Path) -> None:
    artifact_dir = tmp_path / "run-1"
    artifact_dir.mkdir()
    (artifact_dir / "failure.json").write_text("Authorization: Bearer ***abc\n", encoding="utf-8")
    findings = scan_artifact_directory(artifact_dir)
    assert any("bearer token not redacted" in item for item in findings)


def test_scan_fails_on_verification_code_leak(tmp_path: pathlib.Path) -> None:
    artifact_dir = tmp_path / "run-1"
    artifact_dir.mkdir()
    (artifact_dir / "failure.json").write_text('"code":"888888"\n', encoding="utf-8")
    findings = scan_artifact_directory(artifact_dir)
    assert any("verification code leaked" in item for item in findings)


def test_scan_extra_paths_detects_leaks(tmp_path: pathlib.Path) -> None:
    junit_path = tmp_path / "junit.xml"
    junit_path.write_text('JWT_SECRET="real-secret"\n', encoding="utf-8")
    findings = scan_extra_paths([junit_path])
    assert any("JWT_SECRET leaked" in item for item in findings)


def test_scan_live_artifacts_includes_extra_paths(tmp_path: pathlib.Path) -> None:
    artifact_dir = tmp_path / "run-1"
    artifact_dir.mkdir()
    (artifact_dir / "secret-scan.json").write_text(
        json.dumps({"finding_count": 0, "registered_findings": []}),
        encoding="utf-8",
    )
    junit_path = tmp_path / "junit.xml"
    junit_path.write_text('POSTGRES_PASSWORD="leaked"\n', encoding="utf-8")
    findings = scan_live_artifacts(artifact_dir, [junit_path])
    assert any("POSTGRES_PASSWORD leaked" in item for item in findings)

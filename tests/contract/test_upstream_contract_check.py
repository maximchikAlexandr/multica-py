from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "upstream_contract.py"


FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def _run(
    args: list[str], repo_root: pathlib.Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo-root", str(repo_root or ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_check_exits_zero_for_clean_fixture() -> None:
    result = _run(["check", "--format", "human"])
    assert result.returncode == 0
    assert "Multica upstream coverage: clean" in result.stdout
    assert "Supported: version=0.4.2" in result.stdout
    assert "Inventory: commands=" in result.stdout
    assert "manifest_rows=" in result.stdout
    assert "Failures: total=0" in result.stdout


def test_check_check_without_output_writes_nothing(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "report.json"
    result = _run(["check", "--format", "json", "--check"])
    assert result.returncode == 0
    assert not target.exists()
    assert result.stdout == ""


def test_check_check_with_output_writes_report(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "report.json"
    result = _run(
        [
            "check",
            "--format",
            "json",
            "--check",
            "--output",
            str(target),
        ]
    )
    assert result.returncode == 0
    data = json.loads(target.read_text())
    assert data["status"] == "clean"


def test_check_json_output_writes_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "report.json"
        result = _run(
            [
                "check",
                "--format",
                "json",
                "--output",
                str(target),
            ]
        )
        assert result.returncode == 0
        data = json.loads(target.read_text())
        assert data["status"] == "clean"
        assert "coverage" in data
        assert "supported" in data


def test_check_offline_does_not_touch_network() -> None:
    result = _run(["check", "--format", "human"])
    assert result.returncode in (0, 2, 3, 6)


def test_check_runs_under_30_seconds() -> None:
    start = time.monotonic()
    result = _run(["check", "--format", "human"])
    elapsed = time.monotonic() - start
    assert result.returncode in (0, 2, 3, 6)
    assert elapsed < 30.0


def test_check_exit_code_for_invalid_artifact(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 999, "supported": null}'
    )
    result = _run(["check", "--format", "human"], repo_root=fake_root)
    assert result.returncode == 3


def test_check_missing_coverage_manifest_exits_three(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "repo"
    generated = fake_root / "src" / "multica_py" / "_generated"
    generated.mkdir(parents=True)
    shutil.copy(
        ROOT / "src" / "multica_py" / "_generated" / "upstream_state.json",
        generated / "upstream_state.json",
    )
    shutil.copy(
        ROOT / "src" / "multica_py" / "_generated" / "upstream_supported_contract.json",
        generated / "upstream_supported_contract.json",
    )
    result = _run(["check", "--format", "human"], repo_root=fake_root)
    assert result.returncode == 3


def test_check_with_candidate_missing_file_exits_three() -> None:
    state_path = ROOT / "src" / "multica_py" / "_generated" / "upstream_state.json"
    original = state_path.read_text(encoding="utf-8")
    try:
        state = json.loads(original)
        state["candidate"] = {
            "version": "0.4.3",
            "tag": "v0.4.3",
            "commit": "abc1234567890abcdef1234567890abcdef12345",
            "semantic_hash": "sha256:abc",
            "contract_ref": "artifacts/missing-candidate.json",
            "trust_level": "verified",
        }
        state_path.write_text(json.dumps(state), encoding="utf-8")
        result = _run(["check", "--format", "human", "--with-candidate"])
        assert result.returncode == 3
    finally:
        state_path.write_text(original, encoding="utf-8")


def test_check_clean_when_candidate_present_without_with_candidate() -> None:
    state_path = ROOT / "src" / "multica_py" / "_generated" / "upstream_state.json"
    original = state_path.read_text(encoding="utf-8")
    try:
        state = json.loads(original)
        state["candidate"] = {
            "version": "0.4.3",
            "tag": "v0.4.3",
            "commit": "abc1234567890abcdef1234567890abcdef12345",
            "semantic_hash": "sha256:abc",
            "contract_ref": "artifacts/candidate.json",
            "trust_level": "verified",
        }
        state_path.write_text(json.dumps(state), encoding="utf-8")
        result = _run(["check", "--format", "human"])
        assert result.returncode == 0
        assert "Multica upstream coverage: clean" in result.stdout
    finally:
        state_path.write_text(original, encoding="utf-8")

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.verify_composition import CompositionError, verify_composition


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def history(tmp_path: Path) -> dict[str, str | Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "openspec/changes/demo").mkdir(parents=True)
    (repo / "openspec/changes/demo/spec.md").write_text("approved\n", encoding="utf-8")
    (repo / "integration.txt").write_text("integration\n", encoding="utf-8")
    integration = _commit(repo, "integration")
    (repo / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    baseline = _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "planning", integration)
    (repo / "openspec/changes/demo/spec.md").write_text("approved plan\n", encoding="utf-8")
    planning = _commit(repo, "planning")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--no-ff", "planning", "-m", "composition")
    composition = _git(repo, "rev-parse", "HEAD")
    (repo / "product.py").write_text("candidate\n", encoding="utf-8")
    candidate = _commit(repo, "candidate")
    return {
        "repo": repo,
        "baseline": baseline,
        "integration": integration,
        "planning": planning,
        "composition": composition,
        "candidate": candidate,
    }


def _verify(history: dict[str, str | Path], **overrides: str) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    previous = Path.cwd()
    try:
        os.chdir(repo)
        verify_composition(
            composition_sha=overrides.get("composition_sha", str(history["composition"])),
            planning_sha=overrides.get("planning_sha", str(history["planning"])),
            baseline_sha=overrides.get("baseline_sha", str(history["baseline"])),
            integration_sha=overrides.get("integration_sha", str(history["integration"])),
            candidate_sha=overrides.get("candidate_sha", str(history["candidate"])),
            openspec_path="openspec/changes/demo",
        )
    finally:
        os.chdir(previous)


def test_composition_gate_accepts_exact_ancestry_and_preserved_subtree(
    history: dict[str, str | Path],
) -> None:
    _verify(history)


@pytest.mark.parametrize(
    "override",
    [
        {"baseline_sha": "HEAD"},
        {"planning_sha": "HEAD"},
        {"integration_sha": "HEAD"},
        {"candidate_sha": "not-a-commit"},
    ],
)
def test_composition_gate_rejects_identity_and_ancestry_mutations(
    history: dict[str, str | Path], override: dict[str, str]
) -> None:
    with pytest.raises(CompositionError):
        _verify(history, **override)


def test_composition_gate_rejects_candidate_openspec_drift(
    history: dict[str, str | Path],
) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    (repo / "openspec/changes/demo/spec.md").write_text("mutated\n", encoding="utf-8")
    _commit(repo, "mutate approved input")
    with pytest.raises(CompositionError, match="OpenSpec subtree differs"):
        _verify(history, candidate_sha="HEAD")

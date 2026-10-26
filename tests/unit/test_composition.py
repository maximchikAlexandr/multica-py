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


def _merge(repo: Path, branch: str, message: str) -> None:
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "merge",
        "--no-ff",
        branch,
        "-m",
        message,
    )


@pytest.fixture
def history(tmp_path: Path) -> dict[str, str | Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "openspec/changes/demo").mkdir(parents=True)
    (repo / "openspec/changes/demo/spec.md").write_text("approved\n", encoding="utf-8")
    (repo / "integration.txt").write_text("integration\n", encoding="utf-8")
    prior_integration = _commit(repo, "prior integration")
    (repo / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    baseline = _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "planning", prior_integration)
    (repo / "openspec/changes/demo/spec.md").write_text("approved plan\n", encoding="utf-8")
    composition_planning = _commit(repo, "composition planning")
    _git(repo, "checkout", "main")
    _merge(repo, "planning", "composition")
    composition = _git(repo, "rev-parse", "HEAD")

    (repo / "integration.txt").write_text("accepted integration\n", encoding="utf-8")
    integration = _commit(repo, "accepted integration")
    _git(repo, "checkout", "-b", "verified-planning", integration)
    (repo / "openspec/changes/demo/spec.md").write_text("approved revised plan\n", encoding="utf-8")
    verified_planning = _commit(repo, "verified planning")
    _git(repo, "checkout", "main")
    _merge(repo, "verified-planning", "incorporate verified planning")
    (repo / "product.py").write_text("candidate\n", encoding="utf-8")
    candidate = _commit(repo, "candidate")
    return {
        "repo": repo,
        "baseline": baseline,
        "integration": integration,
        "composition_planning": composition_planning,
        "verified_planning": verified_planning,
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
            composition_planning_sha=overrides.get(
                "composition_planning_sha", str(history["composition_planning"])
            ),
            verified_planning_sha=overrides.get(
                "verified_planning_sha", str(history["verified_planning"])
            ),
            baseline_sha=overrides.get("baseline_sha", str(history["baseline"])),
            integration_sha=overrides.get("integration_sha", str(history["integration"])),
            candidate_sha=overrides.get("candidate_sha", str(history["candidate"])),
            openspec_path="openspec/changes/demo",
            accepted_shas=(overrides.get("accepted_sha", str(history["integration"])),),
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
        {"composition_planning_sha": "HEAD"},
        {"integration_sha": "HEAD"},
        {"accepted_sha": "not-a-commit"},
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


def test_composition_gate_uses_new_planning_sha_for_final_equality(
    history: dict[str, str | Path],
) -> None:
    assert history["composition_planning"] != history["verified_planning"]
    _verify(history)

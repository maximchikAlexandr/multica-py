from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.verify_composition import (
    CompositionError,
    _expected_synced_specs,
    _merged_spec_blocks,
    _task_completion_preserves_text,
    main,
    verify_composition,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _closeout(history: dict[str, str | Path], *, complete: bool = True) -> str:
    repo = history["repo"]
    assert isinstance(repo, Path)
    tasks = repo / "openspec/changes/demo/tasks.md"
    tasks.write_text(
        "## Tasks\n\n- [x] 1. First task\n- [x] 2. Second task\n"
        if complete
        else "## Tasks\n\n- [x] 1. First task\n- [ ] 2. Second task\n",
        encoding="utf-8",
    )
    source_spec = repo / "openspec/changes/demo/specs/sdk-surface/spec.md"
    approved_spec = source_spec.read_text(encoding="utf-8").split("## ADDED Requirements\n\n", 1)[1]
    main_spec = repo / "openspec/specs/sdk-surface/spec.md"
    current_main = main_spec.read_text(encoding="utf-8").rstrip()
    main_spec.write_text(current_main + "\n\n" + approved_spec, encoding="utf-8")
    archive = repo / "openspec/changes/archive/2026-10-26-demo"
    archive.parent.mkdir(parents=True)
    (repo / "openspec/changes/demo").rename(archive)
    return _commit(repo, "archive verified change")


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
    (repo / "openspec/changes/demo/tasks.md").write_text(
        "## Tasks\n\n- [ ] 1. First task\n- [ ] 2. Second task\n", encoding="utf-8"
    )
    (repo / "openspec/changes/demo/design.md").write_text("Approved design.\n", encoding="utf-8")
    (repo / "openspec/changes/demo/specs/sdk-surface").mkdir(parents=True)
    (repo / "openspec/changes/demo/specs/sdk-surface/spec.md").write_text(
        "## ADDED Requirements\n\n### Requirement: Fixture behavior\n\n"
        "The fixture SHALL preserve its behavior.\n\n"
        "#### Scenario: Requirements are synchronized\n\n"
        "- **WHEN** closeout runs\n- **THEN** the approved requirement remains\n",
        encoding="utf-8",
    )
    (repo / "openspec/specs/sdk-surface").mkdir(parents=True)
    (repo / "openspec/specs/sdk-surface/spec.md").write_text(
        "# sdk-surface Specification\n\n## Purpose\n\nDraft purpose.\n\n"
        "## Requirements\n\n### Requirement: Existing behavior\n\n"
        "Existing requirements remain.\n",
        encoding="utf-8",
    )
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
            openspec_path=overrides.get("openspec_path", "openspec/changes/demo"),
            accepted_shas=(overrides.get("accepted_sha", str(history["integration"])),),
        )
    finally:
        os.chdir(previous)


@dataclass(frozen=True)
class _CompositionMutationCase:
    id: str
    overrides: tuple[tuple[str, str], ...]


_COMPOSITION_MUTATION_CASES = (
    _CompositionMutationCase("override0", (("baseline_sha", "HEAD"),)),
    _CompositionMutationCase("override1", (("composition_planning_sha", "HEAD"),)),
    _CompositionMutationCase("override2", (("integration_sha", "HEAD"),)),
    _CompositionMutationCase("override3", (("accepted_sha", "not-a-commit"),)),
    _CompositionMutationCase("override4", (("candidate_sha", "not-a-commit"),)),
)


def test_composition_gate_accepts_exact_ancestry_and_preserved_subtree(
    history: dict[str, str | Path],
) -> None:
    _verify(history)


@pytest.mark.parametrize("case", _COMPOSITION_MUTATION_CASES, ids=lambda case: case.id)
def test_composition_gate_rejects_identity_and_ancestry_mutations(
    history: dict[str, str | Path], case: _CompositionMutationCase
) -> None:
    with pytest.raises(CompositionError):
        _verify(history, **dict(case.overrides))


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


def test_composition_gate_rejects_candidate_sha_before_final_head(
    history: dict[str, str | Path],
) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    (repo / "product.py").write_text("final head\n", encoding="utf-8")
    _commit(repo, "advance final candidate")
    with pytest.raises(CompositionError, match="final checkout HEAD"):
        _verify(history, candidate_sha=str(history["candidate"]))


def _cli_args(
    history: dict[str, str | Path],
    candidate_sha: str,
    openspec_path: str = "openspec/changes/demo",
) -> list[str]:
    return [
        "--composition-sha",
        str(history["composition"]),
        "--composition-planning-sha",
        str(history["composition_planning"]),
        "--verified-planning-sha",
        str(history["verified_planning"]),
        "--baseline-sha",
        str(history["baseline"]),
        "--integration-sha",
        str(history["integration"]),
        "--accepted-sha",
        str(history["integration"]),
        "--candidate-sha",
        candidate_sha,
        "--openspec-path",
        openspec_path,
    ]


def _run_cli(
    history: dict[str, str | Path],
    candidate_sha: str,
    openspec_path: str = "openspec/changes/demo",
) -> subprocess.CompletedProcess[str]:
    repo = history["repo"]
    assert isinstance(repo, Path)
    verifier = Path(__file__).resolve().parents[2] / "scripts/verify_composition.py"
    args = [sys.executable, str(verifier), *_cli_args(history, candidate_sha, openspec_path)]
    return subprocess.run(args, cwd=repo, check=False, capture_output=True, text=True)


def _run_main(
    history: dict[str, str | Path],
    candidate_sha: str,
    openspec_path: str = "openspec/changes/demo",
) -> int:
    repo = history["repo"]
    assert isinstance(repo, Path)
    previous = Path.cwd()
    try:
        os.chdir(repo)
        return main(_cli_args(history, candidate_sha, openspec_path))
    finally:
        os.chdir(previous)


@dataclass(frozen=True)
class _CloseoutMutationCase:
    id: str
    mutate: Callable[[dict[str, str | Path]], None]
    expected_error: str


def _tamper_archive(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/changes/archive/2026-10-26-demo/design.md"
    path.write_text("Tampered design.\n", encoding="utf-8")
    _commit(repo, "tamper archived design")


def _leave_tasks_incomplete(history: dict[str, str | Path]) -> None:
    _closeout(history, complete=False)


def _change_requirement(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/changes/archive/2026-10-26-demo/design.md"
    path.write_text("Unauthorized design drift.\n", encoding="utf-8")
    _commit(repo, "change approved archived design")


def _drop_existing_main_requirements(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/specs/sdk-surface/spec.md"
    path.write_text("# sdk-surface Specification\n", encoding="utf-8")
    _commit(repo, "remove existing main spec requirements")


def _omit_synced_change_requirements(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/specs/sdk-surface/spec.md"
    path.write_text(
        "# sdk-surface Specification\n\n## Requirements\n\n### Requirement: Existing behavior\n\n"
        "Existing requirements remain.\n",
        encoding="utf-8",
    )
    _commit(repo, "omit approved change requirements from main spec")


def _add_archived_file(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/changes/archive/2026-10-26-demo/extra.md"
    path.write_text("unapproved file\n", encoding="utf-8")
    _commit(repo, "add unapproved archive file")


def _use_wrong_archive_name(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    (repo / "openspec/changes/archive/2026-10-26-demo").rename(
        repo / "openspec/changes/archive/2026-10-26-other"
    )
    _commit(repo, "move approved artifacts to the wrong archive")


def _add_second_archive(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    extra = repo / "openspec/changes/archive/2026-10-27-demo"
    extra.mkdir()
    (extra / "proposal.md").write_text("duplicate\n", encoding="utf-8")
    _commit(repo, "add a second archive")


def _keep_active_and_archived_trees(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    archive = repo / "openspec/changes/archive/2026-10-26-demo"
    active = repo / "openspec/changes/demo"
    active.mkdir(parents=True)
    for path in archive.rglob("*"):
        if path.is_file():
            target = active / path.relative_to(archive)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    _commit(repo, "keep active and archived trees")


def _remove_change_without_archiving(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    shutil.rmtree(repo / "openspec/changes/demo")
    _commit(repo, "remove approved change")


def _remove_synced_main_spec(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    (repo / "openspec/specs/sdk-surface/spec.md").unlink()
    _commit(repo, "remove synced main spec")


def _add_unrelated_openspec_file(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/specs/unrelated/spec.md"
    path.parent.mkdir(parents=True)
    path.write_text("unrelated\n", encoding="utf-8")
    _commit(repo, "add unrelated spec")


def _change_task_text(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/changes/archive/2026-10-26-demo/tasks.md"
    path.write_text("## Tasks\n\n- [x] 1. Changed task\n- [x] 2. Second task\n", encoding="utf-8")
    _commit(repo, "change archived task text")


def _add_unapproved_spec_requirement(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/specs/sdk-surface/spec.md"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            "\n\n### Requirement: Unapproved behavior\n\n"
            "The product SHALL add unreviewed behavior.\n"
        )
    _commit(repo, "add unapproved main spec requirement")


def _add_unapproved_spec_exclusion(history: dict[str, str | Path]) -> None:
    repo = history["repo"]
    assert isinstance(repo, Path)
    _closeout(history)
    path = repo / "openspec/specs/sdk-surface/spec.md"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            "\n\n### Exclusion: Unapproved closeout scope\n\n"
            "The closeout SHALL exclude unreviewed behavior.\n"
        )
    _commit(repo, "add unapproved main spec exclusion")


_CLOSEOUT_MUTATION_CASES = (
    _CloseoutMutationCase(
        "unauthorized-design", _change_requirement, "changed approved artifact design.md"
    ),
    _CloseoutMutationCase(
        "tampered-archive", _tamper_archive, "changed approved artifact design.md"
    ),
    _CloseoutMutationCase(
        "incomplete-tasks", _leave_tasks_incomplete, "tasks differ beyond completing"
    ),
    _CloseoutMutationCase(
        "lost-main-requirements",
        _drop_existing_main_requirements,
        "main spec requirements differ from the approved merge",
    ),
    _CloseoutMutationCase(
        "missing-synced-requirements",
        _omit_synced_change_requirements,
        "main spec requirements differ from the approved merge",
    ),
    _CloseoutMutationCase(
        "extra-archive-file", _add_archived_file, "changed the approved artifact file set"
    ),
    _CloseoutMutationCase(
        "wrong-archive-name", _use_wrong_archive_name, "archive path does not match"
    ),
    _CloseoutMutationCase(
        "multiple-archives", _add_second_archive, "multiple closeout archive directories"
    ),
    _CloseoutMutationCase(
        "active-and-archive", _keep_active_and_archived_trees, "both active and archived"
    ),
    _CloseoutMutationCase(
        "removed-without-archive",
        _remove_change_without_archiving,
        "removed the approved change without archiving",
    ),
    _CloseoutMutationCase(
        "missing-main-spec", _remove_synced_main_spec, "synced main spec is missing"
    ),
    _CloseoutMutationCase(
        "unrelated-openspec",
        _add_unrelated_openspec_file,
        "unrelated OpenSpec changes",
    ),
    _CloseoutMutationCase("task-text-changed", _change_task_text, "tasks differ beyond completing"),
    _CloseoutMutationCase(
        "extra-requirement",
        _add_unapproved_spec_requirement,
        "main spec requirements differ from the approved merge",
    ),
    _CloseoutMutationCase(
        "extra-exclusion",
        _add_unapproved_spec_exclusion,
        "main spec requirements differ from the approved merge",
    ),
)


def test_composition_cli_accepts_verified_closeout_archive(
    history: dict[str, str | Path],
) -> None:
    candidate = _closeout(history)
    assert _run_main(history, candidate) == 0
    result = _run_cli(history, candidate)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"Composition {history['composition']} is preserved in {candidate}.\n"


@pytest.mark.parametrize("case", _CLOSEOUT_MUTATION_CASES, ids=lambda case: case.id)
def test_composition_gate_rejects_unapproved_closeout_mutations(
    history: dict[str, str | Path],
    case: _CloseoutMutationCase,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case.mutate(history)
    with pytest.raises(CompositionError, match=case.expected_error):
        _verify(history, candidate_sha="HEAD")
    assert _run_main(history, "HEAD") == 1
    assert "Composition verification failed:" in capsys.readouterr().err
    cli_result = _run_cli(history, "HEAD")
    assert cli_result.returncode == 1
    assert cli_result.stderr.startswith(
        "Composition verification failed: candidate OpenSpec subtree differs from planning "
        "SHA (openspec/changes/demo): "
    )
    assert case.expected_error in cli_result.stderr


@dataclass(frozen=True)
class _OpenSpecPathCase:
    id: str
    path: str
    expected_error: str


_OPENSPEC_PATH_CASES = (
    _OpenSpecPathCase(
        "nonexistent-change",
        "openspec/changes/not-real",
        "planning SHA has no OpenSpec change at openspec/changes/not-real",
    ),
    _OpenSpecPathCase(
        "malformed-change-path",
        "openspec/changes/../demo",
        "OpenSpec change path must be openspec/changes/<change>",
    ),
    _OpenSpecPathCase(
        "unapproved-source-tree",
        "openspec/specs/sdk-surface",
        "OpenSpec change path must be openspec/changes/<change>",
    ),
)


_UNAPPROVED_SPEC_BLOCK_CASES = (
    _CloseoutMutationCase(
        "extra-requirement",
        _add_unapproved_spec_requirement,
        "main spec requirements differ from the approved merge",
    ),
    _CloseoutMutationCase(
        "extra-exclusion",
        _add_unapproved_spec_exclusion,
        "main spec requirements differ from the approved merge",
    ),
)


@pytest.mark.parametrize("case", _OPENSPEC_PATH_CASES, ids=lambda case: case.id)
def test_composition_cli_rejects_unapproved_planning_path(
    history: dict[str, str | Path],
    case: _OpenSpecPathCase,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run_main(history, str(history["candidate"]), case.path) == 1
    assert capsys.readouterr().err == f"Composition verification failed: {case.expected_error}\n"
    result = _run_cli(history, str(history["candidate"]), case.path)
    assert result.returncode == 1
    assert result.stderr == f"Composition verification failed: {case.expected_error}\n"


@pytest.mark.parametrize("case", _UNAPPROVED_SPEC_BLOCK_CASES, ids=lambda case: case.id)
def test_composition_cli_rejects_unapproved_main_spec_blocks(
    history: dict[str, str | Path], case: _CloseoutMutationCase
) -> None:
    case.mutate(history)
    result = _run_cli(history, "HEAD")
    assert result.returncode == 1
    assert result.stderr == (
        "Composition verification failed: candidate OpenSpec subtree differs from planning "
        "SHA (openspec/changes/demo): synced main spec requirements differ from the approved "
        "merge: sdk-surface/spec.md\n"
    )


_KEEP_BLOCK = "### Requirement: Kept\n\nKeep this approved behavior."
_OLD_BLOCK = "### Requirement: Changed\n\nOld approved behavior."
_UPDATED_BLOCK = "### Requirement: Changed\n\nUpdated approved behavior."
_REMOVED_BLOCK = "### Requirement: Removed\n\nThis behavior is retired."
_EXCLUSION_BLOCK = "### Exclusion: Existing boundary\n\nThis capability stays excluded."
_ADDED_BLOCK = "### Requirement: Added\n\nAdd this approved behavior."
_BASE_SPEC = "## Requirements\n\n" + "\n\n".join(
    (_KEEP_BLOCK, _OLD_BLOCK, _REMOVED_BLOCK, _EXCLUSION_BLOCK)
)


@dataclass(frozen=True)
class _SpecMergeCase:
    id: str
    additions: tuple[str, ...]
    modifications: tuple[str, ...]
    removals: tuple[str, ...]
    expected: tuple[str, ...]


_SPEC_MERGE_CASES = (
    _SpecMergeCase(
        "append-approved-requirement",
        (_ADDED_BLOCK,),
        (),
        (),
        (_KEEP_BLOCK, _OLD_BLOCK, _REMOVED_BLOCK, _EXCLUSION_BLOCK, _ADDED_BLOCK),
    ),
    _SpecMergeCase(
        "replace-remove-and-append-approved-blocks",
        (_ADDED_BLOCK,),
        (_UPDATED_BLOCK,),
        (_REMOVED_BLOCK,),
        (_KEEP_BLOCK, _UPDATED_BLOCK, _EXCLUSION_BLOCK, _ADDED_BLOCK),
    ),
)


@pytest.mark.parametrize("case", _SPEC_MERGE_CASES, ids=lambda case: case.id)
def test_composition_spec_sync_merges_exact_approved_blocks(case: _SpecMergeCase) -> None:
    assert (
        _merged_spec_blocks(
            previous_text=_BASE_SPEC,
            relative_path="sdk-surface/spec.md",
            additions=case.additions,
            modifications=case.modifications,
            removals=case.removals,
        )
        == case.expected
    )


@dataclass(frozen=True)
class _InvalidSpecMergeCase:
    id: str
    previous_text: str
    additions: tuple[str, ...]
    modifications: tuple[str, ...]
    removals: tuple[str, ...]
    expected_error: str


_INVALID_SPEC_MERGE_CASES = (
    _InvalidSpecMergeCase(
        "duplicate-retained-block",
        _BASE_SPEC + "\n\n" + _KEEP_BLOCK,
        (),
        (),
        (),
        "main spec repeats a requirement",
    ),
    _InvalidSpecMergeCase(
        "unknown-modification",
        _BASE_SPEC,
        (),
        ("### Requirement: Unknown\n\nUnknown behavior.",),
        (),
        "change spec modifies an unknown requirement",
    ),
    _InvalidSpecMergeCase(
        "modify-and-remove",
        _BASE_SPEC,
        (),
        (_UPDATED_BLOCK,),
        (_OLD_BLOCK,),
        "change spec both modifies and removes a requirement",
    ),
    _InvalidSpecMergeCase(
        "add-existing-requirement",
        _BASE_SPEC,
        (_KEEP_BLOCK,),
        (),
        (),
        "change spec adds an existing requirement",
    ),
)


@pytest.mark.parametrize("case", _INVALID_SPEC_MERGE_CASES, ids=lambda case: case.id)
def test_composition_spec_sync_rejects_ambiguous_approved_blocks(
    case: _InvalidSpecMergeCase,
) -> None:
    with pytest.raises(CompositionError, match=case.expected_error):
        _merged_spec_blocks(
            previous_text=case.previous_text,
            relative_path="sdk-surface/spec.md",
            additions=case.additions,
            modifications=case.modifications,
            removals=case.removals,
        )


def test_composition_spec_sync_rejects_unapproved_requirement_sections() -> None:
    with pytest.raises(CompositionError, match="unsupported requirement section"):
        _expected_synced_specs(
            {
                "specs/sdk-surface/spec.md": (
                    b"## ADDED Requirements\n\n### Requirement: Approved\n\n"
                    b"Approved behavior.\n\n## EXCLUDED Requirements\n\n"
                    b"### Exclusion: Unapproved\n\nUnapproved behavior.\n"
                )
            }
        )

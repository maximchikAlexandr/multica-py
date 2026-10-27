#!/usr/bin/env python3
"""Verify the immutable implementation composition and candidate ancestry."""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import PurePosixPath


class CompositionError(ValueError):
    """Raised when a candidate does not preserve the approved composition."""


_TASK = re.compile(r"^(\s*-\s*\[)( |x)(\].*)$")
_SPEC_DELTA_SECTION = re.compile(r"^## (ADDED|MODIFIED|REMOVED) Requirements\s*$", re.MULTILINE)
_SPEC_BLOCK = re.compile(
    r"^### (?:Requirement|Exclusion):.*?(?=^### (?:Requirement|Exclusion):|\Z)",
    flags=re.MULTILINE | re.DOTALL,
)
_SPEC_BLOCK_ID = re.compile(r"^### (Requirement|Exclusion):\s*(.+?)\s*$", re.MULTILINE)


def _tree_files(revision: str, path: str) -> dict[str, bytes]:
    listing = _git("ls-tree", "-r", revision, "--", path)
    files: dict[str, bytes] = {}
    prefix = f"{path.rstrip('/')}/"
    for line in listing.splitlines():
        metadata, separator, full_path = line.partition("\t")
        fields = metadata.split()
        if not separator or len(fields) != 3 or fields[0] not in {"100644", "100755"}:
            raise CompositionError(f"unsupported OpenSpec tree entry under {path}")
        if not full_path.startswith(prefix):
            raise CompositionError(f"unexpected OpenSpec tree entry: {full_path}")
        result = subprocess.run(
            ["git", "show", f"{revision}:{full_path}"],
            check=False,
            capture_output=True,
        )
        if result.returncode:
            raise CompositionError(f"cannot read OpenSpec artifact {full_path}")
        files[full_path[len(prefix) :]] = result.stdout
    return files


def _task_completion_preserves_text(planned: bytes, final: bytes) -> bool:
    try:
        old_lines = planned.decode("utf-8").splitlines(keepends=True)
        new_lines = final.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return False
    if len(old_lines) != len(new_lines):
        return False
    task_count = 0
    for old, new in zip(old_lines, new_lines, strict=True):
        old_match = _TASK.match(old)
        new_match = _TASK.match(new)
        if old_match is None and new_match is None:
            if old != new:
                return False
            continue
        if old_match is None or new_match is None or old_match.group(3) != new_match.group(3):
            return False
        task_count += 1
        if old_match.group(2) not in {" ", "x"} or new_match.group(2) != "x":
            return False
    return task_count > 0


def _requirement_blocks(text: str) -> tuple[str, ...]:
    return tuple(block.strip() for block in _SPEC_BLOCK.findall(text))


def _requirement_id(block: str, path: str) -> tuple[str, str]:
    match = _SPEC_BLOCK_ID.match(block)
    if match is None:
        raise CompositionError(f"invalid requirement block in change spec: {path}")
    return match.group(1), match.group(2)


def _expected_synced_specs(
    files: dict[str, bytes],
) -> dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]]:
    specs: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {}
    for relative_path, content in files.items():
        parts = PurePosixPath(relative_path).parts
        if not relative_path.startswith("specs/"):
            continue
        if len(parts) != 3 or parts[0] != "specs" or parts[2] != "spec.md":
            raise CompositionError(f"unsupported change spec path: {relative_path}")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CompositionError(f"change spec is not UTF-8: {relative_path}") from exc
        headings = list(_SPEC_DELTA_SECTION.finditer(text))
        all_requirement_headings = list(
            re.finditer(r"^## .*Requirements\s*$", text, flags=re.MULTILINE)
        )
        if len(headings) != len(all_requirement_headings):
            raise CompositionError(f"unsupported requirement section: {relative_path}")
        if not any(match.group(1) == "ADDED" for match in headings):
            raise CompositionError(
                f"change spec has no ADDED Requirements section: {relative_path}"
            )
        deltas: dict[str, list[str]] = {"ADDED": [], "MODIFIED": [], "REMOVED": []}
        for index, heading in enumerate(headings):
            section_end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            next_heading = re.search(r"^## ", text[heading.end() : section_end], re.MULTILINE)
            if next_heading is not None:
                section_end = heading.end() + next_heading.start()
            blocks = _requirement_blocks(text[heading.end() : section_end])
            if not blocks:
                raise CompositionError(f"change spec section has no requirements: {relative_path}")
            deltas[heading.group(1)].extend(blocks)
        for operation, delta_blocks in deltas.items():
            identities = [_requirement_id(block, relative_path) for block in delta_blocks]
            if len(identities) != len(set(identities)):
                raise CompositionError(
                    f"change spec repeats a {operation.lower()} requirement: {relative_path}"
                )
        specs[f"{parts[1]}/spec.md"] = (
            tuple(deltas["ADDED"]),
            tuple(deltas["MODIFIED"]),
            tuple(deltas["REMOVED"]),
        )
    return specs


def _spec_prefix(text: str) -> str:
    first_block = _SPEC_BLOCK.search(text)
    return text if first_block is None else text[: first_block.start()]


def _merged_spec_blocks(
    *,
    previous_text: str,
    relative_path: str,
    additions: tuple[str, ...],
    modifications: tuple[str, ...],
    removals: tuple[str, ...],
) -> tuple[str, ...]:
    previous_blocks = _requirement_blocks(previous_text)
    previous_ids = [_requirement_id(block, relative_path) for block in previous_blocks]
    previous_counts = {identity: previous_ids.count(identity) for identity in set(previous_ids)}
    modified_ids = [_requirement_id(block, relative_path) for block in modifications]
    removed_ids_list = [_requirement_id(block, relative_path) for block in removals]
    added_ids = [_requirement_id(block, relative_path) for block in additions]
    if len(modified_ids) != len(set(modified_ids)) or len(removed_ids_list) != len(
        set(removed_ids_list)
    ):
        raise CompositionError(f"change spec repeats an approved edit: {relative_path}")
    modified_by_id = dict(zip(modified_ids, modifications, strict=True))
    removed_ids = set(removed_ids_list)
    previous_id_set = set(previous_ids)
    if not (set(modified_by_id) | removed_ids) <= previous_id_set:
        raise CompositionError(f"change spec modifies an unknown requirement: {relative_path}")
    if set(modified_by_id) & removed_ids:
        raise CompositionError(
            f"change spec both modifies and removes a requirement: {relative_path}"
        )
    if len(added_ids) != len(set(added_ids)) or set(added_ids) & previous_id_set:
        raise CompositionError(f"change spec adds an existing requirement: {relative_path}")
    edited_ids = set(modified_by_id) | removed_ids
    if any(previous_counts[identity] != 1 for identity in edited_ids):
        raise CompositionError(
            f"change spec ambiguously edits a repeated requirement: {relative_path}"
        )
    merged = tuple(
        modified_by_id.get(identity, block)
        for identity, block in zip(previous_ids, previous_blocks, strict=True)
        if identity not in removed_ids
    )
    return (*merged, *additions)


def _approved_change_tree(planning_sha: str, openspec_path: str) -> tuple[str, dict[str, bytes]]:
    source = PurePosixPath(openspec_path)
    if (
        source.is_absolute()
        or source.parts[:2] != ("openspec", "changes")
        or len(source.parts) != 3
        or source.name in {"", ".", ".."}
        or openspec_path != source.as_posix()
    ):
        raise CompositionError("OpenSpec change path must be openspec/changes/<change>")
    source_path = source.as_posix()
    planned = _tree_files(planning_sha, source_path)
    if not planned:
        raise CompositionError(f"planning SHA has no OpenSpec change at {source_path}")
    return source_path, planned


def _verify_closeout(
    *,
    planning_sha: str,
    candidate_sha: str,
    source_path: str,
    planned: dict[str, bytes],
) -> None:
    candidate_source = _tree_files(candidate_sha, source_path)
    changed_paths = set(
        filter(
            None,
            _git("diff", "--name-only", planning_sha, candidate_sha, "--", "openspec").splitlines(),
        )
    )
    closeout_files = planned
    archive_root = "openspec/changes/archive/"
    archive_paths = {
        path.split("/", 4)[3] for path in changed_paths if path.startswith(archive_root)
    }
    archive_path: str | None = None
    if archive_paths:
        if len(archive_paths) != 1:
            raise CompositionError("candidate contains multiple closeout archive directories")
        archive_name = archive_paths.pop()
        match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-(.+)", archive_name)
        if match is None or match.group(2) != PurePosixPath(source_path).name:
            raise CompositionError("candidate archive path does not match the approved change")
        try:
            datetime.date.fromisoformat(match.group(1))
        except ValueError as exc:
            raise CompositionError("candidate archive path has an invalid date") from exc
        archive_path = f"{archive_root}{archive_name}"
        closeout_files = _tree_files(candidate_sha, archive_path)
        if candidate_source:
            raise CompositionError("candidate contains both active and archived change trees")
    elif not candidate_source:
        raise CompositionError("candidate removed the approved change without archiving it")

    if set(closeout_files) != set(planned):
        raise CompositionError("closeout changed the approved artifact file set")
    for relative_path, planned_content in planned.items():
        candidate_content = closeout_files[relative_path]
        if relative_path == "tasks.md":
            if not _task_completion_preserves_text(planned_content, candidate_content):
                raise CompositionError(
                    "closeout tasks differ beyond completing approved checkboxes"
                )
        elif candidate_content != planned_content:
            raise CompositionError(f"closeout changed approved artifact {relative_path}")

    synced_specs = _expected_synced_specs(planned)
    candidate_specs = _tree_files(candidate_sha, "openspec/specs")
    planned_specs = _tree_files(planning_sha, "openspec/specs")
    expected_main_paths = {f"openspec/specs/{path}" for path in synced_specs}
    for relative_path, (additions, modifications, removals) in synced_specs.items():
        previous = planned_specs.get(relative_path)
        final = candidate_specs.get(relative_path)
        if previous is None or final is None:
            raise CompositionError(f"synced main spec is missing: {relative_path}")
        try:
            previous_text = previous.decode("utf-8")
            final_text = final.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CompositionError(f"main spec is not UTF-8: {relative_path}") from exc
        expected_blocks = _merged_spec_blocks(
            previous_text=previous_text,
            relative_path=relative_path,
            additions=additions,
            modifications=modifications,
            removals=removals,
        )
        if (
            _spec_prefix(final_text) != _spec_prefix(previous_text)
            or _requirement_blocks(final_text) != expected_blocks
        ):
            raise CompositionError(
                f"synced main spec requirements differ from the approved merge: {relative_path}"
            )

    allowed_paths = {
        f"{source_path}/{relative_path}" for relative_path in planned
    } | expected_main_paths
    if archive_path:
        allowed_paths.update(f"{archive_path}/{relative_path}" for relative_path in planned)
    if not changed_paths <= allowed_paths:
        raise CompositionError("candidate contains unrelated OpenSpec changes during closeout")


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if result.returncode:
        raise CompositionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _ancestor(ancestor: str, descendant: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise CompositionError(f"{ancestor} is not an ancestor of {descendant}")


def verify_composition(
    *,
    composition_sha: str,
    composition_planning_sha: str,
    verified_planning_sha: str,
    baseline_sha: str,
    integration_sha: str,
    candidate_sha: str,
    openspec_path: str,
    accepted_shas: Sequence[str] = (),
) -> None:
    """Assert immutable history and strict planning equality or verified closeout."""
    _git("cat-file", "-e", f"{composition_sha}^{{commit}}")
    parents = _git("rev-list", "--parents", "-n", "1", composition_sha).split()
    if parents != [composition_sha, baseline_sha, composition_planning_sha]:
        raise CompositionError("composition does not have the exact baseline/planning parents")
    _ancestor(integration_sha, verified_planning_sha)
    _ancestor(composition_sha, integration_sha)
    _ancestor(composition_sha, candidate_sha)
    _ancestor(verified_planning_sha, candidate_sha)
    for accepted_sha in accepted_shas:
        _ancestor(accepted_sha, candidate_sha)
    candidate_head = _git("rev-parse", "--verify", f"{candidate_sha}^{{commit}}")
    if candidate_head != _git("rev-parse", "--verify", "HEAD^{commit}"):
        raise CompositionError("candidate SHA must resolve to the final checkout HEAD")
    source_path, planned = _approved_change_tree(verified_planning_sha, openspec_path)
    diff = subprocess.run(
        ["git", "diff", "--quiet", verified_planning_sha, candidate_sha, "--", openspec_path],
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode == 0:
        return
    try:
        _verify_closeout(
            planning_sha=verified_planning_sha,
            candidate_sha=candidate_sha,
            source_path=source_path,
            planned=planned,
        )
    except CompositionError as exc:
        raise CompositionError(
            f"candidate OpenSpec subtree differs from planning SHA ({openspec_path}): {exc}"
        ) from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--composition-sha", required=True)
    parser.add_argument("--composition-planning-sha", required=True)
    parser.add_argument("--verified-planning-sha", required=True)
    parser.add_argument("--baseline-sha", required=True)
    parser.add_argument("--integration-sha", required=True)
    parser.add_argument("--accepted-sha", action="append", default=[])
    parser.add_argument("--candidate-sha", default="HEAD")
    parser.add_argument("--openspec-path", default="openspec/changes/update-multica-0-7-0")
    args = parser.parse_args(argv)
    try:
        verify_composition(
            composition_sha=args.composition_sha,
            composition_planning_sha=args.composition_planning_sha,
            verified_planning_sha=args.verified_planning_sha,
            baseline_sha=args.baseline_sha,
            integration_sha=args.integration_sha,
            candidate_sha=args.candidate_sha,
            openspec_path=args.openspec_path,
            accepted_shas=args.accepted_sha,
        )
    except CompositionError as exc:
        print(f"Composition verification failed: {exc}", file=sys.stderr)
        return 1
    print(f"Composition {args.composition_sha} is preserved in {args.candidate_sha}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

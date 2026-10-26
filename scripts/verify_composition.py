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


def _expected_synced_specs(files: dict[str, bytes]) -> dict[str, bytes]:
    specs: dict[str, bytes] = {}
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
        header = "## ADDED Requirements\n\n"
        if header not in text:
            raise CompositionError(
                f"change spec has no ADDED Requirements section: {relative_path}"
            )
        body = text.split(header, 1)[1].strip()
        if not body:
            raise CompositionError(f"change spec has no requirements: {relative_path}")
        specs[f"{parts[1]}/spec.md"] = body.encode("utf-8")
    return specs


def _requirement_blocks(text: str) -> tuple[str, ...]:
    return tuple(
        block.strip()
        for block in re.findall(
            r"^### Requirement:.*?(?=^### Requirement:|\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
    )


def _verify_closeout(
    *,
    planning_sha: str,
    candidate_sha: str,
    openspec_path: str,
) -> None:
    source = PurePosixPath(openspec_path)
    if (
        source.is_absolute()
        or source.parts[:2] != ("openspec", "changes")
        or len(source.parts) != 3
        or source.name in {"", ".", ".."}
    ):
        raise CompositionError("OpenSpec change path must be openspec/changes/<change>")
    source_path = source.as_posix()
    planned = _tree_files(planning_sha, source_path)
    if not planned:
        raise CompositionError(f"planning SHA has no OpenSpec change at {source_path}")

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
        if match is None or match.group(2) != source.name:
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
    for relative_path, requirement_body in synced_specs.items():
        previous = planned_specs.get(relative_path)
        final = candidate_specs.get(relative_path)
        if previous is None or final is None:
            raise CompositionError(f"synced main spec is missing: {relative_path}")
        try:
            previous_text = previous.decode("utf-8")
            final_text = final.decode("utf-8")
            required_text = requirement_body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CompositionError(f"main spec is not UTF-8: {relative_path}") from exc
        if any(block not in final_text for block in _requirement_blocks(previous_text)):
            raise CompositionError(
                f"synced main spec removed or changed existing requirements: {relative_path}"
            )
        if required_text not in final_text:
            raise CompositionError(
                f"synced main spec omits approved change requirements: {relative_path}"
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
            openspec_path=openspec_path,
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

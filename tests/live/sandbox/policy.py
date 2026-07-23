"""Sandbox filesystem policy and deterministic issue-description helpers.

Exports:
  - ``ALLOWLIST_FILES`` / ``ALLOWLIST_ROOTS`` / ``ALLOWLIST_PREFIXES``:
    paths the sandbox policy permits the agent to modify.
  - ``USER_FILES``: target and control files the workflow rewrites or pins.
  - ``assert_manifest_policy``: enforce the policy against before/after manifests.
  - ``write_initial_sandbox_files``: write the deterministic starting state.
  - ``issue_description_for_run``: deterministic issue body (fake OpenCode contract).
  - ``canary_issue_title_for_run`` / ``canary_issue_description_for_run``:
    canary-mode title and body.
"""

from __future__ import annotations

import json
import pathlib

from tests.live.sandbox.models import FileManifest, hash_text

ALLOWLIST_FILES = frozenset({"AGENTS.md"})
ALLOWLIST_ROOTS = frozenset({".multica", ".opencode", ".agent_context"})
ALLOWLIST_PREFIXES = (".multica/", ".opencode/", ".agent_context/")
USER_FILES = frozenset({"target.txt", "control.txt"})


def _path_allowed_to_change(relative: str) -> bool:
    if relative in ALLOWLIST_FILES or relative in ALLOWLIST_ROOTS:
        return True
    return any(relative.startswith(prefix) for prefix in ALLOWLIST_PREFIXES)


def assert_manifest_policy(
    before: FileManifest,
    after: FileManifest,
    run_id: str,
    *,
    expect_target_change: bool,
) -> None:
    """Assert sandbox filesystem policy against before and after manifests.

    ``run_id`` pins the expected target/control bytes; ``expect_target_change``
    declares whether the agent should have rewritten ``target.txt``.
    """
    expected_target = f"after:{run_id}\n"
    expected_control = f"control:{run_id}\n"
    target_path = "target.txt"
    control_path = "control.txt"
    if expect_target_change:
        after_target = after.get(target_path)
        if after_target is None:
            msg = "target.txt missing after run"
            raise AssertionError(msg)
        expected_hash = hash_text(expected_target)
        if after_target.sha256 != expected_hash:
            msg = f"target.txt bytes mismatch: expected {expected_target!r}"
            raise AssertionError(msg)
    else:
        if before.get(target_path) != after.get(target_path):
            msg = "target.txt changed unexpectedly"
            raise AssertionError(msg)
    before_control = before.get(control_path)
    after_control = after.get(control_path)
    if before_control != after_control:
        msg = "control.txt changed"
        raise AssertionError(msg)
    if after_control is not None:
        expected_hash = hash_text(expected_control)
        if after_control.sha256 != expected_hash:
            msg = "control.txt bytes mismatch"
            raise AssertionError(msg)
    all_paths = set(before) | set(after)
    for relative in sorted(all_paths):
        if relative in USER_FILES or _path_allowed_to_change(relative):
            continue
        if before.get(relative) != after.get(relative):
            msg = f"unexpected filesystem change at {relative}"
            raise AssertionError(msg)


def write_initial_sandbox_files(sandbox_dir: pathlib.Path, run_id: str) -> None:
    """Write exact initial target and control files for one sandbox run."""
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    (sandbox_dir / "target.txt").write_text(f"before:{run_id}\n", encoding="utf-8")
    (sandbox_dir / "control.txt").write_text(f"control:{run_id}\n", encoding="utf-8")


def issue_description_for_run(run_id: str) -> str:
    """Build the deterministic issue description for one sandbox run."""
    action = json.dumps(
        {
            "schema": 1,
            "path": "target.txt",
            "before": f"before:{run_id}\n",
            "after": f"after:{run_id}\n",
        },
        separators=(",", ":"),
    )
    return (
        "Edit target.txt in the attached local directory.\n"
        "Replace the exact current content with the exact replacement below.\n"
        "Do not modify control.txt or any other user file.\n"
        f"MULTICA_TEST_ACTION={action}"
    )


def canary_issue_title_for_run(run_id: str) -> str:
    """Build the canary issue title for one real-provider run."""
    return f"Agent canary edit {run_id}"


def canary_issue_description_for_run(run_id: str) -> str:
    """Build the canary issue description for one real-provider run."""
    return (
        "Replace the entire contents of target.txt with exactly:\n"
        f"after:{run_id}\n"
        "(with trailing newline)\n"
        "Do not modify control.txt or any other file.\n"
        "Initial content of target.txt is exactly:\n"
        f"before:{run_id}\n"
        "(with trailing newline)"
    )


__all__ = [
    "ALLOWLIST_FILES",
    "ALLOWLIST_PREFIXES",
    "ALLOWLIST_ROOTS",
    "USER_FILES",
    "assert_manifest_policy",
    "canary_issue_description_for_run",
    "canary_issue_title_for_run",
    "issue_description_for_run",
    "write_initial_sandbox_files",
]

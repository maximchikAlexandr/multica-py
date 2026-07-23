"""Immutable data models for the agent-sandbox three-phase workflow.

Exports:
  - FileManifestEntry: one filesystem entry in a sandbox manifest.
  - FileManifest: map of relative path to manifest entry.
  - PreparedSandbox: ready-to-run sandbox handle (T070).
  - CompletedAssignment: result of ``run_assignment`` (T070).
  - SandboxVerification: result of ``verify_sandbox`` (T070).
"""

from __future__ import annotations

import hashlib
import os
import pathlib
from dataclasses import dataclass
from typing import Literal

FileKind = Literal["file", "directory", "symlink"]


@dataclass(frozen=True, slots=True)
class FileManifestEntry:
    """One filesystem entry in a sandbox manifest."""

    kind: FileKind
    size: int
    sha256: str | None = None
    symlink_target: str | None = None
    text: str | None = None


FileManifest = dict[str, FileManifestEntry]


@dataclass(frozen=True, slots=True)
class PreparedSandbox:
    """Result of ``prepare_sandbox``: isolated workspace, ready to assign.

    Carries the canonical paths plus the deterministic marker files. The
    caller registers ``cleanup`` on the session ExitStack immediately after
    ``prepare_sandbox`` returns; removing the workspace dir is enough to
    clean the prepared state.
    """

    sandbox_dir: pathlib.Path
    run_id: str
    target_path: pathlib.Path
    control_path: pathlib.Path


@dataclass(frozen=True, slots=True)
class CompletedAssignment:
    """Result of ``run_assignment``: the run reached a terminal state.

    Carries the run status, before/after filesystem manifests, cleanup
    failures from the immediate post-run cleanup pass, and any canary
    cost. The caller invokes ``verify_sandbox`` next.
    """

    run_status: str
    cancelled: bool
    manifest_before: FileManifest
    manifest_after: FileManifest
    cleanup_errors: tuple[str, ...] = ()
    cost_usd: float | None = None
    primary_error: str | None = None
    file_assertion_failed: bool = False


@dataclass(frozen=True, slots=True)
class SandboxVerification:
    """Result of ``verify_sandbox``: policy checks passed or a primary error.

    The verification must run before the session ExitStack runs cleanup so
    it can still inspect the filesystem.
    """

    verified: bool
    primary_error: str | None


def hash_text(text: str) -> str:
    """Return the sha256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode()).hexdigest()


def build_file_manifest(root: pathlib.Path) -> FileManifest:
    """Build a recursive manifest for files under a sandbox root.

    Text content is included only for the canonical user files
    (``target.txt`` and ``control.txt``); the diff writer uses it.
    """
    from tests.live.sandbox.policy import USER_FILES

    manifest: FileManifest = {}
    if not root.is_dir():
        return manifest
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            manifest[relative] = FileManifestEntry(
                kind="symlink",
                size=0,
                symlink_target=os.readlink(path),
            )
            continue
        if path.is_dir():
            manifest[relative] = FileManifestEntry(kind="directory", size=0)
            continue
        if path.is_file():
            content = path.read_bytes()
            text = content.decode("utf-8") if relative in USER_FILES else None
            manifest[relative] = FileManifestEntry(
                kind="file",
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                text=text,
            )
    return manifest


__all__ = [
    "CompletedAssignment",
    "FileKind",
    "FileManifest",
    "FileManifestEntry",
    "PreparedSandbox",
    "SandboxVerification",
    "build_file_manifest",
    "hash_text",
]

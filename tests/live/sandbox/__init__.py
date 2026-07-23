"""Agent-sandbox subpackage (T070).

Public surface for the three-phase sandbox workflow:
  - ``prepare_sandbox``: phase 1, isolated workspace.
  - ``run_assignment``: phase 2, agent runs the assignment.
  - ``verify_sandbox``: phase 3, policy verification.

Each phase owns its cleanup and registers it on the session ``ExitStack``
as soon as it acquires its resources (immediate LIFO cleanup).
"""

from tests.live.sandbox.models import (
    CompletedAssignment,
    FileKind,
    FileManifest,
    FileManifestEntry,
    PreparedSandbox,
    SandboxVerification,
    build_file_manifest,
    hash_text,
)
from tests.live.sandbox.policy import (
    ALLOWLIST_FILES,
    ALLOWLIST_PREFIXES,
    ALLOWLIST_ROOTS,
    USER_FILES,
    assert_manifest_policy,
    canary_issue_description_for_run,
    canary_issue_title_for_run,
    issue_description_for_run,
    write_initial_sandbox_files,
)
from tests.live.sandbox.workflow import (
    Assignment,
    LiveCleanupError,
    SandboxCleanupRegistry,
    prepare_sandbox,
    run_assignment,
    verify_sandbox,
)

__all__ = [
    "ALLOWLIST_FILES",
    "ALLOWLIST_PREFIXES",
    "ALLOWLIST_ROOTS",
    "USER_FILES",
    "Assignment",
    "CompletedAssignment",
    "FileKind",
    "FileManifest",
    "FileManifestEntry",
    "LiveCleanupError",
    "PreparedSandbox",
    "SandboxCleanupRegistry",
    "SandboxVerification",
    "assert_manifest_policy",
    "build_file_manifest",
    "canary_issue_description_for_run",
    "canary_issue_title_for_run",
    "hash_text",
    "issue_description_for_run",
    "prepare_sandbox",
    "run_assignment",
    "verify_sandbox",
    "write_initial_sandbox_files",
]

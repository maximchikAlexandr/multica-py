## Why

Multica `0.8.1` supersedes the SDK's reviewed `0.7.1` ceiling and changes retained CLI and response behavior across three stable releases. The SDK needs one evidence-backed `0.7.1` to `0.8.1` contract refresh that adapts supported operations without turning newly discovered upstream commands into public SDK surface automatically.

## What Changes

- Advance the approved target through `0.7.2`, `0.8.0`, and `0.8.1` to exact release `436353568` at commit `b1ea927def6490c43bedff537b6f4ed9a47fa828`, preserving the exact `0.7.1` baseline and moving the exclusive compatibility ceiling to `0.8.2`.
- Reconcile the complete `209 -> 225` command inventory: 17 additions, one public removal, 15 changed nodes, the dynamic public `issue wakeup checkin` parser exception, and hidden/source-only commands.
- Reconcile all 196 supported response entrypoints, adapting the 23 changed entrypoints and retaining the other 173 without speculative expansion.
- Add paired updated-time filtering to `issues.list`, literal repeatable attachment handling, roots-only comment resolution projections, task credit usage, image dimensions, project creator identity, runtime concurrency fields, user-profile version state, and workspace pinning.
- **BREAKING**: replace the unsupported target mapping behind issue-targeted `issues.rerun(issue)` with the run-targeted `issues.rerun_task(run_id, *, issue=None, fresh=False)` contract returning a task row. This replacement is proposed for explicit human approval; implementation remains blocked until that gate accepts it.
- Keep comment steering, workflow/project-workflow, views, runtime-concurrency management, daemon process-control options, interactive assignee picking, skill-history commands, and other upstream-only behavior deferred or outside the SDK surface.
- Regenerate only from the human-reviewed `contracts/sdk-contract.json`, extend existing table-driven fixtures and verification gates, and keep binaries, source clones, collector output, and review evidence untracked.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin the complete `0.7.1` to `0.8.1` release/source/binary lineage, command and response reconciliation, compatibility interval, reviewed mappings, and deterministic projection.
- `sdk-surface`: Adapt retained issue, comment, task-run, attachment, project, runtime, user-profile, and workspace contracts, including the proposed breaking rerun replacement, without adding deferred command groups.
- `verification-and-release`: Require positive and negative table-driven coverage, deterministic contract generation, source-link checks, documentation, exact-revision CI evidence, and independent verification.

## Impact

- Approved contract and projection: `contracts/sdk-contract.json`, contract schema/validation/render/check tooling, and `src/multica_py/_generated/approved_sdk.py`.
- Existing resource/model paths for issues and comments, task runs, attachments, projects, runtimes, users, and workspaces; no new top-level resource, runtime dependency, or testing framework.
- Existing unit, contract, component, packaging, documentation, and CI fixtures. Evidence remains in ignored `.devlocal` storage and Multica attachments only.
- Public callers of `issues.rerun` require migration to run-targeted retry only after human approval of this package.

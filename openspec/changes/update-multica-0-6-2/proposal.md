## Why

Multica `0.6.2` changes supported CLI, property, daemon-status, wakeup, error, search, and project-update contracts beyond the SDK's reviewed `0.6.1` ceiling. The SDK needs a direct, evidence-backed `0.6.1` to `0.6.2` contract refresh so it remains deterministic and compatible without promoting unreviewed extractor suggestions or local daemon-autostart controls.

## What Changes

- Advance the approved upstream target and maximum-tested CLI to the exact Multica `0.6.2` release commit, with `0.6.3` as the exclusive compatibility ceiling and full release/binary provenance.
- Reconcile all 209 target CLI nodes and all 196 supported response entrypoints against pinned `0.6.1` and `0.6.2` source, preserving explicit reviewed exceptions for dynamic `issue wakeup checkin` discovery and hidden `daemon probe-runtimes`.
- Extend property definitions and issue property values with open `multi_text` and `multi_url` types, including parsing, validation, filtering, stable de-duplication, and display-value semantics.
- Expose `DaemonStatus.cli_commit` with legacy omission and explicit-empty handling, without falling back to `cli_version`.
- Expose nullable wakeup `last_error` diagnostics and their recovery clearing semantics across supported wakeup operations.
- Align upload transport-error classification, issue-search digit-prefix/cancellation behavior, project omitted-versus-null concurrency semantics, and redacted HTTP 500 errors with `0.6.2`.
- Regenerate only from the human-approved contract, extend table-driven fixtures/tests, and update compatibility, API, migration, coverage, packaging, and release documentation.
- Keep `daemon autostart enable|disable|status` deferred: this change does not add a public SDK surface for local OS registration side effects.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin and validate the direct `0.6.1` to `0.6.2` evidence, inventory, mappings, compatibility interval, and deterministic projection.
- `sdk-surface`: Adapt typed public models and error behavior for daemon identity, wakeup diagnostics, and changed retained operations without exposing daemon autostart.
- `property-resource`: Add reviewed open list-property definitions, values, filters, and display projections.
- `issue-wakeup-resource`: Preserve recoverable condition diagnostics and clear them after recovery.
- `subprocess-transport`: Classify interrupted upload response reads as network failures and preserve redacted server errors.
- `verification-and-release`: Require complete target inventory/response reconciliation, table-driven regressions, documentation, packaging, source-link, and release gates.

## Impact

- Approved contract and generated projection: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, contract schema/validation/render checks.
- Public models and adapters: property types/values, issue projections, daemon status, wakeups, project updates, search, attachments, and command-error mapping.
- Existing table-driven unit, contract, component, packaging, and gated live-smoke coverage; no new test framework.
- User-facing compatibility, API, service-usage, CLI-coverage, migration, changelog, contributing, and release documentation.
- No production dependency addition, no checked-in collector/audit evidence, and no public daemon-autostart methods.

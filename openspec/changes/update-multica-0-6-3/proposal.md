## Why

`multica-py` is certified only through Multica CLI 0.6.1, while the latest stable release is 0.6.3 and introduces reviewed property, project-workflow, daemon-status, and diagnostic response changes. The SDK needs one direct, evidence-pinned compatibility update from the effective 0.6.1 baseline without treating draft 0.6.2/0.6.3 work as an approved intermediate baseline.

## What Changes

- Re-pin the approved upstream contract and compatibility ceiling to stable Multica 0.6.3 at commit `18fa9f728a9e25f2465df2789631edb2a75442ad`, preserving the verified 0.6.1 baseline and reproducible provenance for the full direct range.
- Record a complete reviewed disposition for all 209 target CLI nodes and all 196 supported response work items, while preserving the boundary between review evidence and approved generator input.
- Add typed, deterministic support for `multi_text` and `multi_url` issue properties, including legacy comma-separated input, safe JSON-array input, ordered/duplicate-preserving decoding, and explicit null/empty/presence behavior.
- Add the nullable project `workflow_id` response field and workflow-aware issue create/status/update/project-move validation, status remapping, and assignee/run handoff behavior.
- Accept additive `daemon status.cli_commit` data while remaining compatible with the legacy omitted/empty form.
- Align wakeup diagnostics, upload failures, stable redacted server errors, and project partial-update semantics with the reviewed 0.6.3 behavior.
- Keep workflow-management HTTP endpoints outside the SDK because 0.6.3 exposes no approved public CLI operation; keep `daemon autostart*` deferred rather than expanding the public API automatically.
- Extend deterministic contract, table-driven unit/component/contract, compatibility, documentation, package, and independently collected live verification evidence for the approved behavior.

## Capabilities

### New Capabilities

- `project-workflow-compatibility`: Project workflow identity and workflow-aware issue-write behavior across validation, project moves, status remapping, and handoff.

### Modified Capabilities

- `upstream-contract`: Advance pinned release provenance, complete CLI/response dispositions, compatibility interval, and deterministic generation requirements from 0.6.1 to 0.6.3.
- `sdk-surface`: Extend approved typed wire/public models and adapters for daemon commit and reviewed response/error changes while explicitly excluding unapproved surfaces.
- `property-resource`: Support reviewed multi-value property kinds and deterministic legacy/JSON-array encoding and decoding semantics.
- `issue-wakeup-resource`: Preserve and expose the reviewed 0.6.3 wakeup diagnostic and error behavior.
- `verification-and-release`: Require offline contract/generation gates, targeted CI coverage, packaging checks, and independent live evidence against the exact approved CLI revision.

## Impact

- Approved contract and generated projection: `contracts/sdk-contract.json`, its schema/validator/renderer, and `src/multica_py/_generated/approved_sdk.py`.
- Typed models, wire adapters, decoders, compatibility metadata, and resources for properties, projects/issues, daemon status, wakeups, and errors.
- Existing table-driven unit/component/contract/packaging/live suites, provenance fixtures, compatibility documentation, and generated public API documentation.
- No new runtime dependency, workflow-management API, daemon-autostart API, database migration, or production implementation is authorized by this planning change.

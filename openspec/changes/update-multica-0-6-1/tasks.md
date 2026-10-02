## 1. Approved contract and generated projection

- [ ] 1.1 Replace SDK baseline and target provenance with exact `48745d2…` tree/contract facts and verified `v0.6.1` release, peeled commit, archive, executable and version-output identities; set direct compatibility `[0.6.0,0.6.2)`.
- [ ] 1.2 Reconcile all 205 CLI nodes as 203 unchanged and two adapted nodes with zero additions/removals/renames; retain explicit root/hidden/source-augmented dynamic-checkin classifications.
- [ ] 1.3 Add `duplicate_of -> --duplicate-of -> json_body:duplicate_of_issue_id` mappings, presence semantics, cancelled-only/content/attachment constraints, source references and positive/negative vectors for `issues.set_status`, `issues.set_status_bound`, `issues.update` and `issues.update_bound`.
- [ ] 1.4 Reconcile all 196 response entrypoints as nine changed and 187 unchanged with pinned old/target traces, adapters, fixtures and tests for duplicate transitions, provider quota, usage pricing semantics and repository checkout diagnostics.
- [ ] 1.5 Extend contract schema/validator/generator only if required by the approved mappings; run source-aware validate, render twice byte-identically and check the single generated runtime projection before handwritten edits.

## 2. Existing issue mutation surface

- [ ] 2.1 Add optional `duplicate_of: str | None = None` to direct and bound `set_status[_command]`, emit it once only when present, validate nonblank/cancelled before transport and apply the conditional CLI `0.6.1` minimum.
- [ ] 2.2 Add the same optional input to direct and bound `update[_command]`, preserve `Unset` semantics, permit omitted or `cancelled` status, and reject every other status before transport.
- [ ] 2.3 Reject present description and emitted attachment combinations with `duplicate_of` before executor/upload activity; preserve current attachment normalization, no-op update, assignment follow-up and larger timeout behavior for nonconflicting calls.
- [ ] 2.4 Reuse the existing `Issue.duplicate_of` decoder/binding and centralized typed/redacted CLI error path; prove the CLI-owned missing-response-field failure performs no SDK retry, synthesis or secondary mutation.

## 3. Table-driven compatibility evidence

- [ ] 3.1 Extend existing `ArgvCase`/operation tables with complete expected argv for direct and bound omission, duplicate-only update, cancelled update/status and `no_start`, including exact `--output json` placement and one canonical row per public method.
- [ ] 3.2 Add focused negative cases for blank references, non-cancelled status, present `None`/empty description, emitted attachments and conflicting upstream file/stdin contract vectors; assert zero transport/upload for SDK-owned conflicts.
- [ ] 3.3 Extend existing task-run response fixtures for target provider-quota and unknown future `failure_reason` strings without introducing an enum.
- [ ] 3.4 Extend issue/runtime usage fixtures for GPT-6.1 Sol, GPT-6 Sol and GPT-6 Luna server-supplied integer ticks and uncosted categories without copying price policy into production code.
- [ ] 3.5 Extend repository checkout compatibility cases for unchanged success shape, junction-safe target behavior and actionable containment/workdir failures through existing typed/redacted process errors.
- [ ] 3.6 Integrate contract/provenance/compatibility/public-inventory assertions proving exact 205/193/196 coverage, two adapted commands, nine/187 response verdicts and no new operation/model/fixture hierarchy.

## 4. Documentation and release gates

- [ ] 4.1 Update README and API, CLI coverage, compatibility, migration, contributing, service-usage and releasing guidance for direct `0.6.0 → 0.6.1`, duplicate transitions, compatibility interval, quota/usage/checkout semantics, exclusions and coherent rollback.
- [ ] 4.2 Run strict OpenSpec validation; approved-contract collect/validate/render/check; pinned source-link audit; focused unit/contract/component/compatibility suites; Ruff; mypy source/tests; full non-live pytest and collect-only; build, sdist, wheel, isolated import/package checks; and diff/Git/package forbidden-content audits.
- [ ] 4.3 Record exact commands and exit codes, deterministic clean rerender, live-not-run or explicit live result, and confirm no `.devlocal`, collector output, source checkout, archive, binary, transient render or visual HTML is tracked or packaged.

## 1. Approve the pinned trigger contract

- [ ] 1.1 Update `contracts/sdk-contract.json` trigger add/update signatures, mappings, response schema, compatibility rationale, five-state presence policies, normalized constraints, source refs to `multica-ai/multica@38c992ad0a757434fb51584fa34e3bc57d1b78e1`, and positive/negative test refs; remove add/update `title` and update `kind` entries.
- [ ] 1.2 Verify the CLI `0.4.38` release identity and `version --output json` source at full commit `47dc75741cd03127d32f1b78d04c644ccf690e7f`; store that full SHA in the existing verified-binary `commit` field, bind its test reference to the exact raw envelope commit `47dc75741` and remaining `version`/`date`/`go`/`os`/`arch` values, assert the short/full prefix relation, set `max_tested_cli_version` to `0.4.38`, and require generated exclusive maximum `0.4.39`.
- [ ] 1.3 Run `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout <pinned-v0.4.28-checkout>` and resolve every source or closed-schema error.
- [ ] 1.4 Render from the approved contract to the committed runtime target and an ignored transient directory, verify the transient provenance cites the pinned revision and the generated range is `[0.4.28, 0.4.39)`, and run `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` with no handwritten generated drift.

## 2. Implement the typed schedule surface

- [ ] 2.1 Change the existing compatibility preflight command arguments to `("version", "--output", "json")` with recursion disabled, retain global-argument ordering through `build_full_argv`, lazy first-operation execution, and the one-successful-probe cache shared by snapshot transports.
- [ ] 2.2 Change the existing shared version payload decoder to accept `version`, `commit`, `date`, `go`, `os`, and `arch`, map `date`/`go` to `CliVersion.build_date`/`go_version`, ignore additive keys, and fail closed for a missing, blank, non-semantic, wrong-typed, or malformed `version`; add no text fallback, legacy alias, or second decoder.
- [ ] 2.3 Replace `AutopilotTrigger` and `_AutopilotTriggerWire` legacy `type/config` fields with the specified common/schedule response fields and reuse the existing datetime decoding conventions for next-run, last-fired, created, and updated timestamps.
- [ ] 2.4 Implement the two exact direct add signatures specified in design and delta specs: `kind: str = "schedule"`; `cron_expression`, `timezone`, and `label: str | None = None`; `options: OperationOptions | None = None`; eager return `AutopilotTrigger`; command return `Command[AutopilotTrigger]`. Implement their argv construction, local kind/schedule/webhook validation, and add presence semantics.
- [ ] 2.5 Implement the two exact direct update signatures specified in design and delta specs: `cron_expression`, `timezone`, and `label: str | UnsetType = Unset`; `enabled: bool | UnsetType = Unset`; `options: OperationOptions | None = None`; eager return `AutopilotTrigger`; command return `Command[AutopilotTrigger]`. Emit lowercase inline boolean flags and reject explicit null or all-`Unset` calls before I/O.
- [ ] 2.6 Implement the corresponding four bound `Autopilot` eager/command signatures with the same annotations, defaults, order, keyword-only boundaries, and return types, differing only by absence of `autopilot_id`; preserve success-only trigger-relation invalidation and failure/cache behavior.

## 3. Extend existing table-driven verification

- [ ] 3.1 Replace trigger add/update canonical and variant rows in `tests/cases/operations.py`, update their literal current-case fingerprints/counts, and cover exact schedule argv for `*/30 * * * *`, `0 */3 * * *`, `Europe/Minsk`, label, omitted/empty strings, and both enabled values.
- [ ] 3.2 Extend existing autopilot relation/presence tables and shared-fixture tests for invalid kind, missing schedule cron, webhook cron/timezone conflicts, explicit update nulls, all-`Unset` update, direct/bound command parity, and zero transport calls on local failures.
- [ ] 3.3 Extend existing model/contract tests for the pinned schedule trigger response, timezone-aware timestamps, nullable fields, removal of `type/config`, approved mapping/provenance constraints, and deterministic generated output.
- [ ] 3.4 Extend existing runtime signature tables to assert parameter names/order, keyword-only boundaries, exact annotations/defaults, and exact eager/command return annotations for all eight direct/bound methods; update positive and negative typed fixtures so accepted calls infer `AutopilotTrigger` or `Command[AutopilotTrigger]` as specified and obsolete `title`/update `kind` arguments fail static checking.
- [ ] 3.5 Extend the existing compatibility parser and transport tables with the exact CLI `0.4.38` envelope and probe argv: assert all six public version fields, no executor call during construction, one `version --output json` preflight before the first governed call, configured global-argument order, shared snapshot caching, strict success through generated `<0.4.39`, and strict failure before the requested operation for every invalid-version case.

## 4. Document and prove the public lifecycle

- [ ] 4.1 Update README/API examples and `docs/migration.md` with the canonical schedule create/update calls, exact `title -> label` migration, delete-and-add guidance for kind changes, omitted/null/empty semantics, and the intentional alpha breaking correction.
- [ ] 4.2 Remove any temporary `CompatibilityPolicy.warn` or local max-version override from the consumer/live-smoke setup, retain `CompatibilityPolicy.strict` with generated bounds, and prove CLI `0.4.38` construction plus the first public SDK operation succeeds.
- [ ] 4.3 Extend the existing prepared-target live smoke to create a uniquely labelled `*/30 * * * *` schedule in `Europe/Minsk`, update it to `0 */3 * * *`, disable and re-enable it, assert returned typed fields, and delete it through the SDK in `finally`; update `tests/live/README.md` preparation notes with the required CLI `0.4.38` identity and strict policy.

## 5. Run release gates

- [ ] 5.1 Run `openspec validate support-autopilot-schedule-triggers --strict --json` and the focused trigger unit, contract, relation, type-fixture, and operation-case tests.
- [ ] 5.2 Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy src`, `uv run mypy tests`, `uv run pytest -m "not live"`, and `uv build`; record every command and exit code for review.
- [ ] 5.3 Inspect `git diff --check`, deterministic contract output, and the final tracked diff to confirm no dependency, raw CLI API, unrelated webhook operation, transient evidence, or out-of-scope file was added.

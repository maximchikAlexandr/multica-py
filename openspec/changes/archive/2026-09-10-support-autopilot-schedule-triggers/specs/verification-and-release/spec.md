## ADDED Requirements

### Requirement: Schedule trigger support is verified at every governed layer

Verification SHALL extend existing frozen dataclass case tables and shared fixtures to cover direct eager/command methods, bound eager/command methods, exact trigger and version-probe argv, local validation with zero transport calls, trigger and version-envelope decoding, relation invalidation, approved-contract source validation, deterministic generation, public documentation, and static typing. Offline tests SHALL cover the exact CLI `0.4.38` envelope, both required cron examples, `Europe/Minsk`, omitted/`None`/empty string semantics, both enabled booleans, both kinds on add, all-`Unset` update, and obsolete-parameter absence. No new test framework, duplicate helper, or one-case test file SHALL be added.

#### Scenario: Exact operation cases cover schedule lifecycle inputs
- **WHEN** canonical and variant operation rows run for trigger add and update
- **THEN** they assert complete argv including output, both cron examples, timezone, label, true/false enabled values, and every omitted or explicit-empty variant

#### Scenario: Negative cases perform no transport
- **WHEN** invalid kind, missing schedule cron, webhook schedule-only inputs, explicit update nulls, or an all-`Unset` update is attempted
- **THEN** the expected `TypeError` or `ValueError` is raised and the transport mock has zero calls

#### Scenario: Type checks cover every public form
- **WHEN** runtime signature tables inspect and typed fixtures call all eight direct and bound eager/command add/update methods
- **THEN** parameter names/order, keyword-only boundaries, exact annotations/defaults, and exact `AutopilotTrigger`/`Command[AutopilotTrigger]` returns match the `sdk-surface` signatures; accepted parameters and inferred returns type-check; obsolete `title`/update `kind` calls are rejected by the negative type fixture; and `mypy src` plus `mypy tests` pass

#### Scenario: Offline release gates stay green
- **WHEN** implementation is ready for review
- **THEN** strict change validation, approved-contract source validation/render/check, Ruff check and format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass without backend access

#### Scenario: Compatibility regression covers exact order and decoding
- **WHEN** existing compatibility parser and transport tables exercise strict mode with the exact CLI `0.4.38` version envelope
- **THEN** they assert zero construction I/O, command arguments `("version", "--output", "json")`, full argv with configured global arguments in order, every decoded public field, one shared successful probe, generated-bound acceptance, requested-operation execution, and fail-closed invalid-version cases

### Requirement: Prepared-target smoke proves schedule create and update

The gated live-smoke suite SHALL use only public SDK methods, the prepared profile/workspace, CLI `0.4.38`, and `CompatibilityPolicy.strict` with generated bounds. It SHALL NOT use `CompatibilityPolicy.warn` or a local max-version override. Construction SHALL remain I/O-free, and the first public SDK operation SHALL complete after the exact JSON compatibility preflight. The suite SHALL create one uniquely labelled schedule trigger on the prepared autopilot with cron `*/30 * * * *` and timezone `Europe/Minsk`, update it to cron `0 */3 * * *`, set `enabled=False` and then `enabled=True`, verify returned typed fields after each mutation, and delete the created trigger in `finally`. It SHALL NOT invoke `multica` directly or issue HTTP requests.

#### Scenario: Strict prepared client initializes successfully
- **WHEN** the prepared client is constructed with CLI `0.4.38` and `CompatibilityPolicy.strict`, then its first public SDK operation runs
- **THEN** the JSON version preflight accepts generated bounds, the operation succeeds, and neither the consumer nor live-smoke fixture contains a warning-policy or local-bound workaround

#### Scenario: Live schedule lifecycle succeeds
- **WHEN** the prepared-target live smoke runs with all required environment values
- **THEN** the public SDK creates, updates, disables, re-enables, verifies, and deletes the test-owned trigger without a raw CLI escape hatch

#### Scenario: Live cleanup runs after failure
- **WHEN** any assertion after trigger creation fails
- **THEN** `finally` still calls the public SDK trigger-delete method for the recorded trigger ID before propagating the failure

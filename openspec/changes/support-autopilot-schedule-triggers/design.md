## Context

`multica-py` targets Multica CLI `v0.4.28` at commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`. At that source revision, `autopilot trigger-add` exposes `--kind`, `--cron`, `--timezone`, and `--label`; `autopilot trigger-update` exposes presence-sensitive `--enabled`, `--cron`, `--timezone`, and `--label`. The SDK contract instead maps `--title` and mutable `--kind`, and its trigger wire model expects legacy `type/config` output. The defect crosses the approved contract, generated binding, direct and bound methods, decoding, tests, and documentation.

The prepared consumer uses CLI `0.4.38`, whose release source resolves to commit `47dc75741cd03127d32f1b78d04c644ccf690e7f`. That binary returns `{"arch":"arm64","commit":"47dc75741","date":"2026-09-02T09:52:29Z","go":"go1.26.7","os":"darwin","version":"0.4.38"}` from `multica version --output json`; JSON object ordering is not contractual. Compatibility preflight currently runs `multica version` without the output flag and its decoder expects `buildDate`/`goVersion`; strict mode therefore fails before the first governed operation. Even after parsing is corrected, the generated exclusive maximum `0.4.33` would reject `0.4.38`, so binary provenance and the reviewed compatibility interval must advance together without changing the pinned source target for trigger mappings.

The CLI remains the only transport. The approved contract remains the only generator input. Public methods continue to offer eager and `*_command()` forms and bound `Autopilot` delegates. No direct HTTP path or request DTO is introduced.

## Goals / Non-Goals

**Goals:**

- Make schedule creation and updates expressible with explicit typed parameters and exact pinned-CLI argv.
- Specify every omitted, `None`, empty-string, and boolean presence state that the accepted parameter type can represent.
- Reject locally decidable invalid combinations before transport and rely on the governed CLI/server for target-kind validation that cannot be known without a read.
- Decode the pinned trigger response into an immutable typed model and preserve successful bound-relation invalidation.
- Make a strict client accept the exact CLI `0.4.38` JSON version envelope once, immediately before its first governed transport operation, while keeping client construction I/O-free.
- Extend generated compatibility through verified CLI `0.4.38` and remove the temporary warning-policy workaround from consumer/live-smoke configuration.
- Keep the change deterministic, table-driven, documented, and covered by offline gates plus one prepared-target live lifecycle.

**Non-Goals:**

- Adding trigger list, webhook rotation, webhook provider/filter, signing-secret, or direct HTTP operations.
- Parsing cron expressions or loading the IANA timezone database in the SDK.
- Claiming response-field compatibility for `0.4.38` operations that are not exercised or source-reviewed by this change.
- Adding eager version I/O to `MulticaClient` construction or a second compatibility/version decoder.
- Preserving obsolete trigger parameters that never worked against the pinned CLI.

## Decisions

### 1. Mirror the pinned CLI with direct parameters

The exact direct resource signatures are:

```python
def trigger_add(
    self,
    autopilot_id: str,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_add_command(
    self,
    autopilot_id: str,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...

def trigger_update(
    self,
    autopilot_id: str,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_update_command(
    self,
    autopilot_id: str,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...
```

The exact bound `Autopilot` signatures differ only by removal of `autopilot_id`:

```python
def trigger_add(
    self,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_add_command(
    self,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...

def trigger_update(
    self,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_update_command(
    self,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...
```

Update does not accept `kind`. Eager and command forms have identical operation parameters and differ only in their exact return annotation.

This reuses the repository's direct-parameter and `Unset` conventions. A new request DTO was rejected because the SDK has already removed one-operation DTOs. A new enum was rejected because the existing public `kind: str` input can be preserved while a two-value runtime validator supplies the closed operation constraint with fewer public symbols.

### 2. Correct obsolete compatibility at the documented alpha boundary

`title` is removed from add/update and `kind` is removed from update. They are not aliases: mapping `title` to `label` would invent semantics absent from the approved source, while silently accepting update `kind` would imply a mutation the CLI cannot perform. Existing valid `kind="schedule"` and `kind="webhook"` add calls remain accepted; autopilot and trigger identifiers, keyword-only layout, `options`, eager/command forms, and bound method names remain unchanged.

The migration guide provides mechanical replacements: `title=x` becomes `label=x`; an attempted kind change becomes delete-and-add with the desired kind. This is an intentional alpha API correction, not a compatibility shim.

### 3. Encode source presence semantics without speculative parsing

Add treats omitted/`None`/empty `timezone` and `label` as omitted because the upstream add handler does the same. A schedule requires a nonempty `cron_expression`; a webhook requires `cron_expression` and `timezone` to be omitted, `None`, or empty. `kind=None` is a type error, empty kind follows upstream normalization to `schedule`, and any other unknown kind is a value error. Nonempty cron/timezone/label values are passed verbatim for upstream semantic validation.

Update distinguishes omission with `Unset`. `None` is rejected for every update field. Empty strings are emitted for cron, timezone, and label because `Flags().Changed` forwards them in PATCH; empty timezone restores the server's UTC default and empty label clears the label. Both boolean values are emitted as one argv token, `--enabled=true` or `--enabled=false`. An all-`Unset` update raises `ValueError` without the current fallback GET. Since a direct update does not know the persisted trigger kind, schedule-only cron/timezone checks remain the governed CLI/server's responsibility; adding a preflight read was rejected because it adds a race and an unnecessary subprocess.

### 4. Replace the legacy trigger projection with the pinned response

`AutopilotTrigger` and its private wire model represent the pinned common and schedule response fields: `id`, `autopilot_id`, `kind`, `enabled`, nullable `cron_expression`, `timezone`, `next_run_at`, `label`, and `last_fired_at`, plus `created_at` and `updated_at`. RFC3339 timestamps decode with the repository's existing datetime adapter. Legacy `type` and tuple `config` are removed because they are not emitted by the pinned command. Webhook-only secret, provider, signing, and event-filter fields remain out of this schedule-focused projection and are ignored by the wire decoder.

No schedule-specific subtype is added. One immutable trigger model matches add, update, get-envelope, and relation results and avoids parallel decode paths.

### 5. Promote through the approved contract and existing test tables

The implementer updates `contracts/sdk-contract.json` with pinned source locations, mappings, five-state presence, normalized constraints, response fields, compatibility rationale, and test refs, then regenerates `src/multica_py/_generated/approved_sdk.py` through `scripts/upstream_contract.py render`. Operation rows and legacy fingerprints are updated in place; no handwritten generated edit or parallel manifest is allowed.

Tests extend existing frozen dataclass tables and shared fixtures for exact argv, invalid inputs, result decoding, eager/command/bound signature parity, cache behavior, contract generation, docs, and mypy. A prepared-target live smoke creates one uniquely identifiable schedule trigger, updates it from `*/30 * * * *` to `0 */3 * * *` in `Europe/Minsk`, exercises both enabled values, and deletes it in cleanup through the public SDK.

### 6. Repair the existing lazy version preflight instead of adding a path

For every non-`ignore` compatibility policy, `_check_compat` invokes the existing transport executor with command arguments `("version", "--output", "json")` and `check_compat=False`. `build_full_argv` remains authoritative, so the default full argv is exactly `("multica", "version", "--output", "json")`; configured global arguments remain in their existing fixed position between the executable and `version`. Construction performs no subprocess I/O. The first governed SDK operation performs the probe, a successful shared compatibility state prevents repeats for the original and snapshot transports, and the requested operation then proceeds.

The single existing version payload decoder accepts the CLI keys `version`, `commit`, `date`, `go`, `os`, and `arch`, ignores additive unknown keys, and maps `date` and `go` to the existing public `build_date` and `go_version` attributes. A missing, blank, non-semantic, wrong-typed, or malformed `version` does not become `0.0.0`; strict mode raises the existing `UnsupportedCliVersionError` before the requested operation. No fallback to text parsing or legacy camel-case aliases is added because the governed CLI command explicitly requests the reviewed JSON schema.

The approved contract retains target `v0.4.28` for trigger source mappings and follows the existing verified-binary schema for CLI `0.4.38`: its `commit` field stores resolved full release-source SHA `47dc75741cd03127d32f1b78d04c644ccf690e7f`, while its test reference uses the exact raw envelope commit `47dc75741`; the prefix relation between them is asserted. The remaining identity is build date `2026-09-02T09:52:29Z`, Go `go1.26.7`, Darwin, arm64. Its maximum-tested version becomes `0.4.38`, producing exclusive `MAX_CLI_VERSION = "0.4.39"`. Strict consumer/live-smoke configuration uses those generated defaults; it must not set `CompatibilityPolicy.warn` or a local max-version override.

## Risks / Trade-offs

- [Removing obsolete parameters breaks source compatibility for callers that referenced them] → Document exact replacements and classify the correction as breaking in the alpha migration guide.
- [Update kind-specific errors cannot all be detected locally] → Validate every state known from arguments locally and preserve the CLI/server's authoritative typed failure without a racy preflight read.
- [Empty cron can make a schedule ineffective even though pinned upstream accepts it on update] → Preserve upstream behavior instead of inventing SDK-only validation; cover the exact emitted empty value as a presence contract.
- [Live smoke can leave a trigger after an assertion failure] → Record the created trigger ID immediately and delete it in `finally` through the SDK.
- [Contract and generated output can drift] → Require source validation, deterministic render/check, and a clean regeneration diff before commit.
- [Accepting the envelope but retaining the old generated maximum still breaks strict clients] → Promote the verified `0.4.38` binary record and exclusive `0.4.39` bound in the same contract/render change.
- [Duplicated version decoding can drift between preflight and maintenance APIs] → Correct the existing shared payload decoder and cover its public-field mapping; do not introduce a second decoder.
- [A compatibility fix could accidentally make construction perform I/O or probe on every snapshot] → Assert no executor call at construction, one exact probe before the first operation, and reuse of the successful shared compatibility state.

## Migration Plan

1. Update and validate the reviewed trigger mappings against pinned upstream commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`; separately verify and record the CLI `0.4.38` binary/version-command provenance.
2. Regenerate the approved runtime projection, then repair the existing compatibility probe/decoder and update resource/entity/model code, existing case tables, docs, and live smoke.
3. Remove the temporary warning-policy workaround, confirm strict construction plus the first governed operation against `0.4.38`, and retain strict generated defaults in consumer/live-smoke configuration.
4. Run strict OpenSpec validation and the repository's contract, lint, type, offline test, and package gates before review.
5. Release as an intentional alpha API correction. Rollback is a normal commit revert of the contract and implementation; no persisted SDK state or server migration is involved.

## Open Questions

None.

## Why

The governed `trigger_add` and `trigger_update` SDK methods describe obsolete `--title`/`--kind` flags instead of the pinned Multica CLI's schedule fields, so consumers cannot create or modify a schedule trigger through the typed SDK and successful CLI responses do not match the public trigger model. In addition, strict compatibility preflight invokes the CLI's text version command and decodes obsolete camel-case keys, while CLI `0.4.38` emits a JSON envelope only when requested and names its metadata keys `date` and `go`. The approved contract and handwritten compatibility path must be corrected together so schedule automation works through a strict typed client without a raw CLI escape hatch or a warning-policy workaround.

## What Changes

- Replace the obsolete trigger mutation mappings with the pinned CLI's `kind`, `cron_expression`, `timezone`, `label`, and `enabled` inputs and exact `--kind`, `--cron`, `--timezone`, `--label`, and `--enabled=<bool>` argv.
- Define creation and patch presence semantics, schedule/webhook-specific validation, nonempty-update validation, and timezone/cron handling before transport I/O.
- Align `AutopilotTrigger` decoding with the upstream trigger response and preserve the same mutation surface on direct resource methods, command builders, and bound `Autopilot` methods with successful cache invalidation.
- Make the lazy compatibility preflight invoke `multica version --output json`, decode the exact CLI `0.4.38` envelope, and map `date`/`go` into the existing `CliVersion.build_date`/`go_version` fields.
- Record the verified CLI `0.4.38` binary separately from the pinned `v0.4.28` source target, extend generated strict compatibility through `0.4.38` with exclusive maximum `0.4.39`, and remove the temporary `CompatibilityPolicy.warn` consumer/live-smoke workaround.
- Update the approved contract, deterministic generated binding, operation tables, provenance, public docs, migration guidance, and offline/live verification for schedule creation and updates.
- **BREAKING**: remove the unsupported `title` trigger input and remove `kind` from trigger updates; the pinned CLI has no such flags, and trigger kind is immutable after creation. `kind` remains a create input and accepts the existing `"schedule"`/`"webhook"` values.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `autopilot-resource`: Correct trigger mutation signatures, validation, result models, and schedule behavior.
- `sdk-surface`: Keep direct, command, and bound typed APIs aligned, and restore lazy strict-client startup against the exact CLI `0.4.38` version envelope.
- `bound-resource-relations`: Preserve exact trigger-relation invalidation across the expanded bound mutation methods.
- `upstream-contract`: Record reviewed pinned-source mappings, presence semantics, constraints, response provenance, verified `0.4.38` binary metadata, and deterministic generated bindings.
- `verification-and-release`: Require table-driven unit/contract/type/live-smoke coverage for exact schedule trigger behavior, the version probe, strict initialization, and workaround removal.

## Impact

The implementation will update the approved SDK contract and generated runtime binding, compatibility transport/parser, autopilot resource/entity signatures, the public trigger model and wire decoder, operation and relation test tables, consumer/live-smoke setup and cleanup, and API/migration documentation. It adds no dependency, no eager constructor I/O, no raw CLI API, no new resource abstraction, and no unrelated webhook-management operations.

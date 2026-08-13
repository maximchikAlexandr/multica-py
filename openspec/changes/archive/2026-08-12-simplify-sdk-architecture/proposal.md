## Why

The SDK currently encodes several policies twice: option overlays, bound-entity field classification, relation load state, command-plan composition, and approved-operation argv construction. That duplication makes a behavior-preserving change span generated data, resources, relation internals, and test catalogs; this change reduces those ownership seams while retaining the repository's exact command and lifecycle contracts.

## Starting Revision

The immutable behavior baseline is `e719de13442841c64ed96855c5227bbe5e173f10`. The current planning commit is `2ff0fd954851b9125ea3adba39696c00a57e8eab`; its parent and merge-base with the pinned baseline are the baseline commit. The planning commit is intentionally part of the starting tree, so implementation begins at that commit or a plan-only descendant, while every baseline comparison and phase gate uses the pinned baseline as its reference. No gate requires the implementation checkout's `HEAD` to equal the baseline.

## What Changes

- Remove confirmed dead or migration-only code: legacy-ID maps, test-only compatibility helpers/models, the unused executable resolver/warning, and the redundant workflow keep-file, while retaining independent current-case payload fingerprints and runtime compatibility/error behavior.
- Centralize `OperationOptions` overlay application in one private config-level function used by scoped clients and command snapshots.
- Derive bound-entity public, runtime, and constructor-seed field classes from msgspec declarations, retaining only the proven public runtime-overlay exceptions for `AutopilotRun.trigger_payload` and `result`.
- Share the generation/coalescing state machine used by lazy collections and mappings without merging their container-specific values or metadata.
- Move cached-command, coalescing-wrapper, result-reference, step-alias, and sequential-continuation transformations behind the private command module so relation code no longer reads or reconstructs `_CommandPlan` or `_Step` internals.
- Pilot contract-generated private builders and validators for the homogeneous `squad member list/add/remove` family. Expansion to any other marker-only family is allowed only after recorded stop/go evidence proves unchanged public contracts and a measurable net reduction; otherwise the pilot is reverted or remains the only generated family.
- Reassess bound-relation lifecycle duplication only after the entity, relation-state, and command-composition phases. Any follow-up is limited to one separately approved relation pilot.
- Preserve all public eager methods and typed `*_command() -> Command[T]` siblings, exact argv, validation timing, previews, redaction, configuration snapshots, transport/process behavior, entity semantics, and relation cache/pagination behavior. No new runtime or test dependency is introduced.

## Capabilities

### New Capabilities

- `bound-entity-field-policy`: Defines schema-derived classification of serialized fields, private runtime state, constructor seeds, and the narrow public runtime-overlay exception.

### Modified Capabilities

- `subprocess-transport`: Makes one option-overlay implementation authoritative while preserving command snapshots, semaphore sharing, compatibility checks, and executable error mapping.
- `bound-resource-relations`: Requires collection and mapping loaders to share one transition/coalescing implementation and requires relation composition to use command-module transformations rather than command-plan internals.
- `upstream-contract`: Adds the bounded `squad member` generated-builder pilot and explicit evidence gates for any expansion.
- `verification-and-release`: Replaces legacy-ID migration assertions with independent fingerprints keyed by current canonical case IDs and adds phase-by-phase preservation and stop/go gates.

## Impact

The change affects private configuration helpers, bound-entity internals, relation and command-plan internals, the approved-contract generator and generated module, operation/fingerprint fixtures, compatibility/executable cleanup, and their focused tests. Public Python signatures, return types, CLI behavior, dependencies, and documented usage remain unchanged. Implementation is intentionally staged so each phase can be validated and committed independently before later architectural work proceeds.

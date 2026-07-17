# Contract: Maintainer Commands

## Unified Entry Point

Maintainer workflows are exposed through one thin command adapter:

```text
python scripts/upstream_contract.py observe
python scripts/upstream_contract.py collect --binary PATH --output candidate.json
python scripts/upstream_contract.py diff --from supported.json --to candidate.json
python scripts/upstream_contract.py check --format human
python scripts/upstream_contract.py check --format json --output report.json
python scripts/upstream_contract.py prepare-upgrade --candidate candidate.json --output-dir artifacts/upstream-upgrades/...
python scripts/upstream_contract.py apply-manifest-suggestions --bundle artifacts/upstream-upgrades/...
python scripts/upstream_contract.py promote --candidate candidate.json --decision promotion.json
python scripts/upstream_contract.py reject --candidate candidate.json --decision rejection.json
```

Compatibility wrappers may preserve older script names, but domain behavior
lives in the upstream-contract modules.

## Modes

- `--check`: validates canonical state and never writes files.
- `--write`: atomically writes the selected artifact.
- `--dry-run`: prints planned file changes or patch content.
- `--format human|json`: selects presentation of the same report model.
- `--output PATH`: writes machine output to a destination.

## Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Clean or compatible |
| `2` | Coverage or compatibility gaps |
| `3` | Invalid artifact, schema, or provenance |
| `4` | Collector unavailable, timeout, or incomplete inventory |
| `5` | Source/binary contract mismatch |
| `6` | Candidate exists but contains unresolved breaking changes |
| `64` | Invalid CLI usage |

## Coverage Check

Required behavior:

- Reads checked-in supported artifacts by default.
- Exits successfully only when upstream contract and SDK coverage decisions are complete.
- Does not fail solely because an explicitly unsupported row has no SDK method.
- Renders human output from the machine-readable CoverageReport.
- Fails closed on invalid schema, partial inventory, or unresolved breaking changes.

## Inventory and Contract Collection

Required behavior:

- Accepts a selected executable or verified release asset and assigns trust
  level using `implementation-oracles.md`.
- Records release version, tag, full source commit, binary digest, platform, and collection method.
- Produces deterministic canonical contract output.
- Fails when full source commit cannot be determined for checked-in candidate or supported artifacts.
- Does not modify SDK coverage decisions automatically.

## Diff

Required behavior:

- Compares supported and candidate semantic contracts.
- Reports command, argument, flag, default, alias, deprecation, execution, output, documentation-only, and provenance-only changes.
- Treats possible renames/moves as suggestions requiring maintainer confirmation.
- Links each non-documentation change to affected SDK operations or an unresolved mapping state.

## Upgrade Preparation

Required behavior:

- Generates the deterministic local upgrade bundle layout defined in
  `upgrade-bundle.md`.
- Emits incomplete manifest suggestions and test/task suggestions for missing or changed coverage.
- Does not make generated suggestions pass the coverage gate.
- Separates generated facts from maintainer decisions.

## Applying Manifest Suggestions

Required behavior:

- Applying suggestions is a separate explicit command, never an implicit side effect.
- Applied rows remain `coverage_level=incomplete` until maintainer fills required decisions.
- Applying suggestions does not make the coverage gate pass by itself.
- The command must be idempotent for an unchanged bundle.

## Promotion Decisions

Required behavior:

- Promotion is a separate explicit command, never an implicit side effect of
  collection, observation, diffing, or upgrade preparation.
- Promotion requires a PromotionDecision artifact with candidate version, tag,
  full commit, semantic hash, previous supported baseline, clean offline gate
  evidence, reviewer identity or review reference, and explicit resolution for
  breaking or potentially breaking changes.
- Rejecting a candidate is explicit and records why the candidate remains
  unsupported or superseded.
- Promotion is refused when provenance is incomplete, checked-in artifacts are
  invalid, offline gates fail, or unresolved breaking changes remain.
- Promotion writes supported state atomically; failed writes leave the previous
  supported baseline intact.

## Raw Coverage Safety

Required behavior:

- Raw access accepts only a sequence of arguments.
- Raw access never uses shell interpolation.
- Raw access is reported separately from typed coverage.
- Raw access does not imply stable typed public support.

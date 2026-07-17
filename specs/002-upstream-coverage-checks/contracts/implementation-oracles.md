# Contract: Implementation Oracles

This file is the tie-breaker for implementation choices. When another artifact
uses broad wording, the tables below define the exact expected behavior.

## Artifact Locations

| Artifact | Required path | Written by | May be committed | Notes |
|---|---|---|---|---|
| Upstream state | `src/multica_py/_generated/upstream_state.json` | `check`, `collect --write`, `observe`, `promote`, `reject` | Yes | Blocking CI reads only `supported` from this file. |
| Supported contract | `src/multica_py/_generated/upstream_supported_contract.json` | `promote` | Yes | Must validate against `contracts/schema/upstream-contract-v2.schema.json`. |
| Candidate contract | `artifacts/upstream-upgrades/<from>..<to>/candidate-contract.json` | `collect`, `prepare-upgrade`, `observe` | Optional review artifact | Never becomes supported without `promote`. |
| Approved SDK contract | `contracts/sdk-contract.yaml` | Maintainer edit or explicit apply command | Yes | Only approved generator input. Raw source evidence is not generator input. |
| Source evidence | `artifacts/upstream-upgrades/<from>..<to>/source-evidence.json` | source collector | Optional review artifact | Evidence and review items only. |
| Machine report | explicit `--output PATH` only | any command with `--format json` | No by default | `--check` must not write this unless `--output` is set. |
| JSON Schema | `contracts/schema/upstream-contract-v2.schema.json`, `contracts/schema/upstream-report-v1.schema.json` | schema task | Yes | Schema drift fails CI unless generated model changes are intentional. |

## Maintainer Commands

| Command | Writes by default | Allowed network | Success exit | Failure exits |
|---|---:|---:|---:|---|
| `check --format human` | No | No | `0` | `2`, `3`, `6`, `64` |
| `check --format json --output PATH` | Only `PATH` | No | `0` | `2`, `3`, `6`, `64` |
| `collect --binary PATH --output PATH` | Only `PATH` | No | `0` | `3`, `4`, `5`, `64` |
| `diff --from A --to B --format human` | No | No | `0` for compatible/provenance/doc-only/additive | `2`, `3`, `6`, `64` |
| `prepare-upgrade --candidate C --output-dir D` | Yes, `D` | No | `0` | `2`, `3`, `6`, `64` |
| `apply-manifest-suggestions --bundle D` | Yes | No | `0` | `3`, `64` |
| `observe --dry-run` | No | Yes | `0` | `3`, `4`, `5`, `64` |
| `observe --write` | Candidate artifacts only | Yes | `0` | `3`, `4`, `5`, `64` |
| `promote --candidate C --decision D` | Supported state and supported contract | No | `0` | `2`, `3`, `6`, `64` |
| `reject --candidate C --decision D` | Upstream state only | No | `0` | `3`, `64` |

## Human Summary Oracle

The first non-empty lines of `check --format human` must use this order and
field set:

```text
Multica upstream coverage: <clean|gaps|invalid|unresolved-breaking>
Supported: version=<version> tag=<tag-or-none> commit=<40-char-sha> semantic_hash=<sha256:...>
Inventory: commands=<n> manifest_rows=<n> typed=<n> raw=<n> process=<n> unsupported=<n> legacy=<n> incomplete=<n>
Failures: total=<n> coverage=<n> invalid=<n> unresolved_breaking=<n>
```

Acceptance oracle:

- SC-001 passes when these four lines are present before any detailed command
  list and the offline command returns within 30 seconds on the checked-in
  fixture set.
- Automation must assert the exact field names and order above.
- Additional detail lines are allowed only after `Failures:`.

## Collector Method Order

Collection must attempt methods in this fixed order unless the user explicitly
selects one method with a command flag:

1. Release asset contract: `multica-cli-contract.json`.
2. Binary exporter: `multica __contract --format json`.
3. Go helper/exporter built or run against the pinned full source commit.
4. Help parser fallback.

The first successful method becomes `collection_method`. Later methods may be
used only for cross-checking and must not replace a higher-priority successful
method.

## Trust Levels and Promotion Eligibility

| Trust level | Evidence required | Promotion eligible | Required status behavior |
|---|---|---:|---|
| `verified` | Release asset or binary exporter agrees with source evidence, full commit, checksum, schema validation | Yes | Normal candidate. |
| `release-binary` | Official asset checksum and full commit, no source cross-check | No | Candidate can be reviewed but promotion fails with exit `3`. |
| `source-only` | Full source commit and source evidence, no verified executable | No | Candidate can support review only; promotion fails with exit `3`. |
| `local-manual` | User-selected local binary plus full commit, no official checksum | No | Must not be checked in as supported. |
| `help-degraded` | Help parser output only or missing hidden/deprecated/inherited metadata | No | Must contain review items and promotion-blocking status. |
| `mismatch` | Exporter/source/help disagreement on semantic fields | No | Command exits `5`; report failure code `CONTRACT_SOURCE_MISMATCH`. |

## State Transition Oracle

| Current state | Event | New state | Allowed? | Notes |
|---|---|---|---:|---|
| supported only | observe newer release | supported + observed | Yes | Does not change supported contract. |
| supported + observed | collect candidate | supported + observed + candidate | Yes | Candidate must include trust level. |
| supported + candidate | prepare upgrade | unchanged state | Yes | Writes bundle only. |
| supported + candidate | promote verified clean candidate | supported replaced, observed optional, candidate cleared | Yes | Requires PromotionDecision. |
| supported + candidate | reject candidate | supported unchanged, candidate marked rejected or cleared | Yes | Requires rejection decision. |
| supported + candidate | observe newer release | supported + observed newer + candidate superseded | Yes | Older candidate cannot be promoted. |
| any | collect/observe failure | previous state unchanged | Yes | Temporary artifacts must be invalid or removed. |
| any | scheduled observer promotes | n/a | No | Must never happen. |
| candidate with non-verified trust | promote | n/a | No | Exit `3`. |
| candidate with unresolved breaking changes | promote | n/a | No | Exit `6`. |

## Diff Severity Oracle

| Change | Severity | Blocks promotion | Required action |
|---|---|---:|---|
| Same semantic hash, provenance changed | `provenance_only` | No | Record provenance. |
| Help/description text only | `doc_only` | No | Optional docs review. |
| New command | `additive` | No | Create incomplete manifest suggestion. |
| New optional flag | `additive` | No | Create typed-contract review item. |
| New required argument or flag | `breaking` | Yes | Resolve SDK input contract or reject. |
| Removed command | `breaking` | Yes | Resolve legacy/unsupported binding or reject. |
| Removed flag | `breaking` | Yes | Resolve SDK input contract or reject. |
| Flag or argument type changed | `breaking` | Yes | Resolve SDK input contract or reject. |
| Enum widened | `potentially_breaking` | Yes | Maintainer approves strict/open enum policy. |
| Enum narrowed | `breaking` | Yes | Resolve enum policy and tests. |
| Default value changed | `potentially_breaking` | Yes | Maintainer accepts or maps explicit value. |
| Alias added | `additive` | No | Add binding or review item. |
| Alias removed while canonical command remains | `potentially_breaking` | Yes | Resolve legacy binding impact. |
| Command hidden -> visible | `additive` | No | Create review item. |
| Command visible -> hidden | `potentially_breaking` | Yes | Resolve whether SDK keeps support. |
| Deprecation added | `potentially_breaking` | Yes | Add compatibility note or reject. |
| Output optional field added | `additive` | No | Fixture update if decoder permits extras. |
| Output field removed or type changed | `breaking` | Yes | Decoder/model resolution required. |
| Source/exporter/help mismatch | `mismatch` | Yes | Exit `5`; not an SDK coverage gap. |

## Decoder Policy Oracle

| Policy | Unknown fields | Missing optional field | Missing required field | Type changed field |
|---|---|---|---|---|
| `strict` | Fail negative fixture | Pass only if field is optional in model | Fail | Fail |
| `permissive-extra-fields` | Pass and ignore | Pass only if field is optional in model | Fail | Fail |
| `text-only` | Not applicable | Not applicable | Not applicable | Not applicable |
| `custom` | Requires named decoder and positive/negative fixtures | Requires explicit fixture | Requires explicit fixture | Requires explicit fixture |

## Acceptance Fixture Matrix

| Success criterion | Required fixture/test oracle |
|---|---|
| SC-001 | `test_upstream_contract_check.py` asserts four-line human summary order and runtime budget. |
| SC-002 | Fixture with one missing command asserts exact command appears in coverage failure list. |
| SC-003 | Fixture with unsupported row and reason asserts no missing SDK mapping failure. |
| SC-004 | Collection fixture asserts version, tag, full commit, digest, platform, semantic hash. |
| SC-005 | Missing command fixture asserts generated rows are `coverage_level=incomplete`. |
| SC-006 | Required argument mutation asserts `breaking` and promotion exit `6`. |
| SC-007 | Help-only mutation asserts `doc_only` and no compatibility failure. |
| SC-008 | Same-input collection writes byte-identical canonical contract excluding observation metadata. |
| SC-009 | Timeout/partial fixture exits `4` and cannot write complete contract. |
| SC-010 | Observer fixture updates observed/candidate only, never supported. |
| SC-011 | Mutation set asserts each semantic change appears once with affected operation or unresolved marker. |
| SC-012 | Typed row fixture resolves SDK method, argv test ref, and output contract or non-structured policy. |
| SC-013 | Two prepare-upgrade runs produce no diff in output directory and no duplicate tracking identity. |
| SC-014 | Checksum mismatch fixture exits before binary execution. |
| SC-015 | Diff report includes exactly one of provenance-only/additive/potentially-breaking/breaking summary outcomes. |
| SC-016 | Raw row fixture appears only in raw counts/docs, never typed counts. |
| SC-017 | Exporter/help mismatch exits `5` and uses failure code `CONTRACT_SOURCE_MISMATCH`. |
| SC-018 | Runtime compatibility fixture warns once per client and documents override path. |

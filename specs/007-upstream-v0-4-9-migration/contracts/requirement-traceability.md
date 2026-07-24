# Contract: Requirement Traceability

This matrix is binding. The implementation task list must preserve every row;
no requirement may be treated as implied by another row.

## Functional Requirements

| Requirement | Implementation authority | Acceptance evidence |
| --- | --- | --- |
| FR-001 | schema-v2 `target`; exact provenance contract | coherence validator exact baseline/target identity |
| FR-002 | operation decisions matrix | Gate A counts 16 outcomes |
| FR-003 | `ApprovedOperation` closed fields | schema validation of rationale, binding, source, I/O, tests |
| FR-004 | 15 compatible rows | generated cases plus focused offline/live operation evidence |
| FR-005 | `issues.comments.list` intentional row | public signature/argv/cursor tests and generated compatibility projection |
| FR-006 | unsupported outcome validator | Gate A proves zero feature-007 unsupported rows; validator test covers deliberate unsupported shape |
| FR-007 | status rows bind only `status` | argv rows and coherence binding comparison |
| FR-008 | `ParameterMapping` plus exact `SourceRef` | schema/source-ref validation for every changed mapping |
| FR-009 | closed `Destination` | schema rejects missing/multiple/unknown destination |
| FR-010 | `local_control` destination | description file/stdin and path normalization mapping tests |
| FR-011 | five-key `PresenceContract` | generated presence cases plus project/comment focused tests |
| FR-012 | `Unset` versus null/empty | project model and argv cases |
| FR-013 | closed `Constraint` with both test-ref lists | schema validation plus positive/negative cases |
| FR-014 | `EnumContract` | strict issue sort/direction/status tests; aliases/deprecations explicit |
| FR-015 | 16 operation matrix | Gate A exact-set assertion |
| FR-016 | `ErrorContract` and timeout decision | transport/process-contract tests |
| FR-017 | generator accepts approved contract only | CLI negative tests and generated hash projection |
| FR-018 | reject evidence/candidate/suggestion inputs | generator CLI negative tests |
| FR-019 | family disposition/removal rule | coherence asserts no help-only removal decision |
| FR-020 | scope exact set | coherence asserts no 35-addition promotion |
| FR-021 | schema scope validator | unknown/new ID rejection test |
| FR-022 | family disposition table | exact 11-row count test |
| FR-023 | workspace repo boundary row | contract/coherence negative fixture |
| FR-024 | out-of-scope family rows | exact family disposition test |
| FR-025 | `ApprovedTarget` and provenance contract | provenance checksum/digest test |
| FR-026 | promotion/state history | state/promotion tests retain previous identity |
| FR-027 | coherence validator | one exact-target cross-artifact test |
| FR-028 | canonical state refs and hashes | state dangling/wrong-kind/wrong-hash negative tests |
| FR-029 | generated cases and offline suites | complete `pytest -m "not live"` |
| FR-030 | Phase E offline commands | Ruff, mypy, pytest, architecture/baseline gates |
| FR-031 | `LiveOutcome` categories/stages | live-outcome unit tests and smoke/extended reports |
| FR-032 | comparison fingerprint rule | shared baseline/candidate failure unit case |
| FR-033 | reachability field/rule | unreached-operation outcome test |
| FR-034 | fail-closed mutation protocol | missing-pytest/JUnit/collection cases return 2 |
| FR-035 | exact clean/mutated node protocol | three mutation cases with expected fingerprints |
| FR-036 | repeat prerequisite | missing/non-passed/wrong-target report cases |
| FR-037 | repeat exactly 10 full smoke | stability report 10/10 assertion |
| FR-038 | outcome cleanup and redaction fields | cleanup/secret-scan assertions per live run |
| FR-039 | required final baseline inputs | three missing/unreadable input tests |
| FR-040 | this matrix plus contract refs | traceability completeness guard |

## Backward Compatibility Requirements

| Requirement | Binding evidence |
| --- | --- |
| BC-001 | schema scope and operation decisions contain exactly 16 IDs |
| BC-002 | compatible rows and intentional comment-list row exhaust all IDs |
| BC-003 | complete presence contracts and generated argv cases |
| BC-004 | response/error contracts and malformed-output/error tests |
| BC-005 | exact command bindings plus family boundary negative tests |
| BC-006 | no fallback/probe rules and fail-closed validators |

## Success Criteria

| Criterion | Passing evidence |
| --- | --- |
| SC-001 | Gate A: 16/16 classified, zero unknown |
| SC-002 | schema validator: every changed operation has behavior/source/destination/tests |
| SC-003 | all applicable presence states encoded and covered |
| SC-004 | every changed constraint has positive and negative refs |
| SC-005 | coherence validator reports zero contradictions |
| SC-006 | full offline quality passes on supported CI matrix |
| SC-007 | smoke and extended are passed with zero uncategorized failures |
| SC-008 | all three mutation controls and mutations start; exit 0 |
| SC-009 | stability result is 10/10 against one fingerprint |
| SC-010 | 11 families classified and zero implicit new IDs |
| SC-011 | zero help-only removals approved |
| SC-012 | every live report has green cleanup and redacted diagnostics |

## Completeness Guard

## Execution Requirements

| Requirement | Passing evidence |
| --- | --- |
| ET-001 | source preflight and source-ref validation precede generation |
| ET-002 | seed byte equality and semantic-hash guard |
| ET-003 | nine generated outputs match golden fixtures |
| ET-004 | rollback injection succeeds at replacement ordinals 1 through 5 |
| ET-005 | mutation artifact exists before final baseline |
| ET-006 | ordinary post-promotion check sees a null candidate |
| ET-007 | absent maintainer decision stops before any write |

Add a contract test under `tests/contract/upstream/` that extracts IDs from
`spec.md`, loads a machine-readable traceability projection generated from
schema v2, and asserts exact equality for FR-001..FR-040, BC-001..BC-006,
SC-001..SC-012, and ET-001..ET-007 (65 IDs). Do not parse this Markdown file at runtime; the generated
`approved_sdk_contract.json` carries the requirement IDs attached to operations,
target, generation, coherence, and live-gate sections.

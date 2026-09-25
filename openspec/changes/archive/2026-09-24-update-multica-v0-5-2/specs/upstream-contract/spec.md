## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the approved target version.
For the Multica `0.5.2` target, the interval SHALL be
`[0.4.42,0.5.3)`: `0.4.42` remains the minimum compatible CLI for retained
operations, `0.5.2` is the maximum tested CLI, the newly decoded duplicate and
supplement fields SHALL require `0.5.2` where field-level compatibility is
represented, atomic create-time properties SHALL require `0.5.2`, and `0.5.3`
is the exclusive next-patch ceiling. Existing operation-level minimums SHALL
remain unchanged unless target source proves an operation delta.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.5.2` contract is rendered
- **THEN** it accepts retained operations on `0.4.42` through `0.5.2`, rejects or warns at `0.5.3` according to policy, and identifies the new response fields and atomic create properties as `0.5.2` additions

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions

## ADDED Requirements

### Requirement: Multica 0.5.2 provenance is exact
The approved contract SHALL identify target tag `v0.5.2`, release
`394535503`, peeled commit
`d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, baseline commit
`f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, their direct comparison, official
checksum sources, both reviewed Darwin ARM64 archive and executable SHA-256
values, and both version JSON identities. The unsigned tag SHALL be recorded and
accepted only when the official release, checksum material, asset digest,
peeled commit, executable identity, and binary-reported commit agree.

#### Scenario: Provenance gate accepts one coherent target
- **WHEN** strict provenance validation runs for the approved direct-patch contract
- **THEN** every target and baseline identity equals the pinned release evidence and any mismatch fails validation

#### Scenario: Review evidence stays outside production inputs
- **WHEN** collector, gap, response, checksum, archive, executable, or version evidence is inspected
- **THEN** it remains ignored review input and cannot directly generate or promote public SDK behavior

### Requirement: Complete 0.5.1 to 0.5.2 command inventory is dispositioned
The approved contract SHALL reconcile both 201-node public help trees with zero
additions, removals, renames, or moves and exactly three changed help nodes:
`issue create`, `issue list`, and `issue timeline`. Every retained or changed
node SHALL record positional arity, local and inherited flags, aliases, defaults,
accepted values, required and presence rules, conflicts, and path/query/JSON/
header/multipart/stdin/file/process destinations. Source-only names SHALL be
classified exactly as root normalization (`multica`), hidden
(`probe-runtimes`), test-only (`repo-test`, `test`), and parser false-positive
(`x`).

#### Scenario: Command reconciliation is exact
- **WHEN** strict command audit compares the baseline and target inventories
- **THEN** it reports `201→201`, zero topology changes, three changed help nodes, no unresolved rows, and a disposition for every node and source-only name

#### Scenario: Unchanged nodes retain complete semantics
- **WHEN** any of the 198 unchanged nodes is sampled or exhaustively validated
- **THEN** its arity, flags, aliases, defaults, values, presence, conflicts, and destination mappings equal the approved baseline

### Requirement: Complete 0.5.2 response review governs adaptation
The approved contract SHALL contain exactly 167 unique supported response
work-item IDs with `response_review_complete=true`, pinned old and target source
URLs, exact changed or unchanged disposition, model/fixture/document action, and
no unresolved item. It SHALL adapt the `IssueResponse.duplicate_of` projection
and task supplement metadata only where target source hydrates them, while
retaining existing envelopes, pagination, ordering, timestamps, numeric
encoding, error decoding, and open-enum policy.

#### Scenario: Response registry is complete
- **WHEN** strict response validation runs
- **THEN** all 167 supported work-item IDs occur exactly once and every changed row has reviewed fields, omission policy, source URLs, and test references

#### Scenario: Shared server fields do not imply CLI output
- **WHEN** shared comment or task types contain supplement receipt or daemon-only fields that supported CLI entrypoints do not hydrate
- **THEN** those fields remain absent from the corresponding SDK response contract and negative inventory guards prove no accidental projection

### Requirement: Atomic create-time property mapping is approved
The `issues.create` operation SHALL map each ordered
`IssuePropertyAssignment(reference, value)` to one repeatable
`--property <reference>=<value>` binding. SDK-local validation SHALL be limited
to the tuple and item types, a nonblank string reference, and a string value.
Empty string values, `__none__`, and comparison spellings SHALL reach the pinned
CLI unchanged. The pinned CLI SHALL remain the authority for value grammar,
configuration and capability preflight, name or UUID definition resolution,
all property-type canonical JSON conversions, duplicate and archived rejection,
atomic request binding, and post-create property snapshot verification. The
approved mapping SHALL preserve caller order and SHALL NOT introduce a
client-side catalog lookup.

#### Scenario: Ordered assignments map without extra I/O
- **WHEN** create receives multiple valid assignments
- **THEN** command construction emits one `--property` pair per item in caller order and performs no filesystem, catalog, or transport I/O

#### Scenario: CLI owns value grammar, catalog validation, and atomicity
- **WHEN** a property value is empty, equals `__none__`, uses a comparison spelling, or a property reference is unresolved, archived, duplicated, type-invalid, or mismatches the returned snapshot
- **THEN** the pinned CLI returns its reviewed failure and the SDK surfaces that failure without a create-then-set fallback

### Requirement: New REST-only and local-file behavior remains outside the SDK
Task-supplement create/retry/claim/ack handlers, supplement receipt fields on
comment handlers, duplicate mark/unmark mutations, duplicate timeline actions,
and issue-create attachment path behavior SHALL NOT create public SDK operation
IDs, methods, resources, enums, retries, models, or file inputs in this change.

#### Scenario: Negative inventory prevents accidental promotion
- **WHEN** public symbols, operation IDs, generated mappings, and canonical vectors are enumerated
- **THEN** no supplement mutation, duplicate mutation, issue timeline, comment receipt, or issue-create attachment surface is present

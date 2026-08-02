## Context

One SDK service consumer uses Multica issues as a durable work queue. This read
path needs three pieces of information already present in pinned Multica CLI
`0.4.9` responses but not faithfully exposed by the SDK:

1. issue-list metadata and labels for queue/external-key selection;
2. both workspace-membership and user identities for assignee filtering and
   issue-creator reconciliation;
3. attachment summaries embedded in `issue get` for result discovery.

The current SDK decodes `IssueSummary`, then converts every summary returned by
`issues.list()` into a compact bound `IssueEntity`. That conversion erases the
honest distinction between a list projection and a complete issue and invites
per-item lazy reads. Workspace members expose only membership `id`, even though
upstream also returns `user_id` and `email`. The issue-get wire response accepts
no embedded attachments despite upstream returning them when its best-effort
attachment query succeeds.

The repository is pre-stable, uses immutable data models, explicit CLI argv,
approved-contract generation, and entity-local relation caches. The archived
33-relation contract remains normative except for the five relations backed by
`issues.list`, whose item type changes from full `Issue` to `IssueSummary`.

## Goals / Non-Goals

**Goals:**

- Make queue and external-key discovery one issue-list traversal without an
  N-plus-one issue or relation read.
- Make list return types accurately represent upstream list rows.
- Preserve both meanings of workspace-member identity without breaking the
  membership ID used by assignee filtering.
- Expose already-fetched issue attachments without adding transport calls.
- Keep mappings governed by the approved upstream contract and fully testable
  offline.

**Non-Goals:**

- No global or cross-entity cache.
- No generic query DSL, auto-pagination API, attachment selector, result policy,
  or retry framework.
- No new attachment list relation or replacement for the removed
  `attachments.list` operation.
- No change to upstream Multica CLI or server.
- No inference that an empty embedded attachment tuple proves an atomic or
  terminal backend state.

## Decisions

### 1. Preserve the list projection instead of binding partial issues

`IssueResource.list()` returns the existing `IssueListPage` directly, and its
`issues` tuple remains `IssueSummary`. `BoundIssueListPage` and the private
summary-to-entity conversion are removed. The five relations backed by this
same operation expose `OffsetLazyCollection[IssueSummary]`:

```text
issue list response ──> IssueSummary ──> IssueListPage
                              └───────> five offset relations

issue get response  ──> IssueData    ──> bound IssueEntity
```

This is a deliberate pre-stable breaking change. A caller that needs comments,
metadata mutation, refresh, or any other bound behavior calls
`client.issues.get(summary.id)`. Summary fields remain immutable and passive.
The canonical public imports remain
`multica_py.models.issues.{IssueListFilter, IssueListPage, IssueMetadataItem,
IssueSummary}`. This change removes `BoundIssueListPage` and does not add
top-level compatibility exports.

Alternatives considered:

- Keep `BoundIssueListPage` and add more fields to compact `IssueEntity`.
  Rejected because it continues to present incomplete data as a full entity.
- Add parallel `list_summaries()` and summary relations. Rejected because it
  doubles the public surface and leaves the misleading default in place.

### 2. Reuse `IssueMetadataItem` for ordered list predicates

`IssueListFilter` gains
`metadata: tuple[IssueMetadataItem, ...] = ()`. Each item maps to one repeatable
`--metadata` pair. The handwritten issue-resource adapter encodes each value
with `json.dumps(value, ensure_ascii=False, separators=(",", ":"),
allow_nan=False)`. This gives deterministic representations for
`str | int | float | bool | None`, rejects `nan`, `inf`, and `-inf`, and quotes
strings so numeric-looking or boolean-looking strings cannot be reinterpreted
by the upstream CLI parser. Predicate order is preserved. Keys are validated as
nonblank, unique, and without `=` before invoking transport. Encoding and
validation are adapter policy verified by exact-argv tests; they are not new
approved-contract schema fields.

Alternatives considered:

- Add `dict[str, MetadataValue]`. Rejected because the public filter contract
  uses an immutable ordered predicate sequence and must preserve caller order
  explicitly before conversion to repeatable argv; duplicate keys remain
  invalid, matching pinned CLI behavior.
- Add a new metadata-filter class. Rejected because `IssueMetadataItem` already
  expresses exactly one typed key/value pair.
- Forward Python `str(value)`. Rejected because boolean, null, and ambiguous
  string semantics would diverge from upstream JSON-like parsing.

### 3. Keep `WorkspaceMember.id` and add explicit user fields

`WorkspaceMember.id` remains the upstream workspace-membership ID. It is the
correct identifier for `WorkspaceMember.issues`, whose filter remains
`assignee_id=member.id`. Optional `user_id` and `email` fields are added to the
wire and immutable models. `user_id` is the key consumers compare with
`Issue.creator_id`; `email` supports registry lookup and display.

There is no rename or deletion of `id`: doing so would break the current
relation and would discard a real upstream identity. Optional defaults preserve
decoding of older/minimal fixtures.

Alternatives considered:

- Rename `id` to `membership_id`. Rejected because it creates migration work
  without ambiguity at the typed field boundary once both fields are documented.
- Alias `id` to `user_id`. Rejected because the upstream values have different
  semantics and may differ.

### 4. Treat embedded attachments as a passive snapshot

`IssueWire` gains
`attachments: tuple[AttachmentResult, ...] | msgspec.UnsetType = msgspec.UNSET`.
One normalization maps `UNSET` and an empty array to `()`. Both
`issue_from_wire` and `issue_data_from_wire` use it to populate
`models.issues.Issue.attachments` and `IssueData.attachments`, respectively.
The bound `IssueEntity.attachments` property returns the `IssueData` tuple and
performs no I/O. The SDK reuses `AttachmentResult` (`id`, `filename`, `url`)
rather than introducing a second attachment model.

Both an omitted field and an explicit empty array normalize to `()`. This is the
only faithful shape available without changing upstream: pinned code omits the
field both when no attachments exist and when its best-effort attachment read
fails. Documentation therefore tells polling consumers to repeat
`issues.get(issue_id)` when a result is expected. Download remains an explicit
`attachments.download_bytes(attachment.id)` call.

Alternatives considered:

- Add a lazy `Issue.attachments` relation. Rejected because there is no governed
  upstream list/filter operation and it would contradict the relation policy.
- Add an `attachments_loaded` or tri-state wrapper. Rejected because the pinned
  response cannot distinguish empty from failed; an extra SDK state would imply
  information upstream did not provide.
- Request an upstream response change. Explicitly excluded by the user; the
  retry-safe consumer policy is sufficient for this change.

### 5. Keep caches local and policies application-owned

No global Multica SDK cache is added. These reads are scoped, mutable, and may
be performed against different targets or credentials. A process-wide cache
would need invalidation, isolation, freshness, and memory-bound policies that
the SDK cannot choose correctly for all consumers. Existing relation-local
caches stay unchanged; `IssueSummary` list pages and embedded attachment tuples
are ordinary immutable response snapshots. The consumer owns polling cadence,
queue choice, external-key uniqueness, and result-attachment selection.

Alternatives considered:

- Cache issue/member results globally by ID. Rejected because identity is not
  sufficient without target/credential scope and mutations make freshness
  application-specific.
- Add SDK selection helpers such as `find_by_metadata` or `result_attachment`.
  Rejected because a single list predicate and immutable response fields already
  expose the required primitive without encoding one consumer's policy.

### 6. Reuse existing documentation contract checks

Public type-level examples are encoded in
`tests/contract/test_bound_public_surface.py`; migration-token assertions remain
in `tests/contract/test_bound_public_docs.py`. The implementation updates
`docs/migration.md`, `docs/service-usage.md`, and `examples/issue_queue.py` but
does not add a Markdown parser, snippet extractor, or new documentation test
harness.

Alternative considered: type-check Markdown directly. Rejected because the
repository has no such harness and the existing contract tests already provide
the smallest deterministic seam.

### 7. Pin exact source and test evidence

Implementation MUST add the following narrow `source_refs` and `test_refs` to
`contracts/sdk-contract.json`; broad existing `S-ISSUE`, `S-WORKSPACE`,
`T-OPERATION`, and relation refs remain in place. Line ranges refer to pinned
upstream commit `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.

| Concern / operation updates | Exact source refs to add | Exact test ref to add |
|---|---|---|
| Metadata flag, duplicate/parser semantics, and server query destination; append refs to `issues.list` | `S-ISSUE-LIST-METADATA-CLI`: `server/cmd/multica/cmd_issue.go`, `issueListCmd/runIssueList`, lines 436–622; `S-ISSUE-LIST-METADATA-PARSER`: `server/cmd/multica/cmd_issue_metadata.go`, `buildMetadataFilterQueryParam`, lines 19–54; `S-ISSUE-LIST-METADATA-HANDLER`: `server/internal/handler/issue.go`, `ListIssues/parseMetadataFilterParam/MetadataFilter`, lines 778–878 | `T-ISSUE-LIST-METADATA`: `tests/unit/resources/test_operations.py`, node `test_operation[manual:issues.list:metadata:canonical]` |
| List labels/metadata projection; append refs to `issues.list` | `S-ISSUE-RESPONSE`: `server/internal/handler/issue.go`, `IssueResponse`, lines 31–71; `S-ISSUE-LIST-PROJECTION`: same path, `ListIssues/labelsByIssue/IssueResponse`, lines 778–1270 | `T-ISSUE-LIST-PROJECTION`: `tests/unit/resources/test_issues.py`, node `test_issue_list_page_decodes_summary_collections` |
| Membership ID, `user_id`, and `email`; append refs to `workspaces.members.list` | `S-WORKSPACE-MEMBERS-CLI`: `server/cmd/multica/cmd_workspace.go`, `runWorkspaceMembers`, lines 524–562; `S-WORKSPACE-MEMBER-IDENTITY`: `server/internal/handler/workspace.go`, `MemberWithUserResponse/ListMembersWithUser`, lines 391–429 | `T-WORKSPACE-MEMBER-IDENTITY`: `tests/unit/resources/test_workspace_relations.py`, node `test_workspace_members_preserve_user_identity` |
| Embedded attachments and omitted-field ambiguity; append refs to `issues.get` | reuse `S-ISSUE-RESPONSE`; `S-ISSUE-GET-ATTACHMENTS`: `server/internal/handler/issue.go`, `GetIssue/ListAttachmentsByIssue/Attachments`, lines 1864–1900 | `T-ISSUE-GET-ATTACHMENTS`: `tests/unit/resources/test_issues.py`, node `test_issue_get_decodes_attachment_snapshots` |

The implementation adds each named `test_ref_id` with the exact path/node above
before attaching it to its operation. `issues.list.rationale` states metadata
mapping plus summary projection; `issues.get.rationale` states embedded
attachment normalization and upstream omission ambiguity;
`workspaces.members.list.rationale` states the distinct membership/user identity
projection. No implementer chooses alternative IDs, paths, nodes, or source
ranges.

## Risks / Trade-offs

- [Direct list and five relation item types break alpha callers] → Publish exact
  migration examples and validate them with mypy; full issues remain one
  explicit `issues.get` away.
- [Some callers may miss bound methods on list items] → Type changes make this
  visible statically and documentation distinguishes summary and entity paths.
- [JSON-quoted string values look unusual in argv] → Exact table-driven argv
  tests and pinned-source references prove that quoting preserves string type.
- [Omitted attachments conflate empty and upstream read failure] → Normalize
  honestly to `()` and document retry behavior; do not invent a certainty bit.
- [Optional `user_id` cannot reconcile very old/minimal payloads] → Preserve
  `None` and require consumers to handle absence rather than falling back to the
  semantically different membership ID.
- [Archived relation specs could drift from implementation] → Modify the
  normative matrix and all affected relation requirements in this change, then
  archive-sync them together.

## Migration Plan

1. Add the existing-schema `issues.list` mapping
   `filter.metadata / repeat:--metadata / query:metadata` at all three schema-v3
   locations: `catalogs.bindings.issue_list.mappings`, the matching
   `catalogs.mapping_presence.issue_list` position as `optional_omit`, and
   `catalogs.binding_descriptors[descriptor_id == "issue_list"].mappings`.
   Update the three operation records and exact evidence entries from Decision
   7, then regenerate checked runtime artifacts. Response projections and
   adapter validation remain handwritten because contract schema v3 has no
   fields for them.
2. Extend wire and immutable models with backward-compatible optional/defaulted
   member, summary, and attachment fields.
3. Change direct list and the five list-backed relations to preserve summaries;
   remove `BoundIssueListPage` and the compact-entity conversion.
4. Update table-driven unit/component/contract fixtures and type assertions.
5. Update migration and consumer examples, then run all offline quality gates.
6. Release as an alpha breaking change. Rollback is a revert of this change;
   no persisted data or upstream migration is involved.

## Open Questions

None. The three product decisions are resolved: summaries are the list item
type, `WorkspaceMember.id` remains the membership ID, and upstream is unchanged.

## 1. Approved contract and generated surface

- [x] 1.1 Add `filter.metadata / repeat:--metadata / query:metadata` to `catalogs.bindings.issue_list.mappings` and `catalogs.binding_descriptors[descriptor_id == "issue_list"].mappings`; add `optional_omit` at the matching `catalogs.mapping_presence.issue_list` position.
- [x] 1.2 Add every exact `source_ref_id`, pinned path, symbol, and line range from design Decision 7; append the prescribed refs to `issues.list`, `issues.get`, and `workspaces.members.list` while retaining their existing broad refs.
- [x] 1.3 Register every exact `test_ref_id` and future path/node from design Decision 7 and append it to its prescribed operation while retaining existing refs; do not create placeholder tests or implement nodes owned by tasks 2.6, 4.3, and 5.3.
- [x] 1.4 Update only the three operation rationales prescribed by Decision 7; keep summary/member/attachment projections and validation as handwritten decoder/resource policy without adding schema-v3 fields or upstream operations.
- [x] 1.5 Render the approved runtime artifacts and prove `scripts/upstream_contract.py validate`, `render`, and `check` accept the existing-schema approved mapping as production generator input.

## 2. Issue-list predicates and honest summaries

- [x] 2.1 Add `IssueSummaryWire.labels: tuple[LabelData, ...] | msgspec.UnsetType = msgspec.UNSET` and `metadata: dict[str, MetadataValue] | msgspec.UnsetType = msgspec.UNSET`; map them to `IssueSummary.label_names` and `metadata_snapshot`, with omitted values normalized to `()`.
- [x] 2.2 Extend `IssueListFilter` with ordered `tuple[IssueMetadataItem, ...]` predicates and encode each value with `json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)` in the handwritten issue-resource adapter.
- [x] 2.3 Validate blank, `=`-containing, and duplicate metadata keys plus `nan`, `inf`, and `-inf` values before transport; preserve caller predicate order for valid repeatable `--metadata` argv pairs.
- [x] 2.4 Change `IssueResource.list()` to return `IssueListPage` directly and remove `BoundIssueListPage` plus summary-to-entity fabrication.
- [x] 2.5 Preserve canonical imports from `multica_py.models.issues` for `IssueListFilter`, `IssueListPage`, `IssueMetadataItem`, and `IssueSummary`; remove `BoundIssueListPage` without adding new top-level exports or a compatibility alias.
- [x] 2.6 Add issue-list unit rows for every valid metadata scalar type, omission, ordering, blank/equals/duplicate keys, each non-finite float, summary labels/metadata present and omitted, pagination, and complete expected argv; implement and resolve `T-ISSUE-LIST-METADATA` and `T-ISSUE-LIST-PROJECTION` at the exact Decision 7 nodes.
- [x] 2.7 Update canonical operation rows and decoding fixtures so discovered public methods and the generated contract remain exact.

## 3. Five issue-list relations

- [x] 3.1 Change workspace and project issue loaders and annotations to `OffsetLazyCollection[IssueSummary]` while preserving workspace/project filters and offset progression.
- [x] 3.2 Change agent, squad, and workspace-member issue loaders and annotations to `OffsetLazyCollection[IssueSummary]` while preserving assignee filters and offset progression.
- [x] 3.3 Remove list-summary binding from all five loaders and prove complete loads perform no per-item `issues.get` calls.
- [x] 3.4 Update the existing frozen relation case tables for exact item types, filters, page boundaries, cache refresh, and no-progress behavior without adding duplicate test files.
- [x] 3.5 Update type-checking assertions and public imports for all five summary relations.

## 4. Workspace-member identity

- [x] 4.1 Add optional `user_id` and `email` directly to existing `models.workspaces.WorkspaceMember` and `models.system.WorkspaceMemberData`; do not create a new workspace-member wire class, and keep `id` unchanged as the membership identifier.
- [x] 4.2 Copy `member.user_id` and `member.email` in `_bind_workspace_member`, then expose same-named passive `WorkspaceMemberEntity` properties without extra I/O.
- [x] 4.3 Prove through `WorkspaceResource.members`, using a fixture with distinct IDs rather than direct entity construction, that binding preserves both fields and `WorkspaceMember.issues` emits `--assignee-id <member.id>`, not `user_id`; implement and resolve `T-WORKSPACE-MEMBER-IDENTITY` at the exact Decision 7 node.
- [x] 4.4 Add a consumer-shaped typed test that reconciles `IssueSummary.creator_id` to `WorkspaceMember.user_id` and reads `email` without a user-list API.

## 5. Embedded issue attachments

- [x] 5.1 Add `IssueWire.attachments: tuple[AttachmentResult, ...] | msgspec.UnsetType = msgspec.UNSET`; implement one normalization used by `issue_from_wire` and `issue_data_from_wire` to populate `Issue.attachments` and `IssueData.attachments`.
- [x] 5.2 Expose `IssueEntity.attachments` as the passive read-only `IssueData.attachments` tuple with no lazy relation state or transport call.
- [x] 5.3 Add decode rows for `Issue`, `IssueData`, and `IssueEntity` with ordered attachments, explicit empty arrays, and omitted fields, including repeated passive property access; implement and resolve `T-ISSUE-GET-ATTACHMENTS` at the exact Decision 7 node.
- [x] 5.4 Add a consumer-shaped polling fixture where a later explicit `issues.get` returns exactly one attachment and `download_bytes` receives `issue.attachments[0].id` with no selector helper.
- [x] 5.5 In `tests/contract/test_bound_public_surface.py`, replace the negative `IssueEntity.attachments` assertion with proof that it is a passive non-lazy tuple property; also verify no `attachments.list`, attachment relation loader, selection helper, or new public attachment model is introduced.

## 6. Migration and consumer guidance

- [x] 6.1 Update `docs/migration.md` with before/after examples for direct list and five relation callers moving from bound `Issue` items to `IssueSummary` plus explicit `issues.get` when needed.
- [x] 6.2 Document `WorkspaceMember.id` as membership identity, `user_id` as creator-reconciliation identity, and backward-compatible `None` handling.
- [x] 6.3 Document embedded attachment snapshot semantics, the upstream omitted-field ambiguity, explicit retry through `issues.get`, and download through `download_bytes`.
- [x] 6.4 Update `docs/service-usage.md` and `examples/issue_queue.py` so issue-list pages and list-backed relations use `IssueSummary` and no example invokes bound relations on a summary.
- [x] 6.5 Add a neutral queue/external-key example that filters metadata server-side and consumes summary labels/metadata without N-plus-one reads.
- [x] 6.6 Put type-level consumer examples in `tests/contract/test_bound_public_surface.py` and migration-token checks in `tests/contract/test_bound_public_docs.py`; do not add a Markdown parser or new snippet harness.

## 7. Verification and release readiness

- [x] 7.1 Run focused unit, component, contract, and packaging tests for changed models, resources, relations, generated artifacts, and docs; prove every new Decision 7 `test_ref_id` resolves to its exact existing pytest node.
- [x] 7.2 Run `uv run ruff check .` and `uv run ruff format --check .`.
- [x] 7.3 Run `uv run mypy src` and `uv run mypy tests` with no `Any` escape for new test helpers.
- [x] 7.4 Run `uv run pytest -m "not live"` and verify live nodes remain excluded from offline collection.
- [x] 7.5 Run strict OpenSpec validation and `git diff --check`, then confirm the implementation contains no global cache, new dependency, or upstream-change prerequisite.

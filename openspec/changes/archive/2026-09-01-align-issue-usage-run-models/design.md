## Context

See `proposal.md` for motivation. The current issue decoder accepts only a nested assignee; `IssueUsage` models a legacy summary; and the task-run wire drops most of the API response. The CLI commands pass the server JSON through unchanged. The repository requires the approved SDK contract to remain the sole production generator input, table-driven tests, private wire models, immutable public values, and an offline default suite.

## Goals / Non-Goals

**Goals:**

- Preserve reviewed current fields while continuing to decode supported legacy envelopes.
- Make contradictory assignee projections an explicit output-shape failure.
- Keep cache token categories and totals semantically unambiguous.
- Expose the minimum task-run context required to locate and interpret a run.
- Derive default compatibility bounds from the approved contract.

**Non-Goals:**

- Mirror every field in the server's large task response.
- Make evidence or live responses direct generator input.
- Add a second public DTO hierarchy or recommend raw CLI as the normal path.
- Require a backend for offline verification.

## Decisions

### Normalize assignee projections in one wire-to-public adapter

The private issue wire will accept nested and scalar forms with presence preserved. One adapter will validate the scalar pair, compare dual projections, and produce the existing public `IssueAssignee`. This keeps contradiction policy out of public models and prevents separate decoders from drifting. Treating scalar fields as a second public assignee type was rejected because both shapes represent the same domain value.

### Preserve categories instead of inventing a token total

`IssueUsage` will add exact current envelope fields. Legacy names remain only where they have evidence and clear semantics. A convenience total, if retained for compatibility, will not include cache-read tokens unless its documented arithmetic explicitly says so; current category fields are authoritative. Computing a new all-token total was rejected because cache reads have different billing and semantic meaning.

### Add a bounded task-run projection

The public `TaskRun` and its private wire will add reviewed runtime/location/result fields: `runtime_id`, `workspace_id`, `work_dir`, `relative_work_dir`, durable work-dir variants, `branch_name`, `result`, `error`, `failure_reason`, and lifecycle timestamps. JSON result values will use the repository's immutable JSON conversion. The rest of the server task envelope stays unmodeled until separately reviewed. Mirroring the entire server struct was rejected as speculative SDK surface growth.

### Keep compatibility policy contract-driven without conflating provenance

The catalog-wide pinned source target remains 0.4.28 because the existing
approved operation mappings and their source references were reviewed against
that baseline. The exact 0.4.32 upstream commit is inspected for the three new
response mappings, while the locally installed release binary independently
supplies verified 0.4.32 version/build metadata. A separate approved
compatibility block records inclusive minimum 0.4.28 and maximum-tested 0.4.32;
generation converts that to the existing exclusive upper bound 0.4.33. The
default policy behavior remains unchanged. Rewriting unrelated existing source
references merely to advance the catalog-wide target was rejected because it
would erase their actual review provenance.

### Use source-backed synthetic fixtures and a gated live check

Fixtures will copy the field shapes and representative values established by upstream handler/CLI tests and identify their provenance. They will not contain user secrets or live identifiers. The live smoke will be conditional on existing live credentials/data and will not weaken the offline gate when the backend is unavailable.

## Risks / Trade-offs

- [Older payloads use ambiguous legacy usage totals] -> Preserve legacy fields as compatibility values and document current authoritative categories separately.
- [Both assignee shapes may be emitted during rollout] -> Accept matching dual projections and reject only partial or conflicting projections.
- [Absolute `work_dir` can contain local paths] -> Preserve it because the CLI already returns it, document `relative_work_dir` as the display-safe choice, and avoid logging fixture paths from real users.
- [The server task envelope evolves quickly] -> Keep the projection bounded and require approved-contract review for new public fields.
- [Live backend is unavailable during development] -> Keep live proof explicitly gated and require all source-backed offline gates to pass independently.

## Migration Plan

1. Add approved mappings, separate verified-binary metadata, and compatibility metadata before rendering generated bounds.
2. Extend private wires and public values with backward-compatible optional fields.
3. Add legacy/current/conflict fixtures and tests, then update documentation.
4. Run focused tests, contract render/check, strict OpenSpec, and the complete offline gate.
5. Run the live smoke when an authorized responsive CLI 0.4.32 environment is available; a backend timeout is reported separately and does not masquerade as live acceptance.

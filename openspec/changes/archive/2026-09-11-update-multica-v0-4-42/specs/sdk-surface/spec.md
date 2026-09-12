## ADDED Requirements

### Requirement: Target response deltas preserve typed presence

The SDK SHALL decode target `Issue`, `Comment`, `Agent`, and `TaskRun` additions
through private presence-aware wires into immutable public values. Issue SHALL
preserve `status_name`, exact `revision`, nullable `last_activity_at`, and
detail-only optional `source_context`. Comment SHALL preserve exact `revision`
and distinguish omitted `issue_revision` from a present integer. Agent SHALL
preserve optional `runtime_availability` and required
`conversation_starters` as typed label/prompt values. TaskRun SHALL preserve
the reviewed additive context, usage, path, status-catalog, quick-create,
comment-delta, and plugin-hook-tool fields while removing obsolete
`plugin_execution_manifest` and `active_sibling_runs` projections. Exact
integers SHALL not be converted through floating point.

#### Scenario: Missing null and zero remain distinct
- **WHEN** legacy, compact, null-bearing, zero-bearing, and target payloads are decoded
- **THEN** each reviewed field follows its approved omission/null/value policy and no missing field is silently fabricated as zero or empty

#### Scenario: Nested conversation starters are typed
- **WHEN** an Agent response contains zero or more `{label,prompt}` starters
- **THEN** decoding returns an immutable typed collection, rejects malformed known shapes, and does not expose raw mutable dictionaries

#### Scenario: Removed task-run fields are not public
- **WHEN** the final TaskRun surface and fixtures are inspected
- **THEN** obsolete plugin manifest and active-sibling projections are absent while arbitrary reviewed JSON results remain immutable

### Requirement: Skill content projection is explicit and compatible

`skills.list` SHALL accept the target metadata-only default and SHALL not claim
that bodies are present. `skills.get` SHALL emit `--with-content` so the
existing full Skill return contract is preserved. `skills.files.list` and the
bound `Skill.files` relation SHALL use an explicit `with_content: bool = False`
projection; omitted content and size-only metadata SHALL remain distinguishable
from present empty content.

#### Scenario: Skill get preserves full content
- **WHEN** `skills.get(id)` or its command form runs
- **THEN** argv includes `--with-content`, and the typed result preserves the existing full-skill contract

#### Scenario: Skill lists remain metadata-only
- **WHEN** `skills.list()` runs without a content option
- **THEN** body omission decodes successfully and no empty body is invented

#### Scenario: Skill file content is opt-in
- **WHEN** a caller lists skill files with `with_content=True` versus omission
- **THEN** only the explicit case emits `--with-content`, and decoding distinguishes content-present from content-omitted rows

### Requirement: Unsupported Plugin public symbols are removed

The package SHALL remove `MulticaClient.plugins`, `PluginResource`, Plugin
models and digests, `Workspace.plugins`, root/submodule exports, generated
bindings, canonical operations, documentation, and dedicated tests. The SDK
SHALL NOT remap these symbols to apps, remote MCP, raw CLI, or another service.

#### Scenario: Public discovery contains no Plugin surface
- **WHEN** public symbols, methods, eager/command pairs, bound relations, generated descriptors, and canonical vectors are discovered
- **THEN** no Plugin SDK surface remains and the exact inventories contain no allowlist exception

#### Scenario: Migration names no replacement
- **WHEN** a Plugin consumer reads migration guidance
- **THEN** the removed upstream command is stated plainly and no unsupported replacement is advertised

### Requirement: Issue query projections are reviewed opt-in operations

Issue get SHALL accept `resolve_properties: bool = False`. Issue list SHALL
accept ordered `fields`, repeatable property predicates, property sorting, and
`resolve_properties: bool = False`. `fields` SHALL validate the target
allowlist; limit SHALL be within `1..100`; repeated values for the same property
SHALL mean OR, distinct properties SHALL mean AND, `__none__` SHALL represent
an unset property, and reserved comparison spellings `>=`, `<=`, and `!=`
SHALL fail before transport. Resolved-property JSON SHALL decode through a
separate reviewed projection rather than replacing the default raw UUID map.

#### Scenario: Default issue behavior is unchanged
- **WHEN** issue get/list is called without new options
- **THEN** argv contains none of the new flags and existing raw property and page return contracts are retained

#### Scenario: Property predicates preserve grouping
- **WHEN** issue list receives repeated predicates for one property and another predicate for a second property
- **THEN** argv repeats `--property` in caller order and documentation/tests state same-property OR and cross-property AND semantics

#### Scenario: Projection validation is local
- **WHEN** fields, limit, property operator, sort, or resolve-properties usage violates the reviewed target constraints
- **THEN** construction raises the documented validation error before transport

#### Scenario: Pagination is truthful
- **WHEN** target list/search pages are empty, truncated, repeated, malformed, or cannot provide a valid count
- **THEN** adapters preserve truthful `has_more`, never invent a total, and stop with a typed error rather than looping or claiming completion

### Requirement: New target commands with distinct envelopes remain deferred

The SDK SHALL NOT add public methods for `issue timeline`,
`autopilot trigger-list`, or compact `issue runs --active/--siblings` in this
change. Existing default issue history and bound `Issue.runs` SHALL continue to
return the reviewed full TaskRun page/relation.

#### Scenario: Default run history remains full
- **WHEN** existing issue run methods or relations execute
- **THEN** they omit `--active` and `--siblings` and decode the full history envelope

#### Scenario: Raw evidence does not add deferred APIs
- **WHEN** source or binary evidence exposes a deferred command
- **THEN** no typed public symbol is generated until a separate delta specifies its response and pagination model

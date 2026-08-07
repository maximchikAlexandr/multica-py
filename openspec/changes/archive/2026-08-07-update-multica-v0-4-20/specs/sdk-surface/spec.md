## ADDED Requirements

### Requirement: Agent copy exposes portable upstream semantics

`AgentResource` SHALL expose eager `copy(...) -> Agent` and lazy
`copy_command(...) -> Command[Agent]` methods. Both methods SHALL accept a
required nonblank `source_agent_id` and the same keyword-only override surface:
`name`, `runtime_id`, `description`, `instructions`, `model`,
`thinking_level`, `service_tier`, `custom_args`, `max_concurrent_tasks`,
`permission_mode`, `public_to_workspace`, `public_to_member_ids`, and
`copy_skills`. Presence-sensitive string, tuple, integer, and permission
overrides SHALL use `Unset` as omission; a present `custom_args` SHALL be a
string-only `tuple[str, ...]`; `copy_skills` SHALL default to `True`. The eager
method SHALL delegate through the lazy command.

The operation SHALL emit `agent copy <source-agent-id>` and only the flags
represented by present overrides, plus `--no-skills` when `copy_skills=False`.
When `runtime_id` is present and `model` is omitted, the SDK SHALL emit
`--model ""` so the upstream cross-runtime guard selects the target runtime's
default model. This is the sole runtime-specific omission exception: omitted
`thinking_level` and `service_tier` SHALL remain absent and SHALL NOT be
invented. When `runtime_id` is omitted, omitted `model`, `thinking_level`, and
`service_tier` SHALL remain omitted so upstream preserves same-runtime state.
The SDK SHALL NOT expose or emit `custom_env`, `mcp_config`, or `runtime_config`
through this copy operation.

#### Scenario: Same-runtime copy keeps upstream defaults
- **WHEN** `client.agents.copy(source_agent_id)` is called without overrides
- **THEN** argv is `agent copy <source-agent-id> --output json`, the source remains unchanged, upstream creates a new agent on the source runtime, portable configuration and skills are copied, and machine-local or secret-bearing configuration is not copied

#### Scenario: Cross-runtime copy selects the target default model
- **WHEN** `client.agents.copy(source_agent_id, runtime_id=target_runtime_id)` is called without a model override
- **THEN** argv contains `--runtime-id <target-runtime-id> --model ""`, upstream creates the copy on the target runtime, and source model, thinking level, and service tier are not carried across the runtime boundary

#### Scenario: Cross-runtime runtime-specific values follow settled policy
- **WHEN** a target runtime is supplied with any combination of optional model,
  thinking-level, and service-tier overrides
- **THEN** each present value is emitted through its matching flag, an omitted
  model is emitted as `--model ""`, and omitted thinking-level and service-tier
  values remain absent

#### Scenario: Portable overrides preserve presence
- **WHEN** present overrides include an empty description or instructions, a
  string custom-argument tuple (`tuple[str, ...]`), max concurrency, invocation
  permissions, and `copy_skills=False`
- **THEN** exact argv preserves caller order and empty-string presence,
  serializes the string custom-argument tuple as a compact JSON array, emits
  permission flags and `--no-skills`, and does not emit any secret or
  machine-local flag

#### Scenario: Permission member order is stable
- **WHEN** `public_to_member_ids` contains multiple member IDs
- **THEN** argv contains repeatable `--public-to-member` flags in caller order

#### Scenario: Copy validation occurs before transport
- **WHEN** source ID or a present name is blank, max concurrency is outside `1..50`, or a present member ID is blank
- **THEN** construction raises `ValueError` naming the invalid input before command preview or subprocess execution

#### Scenario: Copy command preview is lazy and redacted
- **WHEN** `copy_command()` is constructed with valid overrides
- **THEN** no subprocess I/O occurs, `commands` shows the exact shell-rendered `agent copy` invocation, and `run()` executes that same plan and returns the bound copied `Agent`

### Requirement: Issue search preserves its API and decodes v0.4.20 results

`IssueResource.search(query) -> tuple[IssueSummary, ...]` and
`search_command(query) -> Command[tuple[IssueSummary, ...]]` SHALL retain their
existing public signatures and exact `issue search <query> --output json`
mapping. The decoder SHALL accept the `v0.4.20` object envelope containing an
`issues` array and SHALL continue accepting the legacy top-level issue array.
`IssueSummary` SHALL expose `match_source: str | None = None`; the field SHALL
remain an open string, SHALL preserve values returned by upstream, and SHALL
default to `None` when omitted. Envelope pagination/count metadata is not a new
public return type in this change.

#### Scenario: v0.4.20 search envelope returns the existing tuple
- **WHEN** `issue search --output json` returns `{"issues":[...],"total":1}`
- **THEN** `issues.search()` returns a one-item immutable tuple of `IssueSummary` rather than exposing a new result wrapper

#### Scenario: Search match source is preserved
- **WHEN** search rows report `match_source` values `title`, `description`, or `comment`
- **THEN** each corresponding `IssueSummary.match_source` preserves the returned string

#### Scenario: Number-shaped query remains a normal query
- **WHEN** `issues.search("412")` returns a number-only match whose upstream fallback source is `comment`
- **THEN** argv contains the exact query `412` and the returned summary exposes `match_source == "comment"`

#### Scenario: Missing match source is backward-compatible
- **WHEN** an envelope or legacy array row omits `match_source`
- **THEN** the row decodes successfully with `IssueSummary.match_source is None`

#### Scenario: Unknown future match source is readable
- **WHEN** a future CLI returns an unrecognized nonempty `match_source` string
- **THEN** decoding succeeds and preserves that string without an SDK enum update

### Requirement: Upstream-owned runtime and model values remain open

Public fields and inputs whose vocabulary is controlled by Multica runtimes or
providers SHALL use `str` or `str | None`, not a closed SDK enum. This includes
runtime/provider/model response fields and agent-copy model, thinking-level,
and service-tier overrides. Closed SDK workflow enums such as issue status are
unchanged.

#### Scenario: Unknown provider and model decode
- **WHEN** a valid upstream response contains provider and model strings unknown at SDK release time
- **THEN** the typed model decodes successfully and preserves both strings

#### Scenario: Future runtime-specific copy values pass through
- **WHEN** agent copy receives previously unknown model, thinking-level, or service-tier strings
- **THEN** command construction accepts and emits them verbatim for upstream validation

## MODIFIED Requirements

### Requirement: Corrected profile, repository, and runtime surfaces
The SDK MUST expose only source-governed D15–D17 surfaces. `users.profile_get`
returns immutable `UserProfile`; `users.profile_update(UserProfileUpdate)`
updates only a present description. `repositories.list/add/remove` use
immutable URL/description records and multi-URL mutation results.
`repositories.get` and `repositories.checkout` MUST be absent: checkout is a
daemon-task workflow, not a configured SDK server operation. `runtimes.get`
MUST be absent; usage/activity return immutable tuples, usage validates
`1 <= days <= 365`, update requires target-version with optional wait, rename
supports machine, and delete supports cascade. `runtimes.delete(...,
cascade=True)` SHALL mean that active dependent agents are unbound, their
queued/running tasks are cancelled, and the runtime is deleted; agent
configuration, chats, and task history SHALL remain preserved so the agents
can later be attached to another runtime. No SDK documentation SHALL describe
cascade deletion as destroying or archiving those agents.

#### Scenario: D15–D17 discovery is exact
- **WHEN** public resources and the approved contract are inspected
- **THEN** every approved D15–D17 symbol resolves with its approved signature, no removed legacy or daemon-only checkout symbol resolves, and each supported method has exactly one canonical transport vector

#### Scenario: Runtime cascade preserves agents
- **WHEN** `runtimes.delete(runtime_id, cascade=True)` is executed against Multica `v0.4.20`
- **THEN** argv contains `runtime delete <runtime-id> --cascade`, the runtime is deleted after dependent agents are unbound and their active work is cancelled, and those agents retain configuration, chats, and task history

#### Scenario: Runtime delete without cascade preserves the refusal
- **WHEN** dependent active agents exist and `runtimes.delete(runtime_id)` omits cascade
- **THEN** the operation raises the classified upstream conflict and does not imply that retrying will delete or archive the agents

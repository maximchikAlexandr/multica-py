## MODIFIED Requirements

### Requirement: Corrected profile, repository, and runtime surfaces
The SDK MUST expose source-governed profile, repository, and runtime surfaces.
`users.profile_get` and `users.profile_update` SHALL preserve every reviewed
public field and safe file/stdin content input. Repository list/add/remove
SHALL retain immutable URL/description records and mutation results, while
native `repositories.checkout` SHALL expose URL, optional ref, fresh behavior,
and the actual CLI-emitted checkout result through the controlled process
transport. Runtime list/usage/activity/update/rename/delete SHALL preserve the
reviewed records and controls, and `runtime_profiles` SHALL expose governed
list/create/update/delete/set-path/unset-path operations. No surface SHALL
invent server-only fields or reimplement CLI-local orchestration.

#### Scenario: Profile repository and runtime discovery is complete
- **WHEN** public resources and the approved contract are inspected
- **THEN** every reviewed public profile, repository, repository-checkout, runtime, and runtime-profile operation resolves with one approved signature and canonical vector

#### Scenario: Runtime cascade preserves agents
- **WHEN** `runtimes.delete(runtime_id, cascade=True)` executes against a compatible CLI
- **THEN** the exact governed cascade argv is used and agent configuration, chats, and task history remain preserved

#### Scenario: Runtime delete without cascade preserves refusal
- **WHEN** dependent active agents exist and cascade is omitted
- **THEN** the operation raises the classified upstream conflict without implying destructive retry behavior

## ADDED Requirements

### Requirement: Broken advertised contracts are corrected at the public boundary
Daemon status/disk usage/stop/restart, auth status/logout, project resources,
recent comments, comment cursors, attachment upload/download/download-bytes,
and squad member add/remove SHALL match the pinned CLI's actual argv,
transport, output, and response shapes. The SDK SHALL NOT append an unsupported
`--output` flag or fabricate a JSON result for a text or lifecycle operation.

#### Scenario: Native mismatch fixtures pass through public methods
- **WHEN** source-linked native fixtures and stderr samples exercise the listed regressions
- **THEN** public methods preserve the actual state, cursor, metadata, member flag mapping, and payload fields without shape errors or silent defaults

### Requirement: Every public domain operation has typed coverage
The SDK SHALL expose typed operations for repository checkout; agent env
get/set and skills add; workspace create/update/member invite; squad
create/update/delete/member set-role/activity; issue timeline; autopilot trigger
URL rotation; chat history/thread; issue wakeups; and runtime profiles. Existing
equivalent typed operations SHALL be reused and duplicate wrappers SHALL NOT be
added without a semantic difference.

#### Scenario: Typed discovery matches the approved inventory
- **WHEN** public method discovery is compared with all `typed` and `typed-equivalent` inventory rows
- **THEN** each row resolves exactly once and no public domain capability relies only on raw argv

### Requirement: Existing operations expose all behavior-affecting inputs
Every existing typed operation SHALL expose or cite a proven typed equivalent
for each public behavior-affecting positional input and flag. This includes the
input gaps C1 through C24 in GitHub issue #93, global and inherited controls,
atomic create/update controls, pagination and compact/folding controls, file or
stdin content, foreground/streaming controls, daemon configuration, and
download timeout. Presentation-only spellings SHALL be inventoried without
duplicating Python parameters.

#### Scenario: Presence-sensitive inputs are explicit
- **WHEN** omission, null, empty string, zero, false, or an explicit clear have different CLI behavior
- **THEN** the public signature and approved contract preserve those states with `Unset` or another existing explicit representation and tests cover each supported state

#### Scenario: Content channels use one safe Python contract
- **WHEN** comment, skill, agent-env, skill-file, or user-profile content supports inline, file, or stdin CLI channels
- **THEN** the SDK exposes one typed safe-content design that preserves bytes/text, redaction, preview, and execution without giant argv or per-command abstractions

### Requirement: Public models preserve emitted fields and variants
Public models SHALL preserve every reviewed CLI-emitted field and nested record
for daemon, runtime, workspace, squad, project, project resource, autopilot
trigger, property, agent, attachment, version, comment, and all other audited
responses. Models SHALL preserve field absence separately from explicit null or
empty where the CLI does, and secret-bearing fields SHALL require explicit
opt-in and remain redacted from previews, reprs, logs, and errors.

#### Scenario: Rich records round-trip without data loss
- **WHEN** a native response contains any reviewed field from D1 through D17
- **THEN** the public result exposes the field with its reviewed type, nesting, presence, and redaction semantics

#### Scenario: Response variants remain discriminable
- **WHEN** daemon or another operation emits healthy, starting, stopped, conflict, aggregate, or lifecycle variants
- **THEN** the public result preserves enough typed state to distinguish the variants without fabricated defaults

### Requirement: Minimal existing architecture is reused
New coverage SHALL reuse `Command[T]`, `BaseResource` planning/finalizers,
`CliTransport`, existing page/action conventions, approved contract generation,
and frozen table-driven cases. It SHALL NOT add a workflow engine, generic
resource framework, second runtime registry, checkout-registry clone, or new
runtime dependency.

#### Scenario: A new family follows existing resource structure
- **WHEN** chat, wakeup, or runtime-profile support is added
- **THEN** it uses the existing resource/model/command patterns and introduces only family-specific validation and decoding required by the reviewed contract

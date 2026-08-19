## Context

Planning is based on repository `main` at `8cbe9cadcb81f179a382f6ec514124b00b1a9631`
after confirming it matches `origin/main`. The approved SDK contract still
targets Multica `v0.4.20` at `93342d04a7a9f788fec921e5aa736f86c7f22d8f`, GitHub
release ID `366120041`. The new authority is released tag `v0.4.28`:

- annotated tag object: `51e710d413171180330ac3826b0368f3313e63d0`
- tagged commit: `38c992ad0a757434fb51584fa34e3bc57d1b78e1`
- GitHub release ID: `371790559`
- darwin-arm64 CLI asset `multica-cli-0.4.28-darwin-arm64.tar.gz` published
  SHA-256 `e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf`

Feature work lives on `feat/multica-v0-4-28`. Planning artifacts and later
verification edits MUST be pushed on that branch via SSH.

Relevant current SDK gaps versus tagged `v0.4.28` CLI:

- No Plugin resource. Upstream `server/cmd/multica/cmd_plugin.go` adds
  `plugin init|validate|pack|install|list|status` and
  `plugin remote-mcp configure|test|approve|revoke`.
- No Property resource. Upstream `cmd_property.go` already had a catalog and
  `issue property` bag at `v0.4.20`; `v0.4.28` adds `actor` / `multi_actor`.
- No MCP library. `cmd_workspace.go` and `cmd_agent_mcp.go` add
  `workspace mcp` and `agent mcp` trees. Workspace MCP entries are write-only
  on the wire and routinely carry tokens.
- `SkillResource` has no `refresh`. Tagged CLI adds `skill refresh <id>`
  (`POST /api/skills/<id>/refresh`) for bulk update from source.
- `IssueStatus` keeps seven canonical members. `v0.4.28` lands per-workspace
  custom statuses over those categories. Decode preserves unknown names;
  `set_status` forwards `IssueStatus | str` to argv without a local membership
  check. This change does not add workspace-status CRUD.
- Assignee flags already exist; tagged CLI resolves `--assignee` including
  email. SDK currently forwards the string and does not document that.
- Canonical discovery currently requires an exact public-method set (163
  unique canonical methods on `main`). New operations change those stored
  counts; they MUST be recomputed, never allowlisted.

The existing maintainer pipeline remains the only promotion path:
`collect → validate --source-checkout → render → check`, with evidence under
ignored `.devlocal` storage.

## Goals / Non-Goals

**Goals:**

- Promote only the reviewed `v0.4.28` release contract and generate the exact
  default compatibility interval `[0.4.28, 0.4.29)`.
- Reconcile every retained approved operation against the pinned commit.
- Promote every tagged CLI family that is SDK-appropriate and currently
  missing, including Plugin, Property, Workspace/Agent MCP, and skill refresh.
- Classify every remaining tagged command as approved in this change or
  explicitly deferred with rationale (interactive, hidden, daemon-only,
  human-local, or secret-unsafe).
- Keep MCP credentials and Remote MCP secrets out of argv/preview by default.
- Keep all existing quality, contract, typing, and packaging gates green.

**Non-Goals:**

- Import behavior from upstream `main` after `38c992ad0a757434fb51584fa34e3bc57d1b78e1`.
- Desktop-only, UI-only, or npm skill-plugin host loops that have no `multica`
  Cobra command on the tagged CLI.
- Turning Plugin install into a Python HTTP client; the SDK stays CLI
  subprocess based.
- Merging issue properties into issue metadata.
- Restoring a plugin registry for execution backends (that is a different
  OpenSpec change already on `main`).
- Changing subprocess architecture, command-plan snapshots, or live-test
  gating.

## Decisions

### Decision 1: Full tagged command-tree reconciliation, then explicit deferrals

Run `scripts/upstream_contract.py collect` against a clean `v0.4.28` checkout
and the verified platform CLI. Review the collected tree plus `git diff
v0.4.20..v0.4.28 -- server/cmd/multica`. Every Cobra command is either:

1. already approved and only needs source-ref / mapping refresh;
2. newly approved in this change;
3. deferred in contract compatibility metadata with a one-line rationale.

Known new or previously ungoverned families that this change MUST approve
unless source proves they are hidden/interactive/human-local-only:

| CLI path | Proposed operation IDs |
|---|---|
| `plugin list\|status\|validate\|pack\|init\|install` | `plugins.list`, `plugins.status`, `plugins.validate`, `plugins.pack`, `plugins.init`, `plugins.install` |
| `plugin remote-mcp *` | `plugins.remote_mcp.configure\|test\|approve\|revoke` |
| `property list\|get\|create\|update\|archive\|unarchive` | `properties.list\|get\|create\|update\|archive\|unarchive` |
| `issue property list\|set\|unset` | `issues.properties.list\|set\|unset` |
| `workspace mcp list\|add\|update\|remove` | `workspaces.mcp.list\|add\|update\|remove` |
| `agent mcp list\|add\|enable\|disable\|remove` | `agents.mcp.list\|add\|enable\|disable\|remove` |
| `skill refresh` | `skills.refresh` |

`skill search` existed at `v0.4.20` and is still missing. If collect shows a
stable JSON shape, approve `skills.search` in this change; otherwise defer
with the missing-adapter reason.

Interactive `chat`, daemon lifecycle already covered, and commands that
`requireHumanLocalCommand` without a safe SDK mapping stay deferred or are
recorded as human-local the way repository checkout is recorded.

Alternative considered: promote only Plugin because the issue mentioned it.
Rejected: the issue requires mismatch repair and new resources/commands, and
MCP/property/skill-refresh are present on the same tagged CLI.

### Decision 2: Upgrade the approved contract before generating runtime behavior

Same pipeline as the `v0.4.20` change:

1. Pin `contracts/sdk-contract.json.target` to version/tag/commit/release
   `0.4.28` / `v0.4.28` / `38c992ad0a757434fb51584fa34e3bc57d1b78e1` /
   `371790559`.
2. Re-resolve every retained `source_refs` entry individually.
3. Add complete catalogs for newly approved operations with five-state
   presence, destinations, validators, adapters, and vectors.
4. `validate --source-checkout`, render tracked
   `src/multica_py/_generated/approved_sdk.py` plus ignored transients, then
   `check`.

Evidence stays under `.devlocal/upstream-contract/v0.4.20..v0.4.28/`.

### Decision 3: Plugin resource split by destination class

Add `MulticaClient.plugins` → `PluginResource` with eager/command pairs.

- **API JSON:** `list` and `status` map to `plugin list|status` with
  `--output json`. Workspace scope defaults to client `--workspace-id` the
  same way `client.agents.list()` / `Workspace.agents` do. Canonical argv
  tables list command tokens only and MUST NOT require a command
  `--workspace` flag on `list()`. If tagged CLI source shows a distinct
  command `--workspace` flag, expose it as an optional method kwarg mapped
  1:1 after that trace; it remains optional. `Workspace.plugins` uses
  `with_workspace(self.id)` like other unpaged workspace relations. Decode
  each list/status JSON row into one public frozen `Plugin` type. Do not
  ship a second public name (`PluginInstallation`) for the same row.
  Fields follow the CLI table plus JSON keys observed in source:
  `plugin_key`, `desired_version`, `lifecycle_status`, `trust_tier`,
  `uploader_id`, and any additional reviewed keys.
- **Local filesystem:** `init`, `validate`, `pack` run the CLI against a
  caller path. They are still subprocess operations with exact argv.
  `list`, `status`, `validate`, `pack`, and `init` emit `--output json`
  unless source proves a given command is non-JSON. `init` is
  `ActionResult` / path confirmation, not an HTTP entity. `validate` and
  `pack` decode a separate digest type (`plugin_key`, `version`,
  `manifest_digest`, `archive_digest`, `artifact_digest`, `size_bytes`,
  `file_count`) — not `Plugin`.
- **Install:** `install(source, *, workspace=Unset)` emits
  `plugin install <source>`. Source-trace `requireHumanLocalCommand`. If the
  tagged CLI refuses agent/daemon contexts, record the operation as
  human-local in the contract (same class as repository checkout): public
  method exists, offline tests cover argv and the reviewed refusal, live
  smoke stays gated.
- **Remote MCP:** `configure` requires `--endpoint` and uses
  `--credential-file` or `--credential-stdin` (mutually exclusive). Do not
  add a plaintext `--credential` string flag. `--credential-file` path is
  not a secret; collect stdin/file **contents** into `secret_values`.
  Redact credential bytes and endpoint auth headers from preview and
  diagnostics; executed argv still carries the file-path flag. `test`,
  `approve(--tool ...)`, `revoke` follow positional
  `<plugin-key> <contribution-key>`.

Do not invent a Python plugin registry or parse `multica.plugin.json` in the
SDK; the CLI owns packing and validation.

### Decision 4: Property catalog is distinct from issue metadata

Add `MulticaClient.properties` for workspace definitions and
`IssueResource.properties` (plus bound `Issue.properties`) for per-issue
values.

Catalog types at `v0.4.28`: `text`, `number`, `select`, `multi_select`,
`date`, `checkbox`, `url`, `actor`, `multi_actor`. Keep them as an open
string or a documented open enum that still decodes unknown future types.

`create` requires `--name` and `--type`. Repeatable `--option` is allowed
only for select types; actor types take no options. `update` is
presence-sensitive (`Flags().Changed` on name/description/icon/option);
empty `--icon` clears the icon — use `Unset` vs `""` vs `None` exactly as
source requires.

Issue `set` requires `--name` and `--value`. Actor values resolve through
the CLI assignee/member resolver (`member:<id>` form in source). The SDK
passes the caller string through `--value` after documenting the per-type
forms; it does not pre-resolve emails unless source shows the CLI will not.

`Issue.properties` is a `LazyMapping` keyed by property name, loaded by
`issue property list <issue-id> --output json`. It MUST NOT share storage
or types with `Issue.metadata`.

### Decision 5: MCP library uses secret-safe inputs and write-only list rows

Add methods on `WorkspaceResource` / bound `Workspace.mcp_servers` and
`AgentResource` / bound `Agent.mcp_servers`.

Workspace `mcp list` JSON MUST NOT be documented as containing server
config/tokens; decode only the reviewed public fields (`id`, `name`,
transport summary, and whatever list JSON actually emits after source
trace). Canonical argv for `workspace mcp list` is command tokens only
(`workspace mcp list --output json`); bound `Workspace.mcp_servers` scopes
via `with_workspace(self.id)` / client `--workspace-id`, not a required
command `--workspace` flag. `add`/`update` accept exactly one of
`server_config_file`, `server_config_stdin`, or (discouraged)
`server_config` string. Prefer the file/stdin pair in public signatures.
`--server-config` inline JSON is a secret; `--server-config-file` path is
not. Collect inline JSON (and stdin/file contents when those channels
carry config) into `secret_values`. Do not redact the file-path flag.
`agent mcp add|enable|disable|remove` take agent id and server id only.
MCP mutations emit `--output json` unless source proves a non-JSON command.

Do not copy MCP config through `agents.copy`; that exclusion from `v0.4.20`
stays.

### Decision 6: Issue status construction vs decode

Keep the seven canonical `IssueStatus` members. Do not add workspace-status
CRUD.

- **Decode** (get/list/`Issue.status`/`_IssueWire.status`):
  `IssueStatus | str`. Unknown names are preserved; decoding MUST NOT
  crash in the enum constructor.
- **All issue status inputs** (direct list fields, `IssueListFilter`,
  resource `set_status`, bound `Issue.set_status`): accept
  `IssueStatus | str` and pass the value through to argv without a local
  enum membership check for unknown custom names. Invalid names fail at
  the CLI after construction. Keep `TypeError` for non-str/non-enum.
  `"open"` remains a documentation anti-example of a non-status spelling,
  not a local `ValueError` oracle. This is one rule for list and
  `set_status`; do not keep `_normalize_issue_status` / closed-enum
  `ValueError` on either path.
- **ProjectStatus** stays closed exact-enum normalization (`ValueError`
  for unknown strings).
- This change MODIFIES the existing sdk-surface requirement **Public
  status inputs normalize exact enum values**. Whether tagged CLI accepts
  custom names is a source mapping note, not a second SDK rule.
- Any reviewed category field is an optional open string on issue models
  and defaults to `None` when omitted.

`--assignee` continues to be a single string flag. Add a canonical vector
where the value is an email if source resolves email; do not add a second
`assignee_email` parameter.

### Decision 7: Bound relations grow by five reviewed rows

Raise the normative inventory from 33 to 38:

| ID | Member | Operation |
|---|---|---|
| R34 | `Workspace.plugins` | `plugins.list` |
| R35 | `Workspace.properties` | `properties.list` |
| R36 | `Workspace.mcp_servers` | `workspaces.mcp.list` |
| R37 | `Agent.mcp_servers` | `agents.mcp.list` |
| R38 | `Issue.properties` | `issues.properties.list` |

R25 `Issue.metadata` is unchanged. Completeness tests must use the new
count with no allowlist.

### Decision 8: Table-driven coverage and recomputed discovery counts

Add `ArgvCase` / `DecodeCase` / `CommandCase` rows for every new canonical
method. Distinct secret-redaction, human-local refusal, and actor-value
encoding stay as dedicated tests. Recompute
`test_discovered_public_methods` expected sets from the final tables.

## Risks / Trade-offs

- [Custom statuses are flagged-off] → Keep seven `IssueStatus` members;
  widen decode and `set_status` string pass-through. Do not invent
  workspace-status CRUD.
- [Plugin install / remote-mcp are human-local] → Record the CLI guard;
  do not fake success in offline tests.
- [MCP tokens in argv] → Default to file/stdin; redact inline
  `--server-config` JSON and credential **contents**, not `--credential-file`
  or `--server-config-file` paths.
- [Property catalog existed at 0.4.20] → Treat as overdue coverage, not
  optional polish.
- [Relation count change breaks completeness] → Update inventory, tests,
  and docs in the same change.
- [Evidence mistaken for approval] → Collect remains review-only.

## Migration Plan

1. Land OpenSpec on `feat/multica-v0-4-28` and keep pushing verification
   edits to that branch.
2. Implementer collects evidence, amends `sdk-contract.json`, generates
   runtime, adds resources/tests/docs.
3. Compatibility docs state `[0.4.28, 0.4.29)`. Consumers on CLI `< 0.4.28`
   stay on the previous SDK release.
4. Rollback is reverting the PR; no server migration.

## Open Questions

None blocking planning. Issue status construction vs decode is decided in
Decision 6; implementer does not choose between local seven-value
validation and CLI-after-construction. Implementer MUST still trace, at
the pinned commit:

1. Whether issue JSON includes a category field (optional open string).
   Custom-name acceptance by tagged CLI is a mapping note, not a fork of
   Decision 6.
2. Exact `requireHumanLocalCommand` callers in `cmd_plugin.go`.
3. Workspace MCP list JSON fields after the write-only boundary.
4. Issue property list/set JSON shapes for actor values.
5. Whether `skill search` JSON is stable enough to approve now (tasks 2.6
   only: approve or defer; do not invent extra CLI families).
6. Whether tagged `plugin` / `workspace mcp` expose a distinct command
   `--workspace` flag (optional kwarg only; never required on `list()`).

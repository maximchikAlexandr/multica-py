# v0.4.28 Command Inventory (Block 1)

Authority collected 2026-08-18 for change `update-multica-v0-4-28`. Decisions
1–7 in `design.md` are binding; this file records the reviewed disposition of
every tagged `v0.4.28` CLI family before contract reconciliation (tasks 2.x).

## Authority pins

| Item | Value |
| --- | --- |
| Upstream checkout (absolute) | `/Users/alexandr/local_dev/repositories/my_projects/multica-py/.devlocal/upstream-contract/source/v0.4.28` |
| `git describe --tags --exact-match` | `v0.4.28` |
| `git rev-parse HEAD` | `38c992ad0a757434fb51584fa34e3bc57d1b78e1` |
| GitHub release ID | `371790559` |
| CLI asset | `multica-cli-0.4.28-darwin-arm64.tar.gz` |
| Asset SHA-256 (tarball, `checksums.txt`) | `e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf` |
| Binary SHA-256 (extracted `multica`) | `26a722384d8ef39a30cb83fec4e76f3185768369536d1f13a546b03e6c7fbeb9` |
| Platform | `darwin` / `arm64` |
| `multica version --output json` | `.devlocal/upstream-contract/release/v0.4.28/version-output.json` |

## Collect evidence

| Path | Contents |
| --- | --- |
| `.devlocal/upstream-contract/v0.4.20..v0.4.28/collect/evidence.json` | Declarative Cobra facts (`schema_version` 1) |
| `.devlocal/upstream-contract/v0.4.20..v0.4.28/collect/review-items.json` | Fail-closed review items (55 199 rows) |

Collect command:

```text
uv run python scripts/upstream_contract.py collect \
  --source-checkout .devlocal/upstream-contract/source/v0.4.28 \
  --binary .devlocal/upstream-contract/release/v0.4.28/multica \
  --tag v0.4.28 --version 0.4.28 --commit 38c992ad0a757434fb51584fa34e3bc57d1b78e1 \
  --release-id 371790559 --asset-name multica-cli-0.4.28-darwin-arm64.tar.gz \
  --sha256 26a722384d8ef39a30cb83fec4e76f3185768369536d1f13a546b03e6c7fbeb9 \
  --os darwin --arch arm64 \
  --version-output .devlocal/upstream-contract/release/v0.4.28/version-output.json \
  --output-dir .devlocal/upstream-contract/v0.4.20..v0.4.28/collect
```

Review-item codes: `IMPERATIVE_VALIDATION` 49 681, `DYNAMIC_ENUM` 4 100,
`UNKNOWN_PATTERN` 1 109, `UNRESOLVED_HELPER` 170, `PRESENCE_SENSITIVE` 139.
All remain review-only; none promote public SDK behavior.

## Source diff reviewed

`git diff v0.4.20..v0.4.28 -- server/cmd/multica` (37 files, +5 543 / −175 lines).
Material SDK-facing deltas:

- **New:** `cmd_plugin.go` (plugin + remote-mcp trees)
- **Extended:** `cmd_property.go` (actor / multi_actor types; issue property bag)
- **Extended:** `cmd_workspace.go` (workspace MCP CRUD)
- **New:** `cmd_workspace_mcp_test.go`, agent MCP in `cmd_agent_mcp.go`
- **Extended:** `cmd_skill.go` (`skill refresh`)
- **Extended:** `cmd_issue.go` (custom status pass-through, assignee email resolution)
- **New:** `cmd_chat.go` (interactive chat history/thread)
- **Daemon/profile:** additional human-local guards and tests (no new SDK surface)

## Newly approved in this change

Per Decision 1; operation IDs to be added in task 2.3–2.6.

| CLI path | Operation ID(s) | Notes |
| --- | --- | --- |
| `plugin list` | `plugins.list` | JSON rows → `Plugin` |
| `plugin status` | `plugins.status` | JSON rows → `Plugin` |
| `plugin validate` | `plugins.validate` | Local digest type |
| `plugin pack` | `plugins.pack` | Local digest type |
| `plugin init` | `plugins.init` | Local `ActionResult` |
| `plugin install` | `plugins.install` | Human-local (`requireHumanLocalCommand`) |
| `plugin remote-mcp configure` | `plugins.remote_mcp.configure` | Human-local; credential file/stdin |
| `plugin remote-mcp test` | `plugins.remote_mcp.test` | Human-local |
| `plugin remote-mcp approve` | `plugins.remote_mcp.approve` | Human-local |
| `plugin remote-mcp revoke` | `plugins.remote_mcp.revoke` | Human-local |
| `property list\|get\|create\|update\|archive\|unarchive` | `properties.*` | Catalog incl. actor types |
| `issue property list\|set\|unset` | `issues.properties.*` | Distinct from metadata |
| `workspace mcp list\|add\|update\|remove` | `workspaces.mcp.*` | Write-only list decode |
| `agent mcp list\|add\|enable\|disable\|remove` | `agents.mcp.*` | Agent-scoped |
| `skill refresh` | `skills.refresh` | `POST /api/skills/<id>/refresh` |
| `skill search` | `skills.search` | Stable JSON array (`name`, `url`, `source`, `installs`, `description`) at pinned commit |

## Retained from v0.4.20 contract

Existing operation IDs are retained only when the exact tagged Cobra leaf or a
source-proven replacement exists. Representative
families: agents, issues (incl. search/copy deltas), projects, skills (except
refresh/search), workspaces (list/get/members/switch), runtimes, daemon
subset, auth, setup, attachments, repositories (list/add/remove only), squads,
labels, autopilots, configuration, maintenance.

The post-implementation audit corrected retained drift:

| Prior SDK operation | v0.4.28 disposition |
| --- | --- |
| `auth.login` → `auth login` | Retained and remapped to root `login` |
| `configuration.get(key)` → `config get` | Retained only as no-arg compatibility alias of `config show` |
| `issues.deprioritize` | Removed; tagged Cobra tree has no equivalent leaf |
| `workspaces.watch`, `workspaces.unwatch` | Removed; tagged Cobra tree has no equivalent leaves |

Issue status/assignee behavior **changes** decode/construction policy per
Decision 6 but retains `issues.set_status`, `issues.list`, and assignee argv
mappings.

## Explicitly deferred

| CLI family / command | Rationale |
| --- | --- |
| `chat history`, `chat thread` | Interactive; requires in-task chat context (`MULTICA_TASK_ID`); family `chat-read` stays `separate_extension_candidate` |
| `repo checkout` | Human-local daemon worktree control; not in v0.4.20 contract |
| `workspace create`, `workspace update`, `workspace member invite` | Out of governed workspace subset; CLI-only |
| `agent create`, `agent update`, `agent archive`, `agent restore`, `agent env get`, `agent env set`, `agent skills add` | CLI-only lifecycle/environment mutation; SDK exposes reviewed list/get/copy/skills/tasks/avatar/MCP subset only |
| `issue create`, `issue update`, `issue assign`, `issue delete`, reorder variants not in contract | Partial issue subset governed; remainder CLI-only |
| `project create`, `project delete`, status CRUD | Project subset governed; workspace-status CRUD explicitly out of scope |
| `skill create`, `skill update`, `skill delete`, `skill import` | Governed subset is list/get/files; create/update/delete/import remain CLI-only |
| `squad create`, `squad update`, `squad delete`, member set-role, `squad activity` | Squad subset is get/list/members add/remove |
| `label *` (full CRUD) | Not in approved contract |
| `autopilot create/update/delete` and trigger-* except governed trigger | Partial autopilot subset |
| `login`, `logout` (direct command ownership) | Human-local auth; SDK wrappers map to root `login` and `auth logout` respectively |
| `setup *` | Human-local interactive bootstrap |
| `daemon start/stop/restart/logs/probe-runtimes` | Human-local or daemon-managed; SDK exposes status/disk-usage/start/stop subset per existing contract |
| `runtime profile create/list/update/delete/set-path/unset-path` | Human-local profile administration |
| `attachment upload` (chat-task context) | Chat-task scoped; SDK attachment paths are issue-comment scoped |
| `config *`, `update`, `version`, `user *` | Configuration/maintenance subset only (`configuration.*`, `maintenance.*`, `users.profile_*`) |
| Hidden `x` maintenance | Hidden command |
| Desktop/npm-only surfaces | No tagged Cobra command |

## Unknown / review-required patterns

Collected evidence marks imperative validation, presence-sensitive flags, and
dynamic enums across retained and new commands. Each becomes a contract review
item during tasks 2.3–2.8 (validators, presence policy, adapters). Notable
new-family traces still requiring manual `RunE` review:

- `cmd_plugin.go`: `requireHumanLocalCommand` on install and all remote-mcp ops
- `cmd_property.go`: `Flags().Changed` on update; actor option rejection
- `cmd_workspace.go`: `resolveMcpJSONObject` exactly-one config channel
- `cmd_issue.go`: custom status name pass-through; `--assignee` email resolution

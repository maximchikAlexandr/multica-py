## 1. Collect and Review the v0.4.28 Authority

- [x] 1.1 Create a clean, read-only upstream checkout at tag `v0.4.28`; verify `git describe --tags --exact-match` and `git rev-parse HEAD` resolve to `v0.4.28` / `38c992ad0a757434fb51584fa34e3bc57d1b78e1`, and record the absolute checkout path.
- [x] 1.2 Download the platform-matching CLI asset from GitHub release `371790559` into ignored `.devlocal` storage, verify its SHA-256 against `checksums.txt` (darwin-arm64 `multica-cli-0.4.28-darwin-arm64.tar.gz`: `e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf`), extract it, and capture the exact `multica version --output json` bytes beside the binary.
- [x] 1.3 Run `scripts/upstream_contract.py collect` with tag `v0.4.28`, version `0.4.28`, commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`, release ID `371790559`, and the verified asset/checksum/OS/architecture; confirm evidence stays under ignored `.devlocal` output.
- [x] 1.4 Review the collected command tree plus `v0.4.20..v0.4.28` CLI source; produce an approved / deferred inventory covering plugins, properties, issue properties, workspace MCP, agent MCP, skill refresh, skill search, chat, and every other tagged command. Record unknown patterns as review items.

## 2. Reconcile the Approved SDK Contract

- [x] 2.1 Update `contracts/sdk-contract.json.target` to version/tag/commit/release `0.4.28` / `v0.4.28` / `38c992ad0a757434fb51584fa34e3bc57d1b78e1` / `371790559` and point `release_provenance_ref` at the ignored `v0.4.20..v0.4.28` evidence location.
- [x] 2.2 Re-resolve every retained `source_refs` entry against the pinned checkout: update commit, path, symbol, and line range individually, and add a contract test that no current target/source ref retains `93342d04a7a9f788fec921e5aa736f86c7f22d8f`.
- [x] 2.3 Add complete catalogs for `plugins.list|status|validate|pack|init|install` and Remote MCP configure/test/approve/revoke, tracing destinations and `requireHumanLocalCommand` guards.
- [x] 2.4 Add complete catalogs for `properties.*` and `issues.properties.*`, including `actor` / `multi_actor`, option constraints, icon-clear presence, and `--value` encoding.
- [x] 2.5 Add complete catalogs for `workspaces.mcp.*` and `agents.mcp.*`, including exactly-one config-channel constraints and write-only list fields.
- [x] 2.6 Add `skills.refresh` (and `skills.search` if the inventory approved it); otherwise record the deferral rationale in compatibility metadata.
- [x] 2.7 Refresh issue status, assignee, and error-classification source refs for `v0.4.28`. Map `set_status` as `IssueStatus | str` pass-through (CLI validates unknown names). Record email-assignee as approved mapping or explicit non-support. Do not add workspace-status CRUD.
- [x] 2.8 Run `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout <absolute-v0.4.28-checkout>` and resolve every failure before generation.

## 3. Implement Plugin and Property Surfaces

- [x] 3.1 Add frozen `Plugin` list/status row model, a distinct digest type for validate/pack, and `PluginResource` on `MulticaClient.plugins` with list/status/validate/pack/init/install eager and command methods matching Decision 3 (`Plugin` only for the JSON row; no second public name). Register `PluginResource` in `RESOURCE_SPECS` and `__init__` / docs exports the same way as `AgentResource`.
- [x] 3.2 Implement Remote MCP configure/test/approve/revoke with file/stdin credential exclusivity, `--endpoint` required, `--tool` at-least-one, and redaction of credential **contents** (not `--credential-file` path).
- [x] 3.3 Add `PropertyDefinition` / `PropertyValue` models and `PropertyResource` for catalog list/get/create/update/archive/unarchive with `Unset` update presence and actor option rejection. Register `PropertyResource` in `RESOURCE_SPECS` and `__init__` / docs exports the same way as `AgentResource`.
- [x] 3.4 Add nested `IssuePropertyResource` at `client.issues.properties` (list/set/unset distinct from metadata), bound `Issue.properties` as `LazyMapping`, plus `__init__` / docs exports.
- [x] 3.5 Register `IssuePropertyResource` in `tests/cases/operations.py` `RESOURCE_SPECS` and `_NESTED_RESOURCE_ATTRS` mirroring `issues.metadata` → `IssueMetadataResource`.

## 4. Implement MCP, Skill Refresh, and Status Decoding

- [x] 4.1 Add nested workspace MCP list/add/update/remove on `WorkspaceResource` and bound `Workspace.mcp_servers`, enforcing one config channel and public-only list decoding; register the nested MCP resource in `RESOURCE_SPECS` / `_NESTED_RESOURCE_ATTRS` and `__init__` / docs exports.
- [x] 4.2 Add nested agent MCP list/add/enable/disable/remove on `AgentResource` and bound `Agent.mcp_servers`; register that nested surface the same way; emit `--output json` on MCP mutations unless source proves a non-JSON command.
- [x] 4.3 Add `SkillResource.refresh` / `refresh_command` emitting `skill refresh <id> --output json`.
- [x] 4.4 Apply Decision 6 as one rule for every issue status input (direct list fields, `IssueListFilter`, resource/bound `set_status`): keep seven `IssueStatus` members; decode get/list/`Issue.status`/`_IssueWire.status` as `IssueStatus | str` without constructor crash; construction passes `IssueStatus | str` to argv without local membership check (`TypeError` for non-str/non-enum); stop using `_normalize_issue_status` / `ISSUE_INVALID_STATUS_CASES` local `ValueError` for unknown strings on list or set_status; ProjectStatus stays closed; do not add workspace-status CRUD; add assignee-email vectors if source accepts email on `--assignee`.
- [x] 4.5 Wire relations R34–R38 (`Workspace.plugins` via `with_workspace(self.id)` like other unpaged workspace relations) and update relation-inventory completeness from 33 to 38 with no allowlist.
- [x] 4.6 Extend `collect_secret_values` so `--credential-file` and `--server-config-file` paths are not secrets, stdin/file contents and inline `--server-config` JSON are collected, plaintext `--credential` is not added; add unit tests for those cases.

## 5. Generate Runtime, Tests, and Documentation

- [x] 5.1 Render `contracts/sdk-contract.json` to `src/multica_py/_generated/approved_sdk.py` with ignored transient output; verify generated min/target/max are `0.4.28` / `0.4.28` / `0.4.29`.
- [x] 5.2 Render a second time and compare hashes to prove deterministic bytes; run `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json`.
- [x] 5.3 Add table-driven `ArgvCase` / `DecodeCase` / `CommandCase` rows for every new canonical method; keep human-local refusal, actor encoding, and MCP/plugin secret redaction as dedicated tests.
- [x] 5.4 Recompute discovered canonical method, unique case, noncanonical variant, and legacy-migration counts from the final tables and update stored constants so `test_discovered_public_methods` is exact equality.
- [x] 5.5 Update `docs/api.md`, `docs/migration.md`, `docs/compatibility.md`, and maintainer/release text to `v0.4.28` / `[0.4.28, 0.4.29)` and document Plugin, Property, MCP, and skill refresh.

## 6. Verification and Delivery Gates

- [x] 6.1 Run focused tests for plugins, properties, MCP, skills, issues, relations, transport redaction, compatibility, and upstream contract; fix discovery/count/type failures before the full suite.
- [x] 6.2 Re-run `collect → validate --source-checkout → render → check` from clean ignored evidence paths and verify tracked output excludes binaries, evidence, and transients.
- [x] 6.3 Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy src`, and `uv run mypy tests`; resolve every failure without suppressing new errors.
- [x] 6.4 Run `uv run pytest -m "not live" --collect-only` and verify no `tests/live/*` node is collected, then run `uv run pytest -m "not live"`.
- [x] 6.5 Run `uv build`, packaging tests, and `openspec validate update-multica-v0-4-28 --json`; confirm `git diff --check` is clean of secrets and unrelated files.

## 7. Close Post-Implementation Migration Audit

- [x] 7.1 Correct Plugin init/list/status and Remote MCP public-config argv against the pinned binary/source; add exact negative and positive vectors.
- [x] 7.2 Correct Workspace MCP remove text semantics and add bound Agent/Workspace MCP mutation cache invalidation with focused tests.
- [x] 7.3 Remap or remove retained SDK operations whose Cobra leaves are absent at `v0.4.28`, including root login, configuration get semantics, issue deprioritize, and workspace watch/unwatch.
- [x] 7.4 Reconcile every affected contract signature, binding, destination, validator, source ref, response adapter, canonical vector, public-method count, generated runtime, and documentation.
- [x] 7.5 Classify every remaining tagged Cobra leaf as approved, retained, or explicitly deferred; add a regression that compares approved command paths with the pinned command tree.
- [x] 7.6 Run focused source/binary regressions, `collect → validate → render → check`, and the complete `make pr` gate without suppressions.
- [x] 7.7 Push the remediation commit and verify all required GitHub checks are green at the pushed feature HEAD.

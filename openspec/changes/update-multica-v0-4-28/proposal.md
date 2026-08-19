## Why

The approved SDK contract still certifies Multica `v0.4.20`, so it neither
covers tagged `v0.4.28` nor exposes CLI families added after that baseline:
workspace-private Plugins, workspace/agent MCP libraries, skill refresh from
source, and the still-ungoverned Property catalog. The `v0.4.28` release is
now the required compatibility target, and the SDK needs a source-traced
full-tree upgrade rather than a cherry-picked subset of changelog bullets.

## What Changes

- Move the reviewed upstream target from Multica `v0.4.20` to tagged release
  `v0.4.28` (annotated tag object `51e710d413171180330ac3826b0368f3313e63d0`,
  tagged commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`, GitHub release ID
  `371790559`) and regenerate the approved runtime compatibility projection for
  `[0.4.28, 0.4.29)`.
- Reconcile every retained approved operation against the pinned `v0.4.28`
  source and verified release binary: re-resolve every `source_refs` path,
  symbol, and line range, and update argv/response adapters wherever the tagged
  CLI drifted.
- Add a public Plugin resource for the tagged `plugin` command family, covering
  list/status plus the reviewed local pack/validate/init paths, with explicit
  policy for human-local install and secret-bearing Remote MCP configure.
- Add a public Property resource for the tagged `property` catalog and
  `issue property` value commands, including `actor` / `multi_actor` types.
- Add governed Workspace MCP and Agent MCP operations for the tagged
  `workspace mcp` and `agent mcp` trees, using file/stdin secret channels rather
  than putting MCP JSON in argv.
- Add `skills.refresh` for tagged `skill refresh <id>`.
- Source-trace issue JSON category fields, `--assignee` email resolution, and
  actor property encoding at `v0.4.28`. All issue status **inputs** (direct
  list fields, `IssueListFilter`, resource and bound `set_status`) forward
  `IssueStatus | str` without local membership checks; decode preserves
  unknown names. Project status stays closed. Do not add workspace-status CRUD.
- Keep evidence, candidate listings, and transient generator output outside
  version control. Only the approved contract may change public generated
  behavior.
- Update API, compatibility, migration, and maintainer documentation plus
  table-driven unit, contract, component, and command-preview coverage. Recompute
  canonical method/case counts from the final tables with no allowlist.

## Capabilities

### New Capabilities

- `plugin-resource`: workspace-private Plugin entity, CLI mappings, local
  versus API operations, and Remote MCP contribution policy.
- `property-resource`: workspace Property catalog, issue property values,
  actor/multi-actor encoding, and presence semantics.

### Modified Capabilities

- `sdk-surface`: expose Plugin and Property resources, Workspace/Agent MCP
  methods, skill refresh, and reviewed status/assignee/property-type decoding
  without removing existing eager methods.
- `bound-resource-relations`: add reviewed lazy relations for plugins,
  properties, and MCP server lists; raise the normative inventory count by the
  approved new rows only.
- `upstream-contract`: promote `v0.4.28` as the pinned authority, require
  full command-tree reconciliation, and govern every newly approved operation.
- `subprocess-transport`: re-validate conflict/validation classification
  against `v0.4.28` and extend redaction to MCP credentials and plugin Remote
  MCP secrets.
- `verification-and-release`: cover the new resources, changed status/property
  contracts, compatibility interval, docs, and focused/full offline gates.

## Impact

- Approved/generated contract: `contracts/sdk-contract.json`, generated runtime
  projection, compatibility reports/docs, provenance fixtures, and contract
  validator/render/check workflows.
- Public SDK: new `PluginResource` and `PropertyResource` (plus issue-property
  accessors), Workspace/Agent MCP methods, `SkillResource.refresh`, issue
  status/assignee decoding, bound relations, and documentation. No existing
  eager method or return type is removed.
- Transport: secret redaction for MCP config and Remote MCP credentials;
  conflict/validation markers re-pinned to `v0.4.28` source. Subprocess
  execution, command-plan, and existing redaction boundaries stay intact.
- Tests/docs: table-driven operation inventory, model decoding, fake-CLI
  component cases, compatibility policy, API/migration/service documentation,
  and live-smoke inventory where applicable.
- External authority: tagged Multica `v0.4.28` source and verified release
  assets only; later upstream `main`, desktop-only, and UI-only changes remain
  out of scope.

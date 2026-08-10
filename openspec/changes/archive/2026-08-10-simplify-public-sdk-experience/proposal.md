## Why

The SDK has a strong typed command layer, but its public entry points still expose competing request-object and keyword APIs, partial issue objects, CLI-shaped mode flags, and configuration/file-handling special cases. Consolidating GitHub issues #33, #37, #38, #40, and #42 now gives ordinary Python and AI-assisted callers one discoverable path without weakening command inspection, validation, or advanced execution control.

## What Changes

- Allow `MulticaClient()` to use default `ClientConfig` values while preserving explicit `MulticaClient(ClientConfig(...))` construction.
- Add immutable `client.with_options(...)` views and typed per-operation `OperationOptions`, with operation overrides taking precedence over scoped-client and base configuration and with command plans snapshotting the effective configuration.
- **BREAKING**: remove the 23 one-operation input DTOs named in GitHub issue #42, their request-object overloads, exports, generic `_resolve_request` plumbing, and parity tests. Keep reusable specifications, semantic value objects, sentinels, enums, and output models.
- **BREAKING**: make explicit typed method parameters the sole public input form for affected eager and `*_command()` methods while preserving validation, `Unset`/`None` semantics, argv, plans, results, and eager/command signature parity.
- **BREAKING**: return bound `Issue` entities from issue list, search, and issue relations without extra `issue get` calls; retain optional search-match metadata on `Issue` and remove `IssueSummary` from the primary public API.
- Add bound `Issue` and `Project` continuation methods, explicit issue assignment/unassignment and move verbs, and project-scoped issue creation through `project.issues.create(...)` / `create_command(...)` with relation-cache invalidation.
- Unify path, bytes, and binary-file attachment inputs under `attachments.upload(...)` / `upload_command(...)`, retaining `upload_bytes(...)` only as a documented compatibility alias during migration.
- Add `client.cli.command(*argv, ...)` as a shell-free, non-interactive escape hatch returning the existing `Command` abstraction under the same configuration, redaction, timeout, and error contracts.
- Add configured issue and project permalinks using the reviewed Multica web routes `/{workspace_slug}/issues/{id}` and `/{workspace_slug}/projects/{id}`; fail clearly when app URL or workspace slug is unavailable rather than deriving either from API settings.
- **BREAKING**: reduce the package-root namespace to primary clients, commands, entities, common results/enums, and errors; advanced relation, wire/value, and compatibility types remain importable from dedicated modules.
- Rewrite README, API, migration, examples, operation contracts, and verification matrices around the single canonical API, including explicit migration guidance for removed DTOs and summary entities.

## Capabilities

### New Capabilities

- `raw-cli-escape-hatch`: Safe construction, inspection, and execution of unsupported non-interactive Multica argv through `client.cli.command(...)`.
- `entity-permalinks`: Explicitly configured, deployment-correct web permalinks for bound issues and projects.

### Modified Capabilities

- `sdk-surface`: Default client construction, scoped and per-operation options, typed-parameter-only operations, request DTO removal, unified attachment inputs, canonical bound issues, explicit domain verbs, and the reduced root namespace.
- `bound-resource-relations`: Full bound `Issue` values across collections, entity continuation actions, project-scoped issue creation, command inspection, and mutation cache invalidation.
- `subprocess-transport`: Effective-option snapshotting, raw argv safety, and temporary-file lifetime/cleanup for unified uploads.
- `verification-and-release`: Public inventory, typing, plan parity, no-N+1, cache, namespace, migration, and offline release gates for the breaking API cleanup.

## Impact

- Public API and models in `src/multica_py/client.py`, `config.py`, `__init__.py`, `models/`, and `resources/` change substantially; consumers using removed request DTOs, `IssueSummary`, old assignment/reorder modes, or root-level advanced imports must migrate.
- `contracts/sdk-contract.json`, its schema/generator, operation cases, and completeness checks must describe direct-only inputs, effective operation options, new domain entry points, and canonical `Issue` returns without deriving behavior from unapproved upstream evidence.
- Command plans and `CliTransport` remain the only subprocess path. The change adds no shell execution, HTTP transport, asynchronous client, persistence, or server/CLI behavior.
- Documentation, examples, static typing fixtures, unit/contract/component tests, packaging validation, and release notes are updated as one coordinated breaking release surface.

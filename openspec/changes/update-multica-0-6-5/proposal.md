## Why

The reviewed SDK contract stops at Multica `0.6.1`, while stable `0.6.5`
contains additive CLI and response changes that affect typed properties, project
workflows, daemon identity, wakeups, runtime privacy, uploads, and stable error
handling. A single source-pinned upgrade from exact SDK commit
`a96eecf3e12a88dd7b4d56e1aafae3285fb0990c` is required so consumers receive a
coherent compatibility claim without treating draft `0.6.2`/`0.6.3` work as an
effective baseline.

## What Changes

- Move the approved upstream contract, generated compatibility projection, and
  release documentation from Multica `0.6.1` commit
  `2ea01ae4ef55de4310b99af192d2dbd367832883` to stable `0.6.5` commit
  `654b8ca954034f8181eb6bbb4fc298dede760156`, preserving distinct release,
  archive, executable, and source provenance.
- Reconcile all 209 target CLI nodes and every positional argument, local flag,
  and persistent flag: four additions, no removals, and three changed nodes,
  with explicit `support`, `retain`, `adapt`, `remove`, `defer`, or
  `not_sdk_surface` dispositions.
- Adapt the existing typed SDK surface for `multi_text`/`multi_url` properties,
  JSON-array property input, `daemon status.cli_commit`, nullable project
  workflow identity, workflow-aware issue writes, wakeup diagnostics,
  self-hosted pull-request wakeups, runtime privacy conflicts, and stable
  upload/network/server errors.
- Reconcile all 196 supported response work items with one verdict, pinned old
  and target source references, and concrete fixture/test/documentation action;
  retain unchanged behavior without promoting evidence-only fields into the
  public API.
- Extend the existing contract generator, models, adapters, table-driven tests,
  documentation, packaging, and release gates only where the approved mappings
  require it. Keep `daemon autostart`, workflow-management HTTP endpoints, and
  daemon-internal/UI-only fields outside this delivery.
- Verify one direct `0.6.1 → 0.6.5` migration and one coherent rollback. No
  production implementation starts until independent plan verification and
  human approval.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: exact provenance, the 209-node inventory, argument/flag
  transport mappings, and the complete 196-item response audit advance from
  Multica `0.6.1` to `0.6.5`.
- `sdk-surface`: existing property, project, issue, daemon, wakeup, runtime, and
  error boundaries gain the reviewed additive fields and presence-sensitive
  behavior while deferred and non-CLI surfaces remain excluded.
- `verification-and-release`: deterministic generation, source-link audit,
  positive/negative tests, independent local verification, documentation,
  packaging, and rollback must prove the direct upgrade without tracked raw
  evidence or transient artifacts.

## Impact

The implementation will affect `contracts/sdk-contract.json`, its schema and
validator only if required, the generated approved SDK projection, existing
property/project/issue/daemon/wakeup/runtime models and adapters, their direct
and bound resource methods, shared operation/response fixtures, compatibility
documentation, and package/release checks. The existing Python/subprocess
architecture and dependencies remain in place. Collector output, upstream
checkouts, archives, binaries, diagnostic logs, screenshots, and the visual
explanation remain outside Git.

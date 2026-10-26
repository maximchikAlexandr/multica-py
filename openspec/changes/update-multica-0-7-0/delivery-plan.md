## Delivery basis

- `change_id`: `update-multica-0-7-0`
- `task_key`: `MYL-557`
- `implementation_baseline`: draft PR #101, branch
  `feat/MYL-474-update-multica-0.6.2`, exact head
  `b1c350ce22941a66871f11e0c5830a6ec542878c`
- `approved_integration_target`: exact `origin/main` snapshot
  `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`
- `composition`: start at the implementation baseline, then before product
  edits create one `--no-ff` merge whose second parent is the exact verified
  planning revision recorded by Plan Verifier; that parent descends from the
  approved integration target and carries the published OpenSpec input
- `baseline_state`: reviewed `0.6.2` implementation evidence; currently
  conflicts with `main` and is not treated as merge-ready
- `target`: Multica `0.7.0` at
  `dbdbb299164347586e2650bb67684a490726a798`
- `scope_basis`: remaining work from exact PR #101 head to this change's
  acceptance criteria; accepted `0.6.2` implementation is retained, not redone

PR #101 and its branch are preserved. PR #103 is controller-only evidence and
is not an implementation base. This plan does not modify either PR, issue
statuses, or duplicate records.

## E2E decision

`e2e_required=false`.

The remaining public behavior consists of deterministic contract reconciliation,
argument encoding, pre-I/O validation, payload decoding, typed error mapping,
redaction, generation, and package exports. Each observable result can be fully
asserted with existing fake-CLI, frozen unit/resource tables, component transport
tests, contract mutation/closure checks, package imports, and ordinary GitHub CI.
No requirement depends on a real database, browser, external service, interactive
TTY, changed human-visible output, or persistent environment state.

The unavailable project stand is not a waived necessary check: no remaining
verification gap requires it. No environment-based case, stand provisioning,
live identity, image, terminal capture, renderer input, or live cleanup is planned.
Tests SHALL use only repository-owned deterministic fixtures already appropriate
to their layer; unavailable server behavior SHALL be represented only by exact
source-reviewed payload fixtures, never by invented identities or operations.

## Verification commands and CI ownership

| Gate | Concrete command | Required assertion | CI disposition |
|---|---|---|---|
| Composition identity | `test "$(git rev-parse HEAD^1)" = b1c350ce22941a66871f11e0c5830a6ec542878c && test "$(git rev-parse HEAD^2)" = "$VERIFIED_PLANNING_SHA"` | composition first parent is exact PR #101 head and second parent is the planning SHA from the approved managed contract | required before product edits |
| Integration ancestry | `git merge-base --is-ancestor a96eecf3e12a88dd7b4d56e1aafae3285fb0990c HEAD^2 && git merge-base --is-ancestor a96eecf3e12a88dd7b4d56e1aafae3285fb0990c HEAD` | exact integration target reaches both planning input and composed line | required preflight in implementation PR |
| OpenSpec preservation | `git diff --exit-code HEAD^2 -- openspec/changes/update-multica-0-7-0/` | published OpenSpec input is byte-identical on composition commit | required before product edits and in final CI |
| Contract/source | `make contract` | approved contract validates and all source links are pinned | existing `contract-check` job |
| Generated freshness | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` | tracked projection equals approved contract; repeated render proof is covered by contract tests | existing contract job plus focused contract tests |
| Focused remaining delta | `uv run pytest -o addopts="" -q tests/unit/resources tests/unit/test_project_resource_models.py tests/unit/test_transport.py tests/component/test_issue_project_assignment.py tests/component/test_transport_errors.py tests/contract/test_sdk_contract.py` | all remaining adapters, validators, decoders, conflicts, and redaction paths pass | extend existing unit/component/contract jobs |
| Retained baseline | `uv run pytest -o addopts="" -q tests/unit/test_upstream_contract.py tests/unit/resources/test_properties.py tests/unit/resources/test_issue_wakeups_v2.py tests/unit/test_transport.py tests/packaging/test_generated_runtime.py` | accepted PR #101 behavior remains present unless an explicit adapt row exists | same ordinary CI revision |
| Lint/types | `make lint && make types` | formatting, lint, source/test/script typing pass | existing CI jobs |
| Complete offline suite | `make test && make compat` | all non-live and compatibility tests pass; no live node is selected | existing CI jobs; local run obeys workspace time limit |
| Package | `make package` | one wheel and one sdist build and pass isolated package tests | existing package workflow |
| OpenSpec | `openspec validate update-multica-0-7-0 --strict && openspec validate --specs --strict` | change and main specs are structurally valid | planning and implementation preflight |

Implementer owns new/changed tests, exact payload fixtures, generated projection,
docs, and CI assertions. Independent verification inspects the published exact
SHA, ancestry, CI results, package contents, and scenario mapping; it does not
edit implementation fixtures or substitute a live run.

## Scenario traceability

| Capability and scenario | Sufficient lower-level or CI proof | Owning tasks |
|---|---|---|
| upstream-contract — The implementation starts from another revision | exact first/second-parent, integration-ancestor, OpenSpec-tree, and retained public-surface assertions | 1.1, 1.6 |
| upstream-contract — Conflict resolution changes accepted behavior | PR #101 regression tables and generated binding comparison | 1.1, 1.6, 5.2 |
| upstream-contract — Provenance is incomplete or mixed | contract schema, mutation, checksum, and source-link cases | 1.2, 1.6 |
| upstream-contract — A target item lacks one decision | inventory/response closure and duplicate/missing mutation cases | 1.3, 1.6 |
| upstream-contract — An accepted 0.6.2 item is needlessly reimplemented | retained/adapt verdict audit against PR #101 references | 1.3, 5.2 |
| upstream-contract — A candidate has no traced behavior | destination/constraint/source validation rejects promotion | 1.4, 1.6 |
| upstream-contract — Generated output drifts | deterministic double-render and generated freshness assertions | 1.5, 5.3 |
| upstream-contract — A reviewed endpoint is checked | compatibility policy unit and package tests for `0.6.2` and `0.7.0` | 1.2, 5.3 |
| upstream-contract — A version exceeds the reviewed ceiling | strict/warn compatibility boundary cases | 1.2, 5.3 |
| public-cli-parity — Target help inventory is checked offline | 209-node closure and full flag/positional comparison | 1.3, 1.6 |
| public-cli-parity — Upstream-only behavior is discovered | forbidden-public-symbol and explicit exclusion assertions | 1.3, 5.2 |
| public-cli-parity — An accepted operation drifts | public discovery, signature, vector, binding, and fixture regressions | 1.1, 5.2 |
| public-cli-parity — A remaining adaptation is introduced | adapt row requires source, task, tests, and docs before contract validation passes | 1.3, 1.4, 5.1 |
| sdk-surface — Ordered comparisons are valid | ordered predicate unit/resource rows assert exact argv/query and call count | 2.1, 2.2 |
| sdk-surface — A comparison is ambiguous or unsupported | negative operator/type/value rows assert stable error and zero I/O | 2.1, 2.2 |
| sdk-surface — Workflow identity is omitted or null | project wire/public decoder fixtures for omitted/null/legacy payloads | 2.3, 2.5 |
| sdk-surface — A workflow-aware write succeeds | issue/project resource and component rows assert exact call and authoritative result | 2.4, 2.5 |
| sdk-surface — A workflow-aware write is rejected | validation/conflict fixtures assert no retry and no unrelated mutation | 2.4, 2.5 |
| sdk-surface — A PR-conflict wakeup is constructed | eager/command table rows assert identical exact argv and decode | 3.1, 3.2 |
| sdk-surface — Wakeup conditions conflict | exactly-one negative rows assert pre-I/O failure | 3.1, 3.2 |
| sdk-surface — Sharing identities are returned | runtime decoder/binding fixtures assert safe ordered identity shape | 4.1, 4.5 |
| sdk-surface — Privacy revocation is blocked | runtime conflict component rows assert typed safe context and unchanged state | 4.2, 4.5 |
| sdk-surface — An agent write lacks an explicit grant | agent authorization rows assert no retry and redacted typed failure | 4.3, 4.5 |
| sdk-surface — A reviewed allowlist failure occurs | workspace/transport payload rows assert stable safe exception fields | 4.4, 4.5 |
| sdk-surface — An unknown failure occurs | malformed/unknown payload rows assert retained generic fallback | 4.4, 4.5 |
| verification-and-release — Baseline reconciliation runs | exact parent/ancestor/OpenSpec-tree assertions plus retained discovery/vector/fixture suite | 1.1, 1.6, 5.2 |
| verification-and-release — Coverage reconciliation runs | 196-item response closure and test-reference audit | 1.3, 1.6, 5.2 |
| verification-and-release — A deterministic gate detects drift | contract, source-link, render, test, package, and forbidden-content negative checks | 1.5, 1.6, 5.3 |
| verification-and-release — GitHub CI evaluates the candidate | required ordinary CI jobs resolve to the published exact SHA | 5.3, 5.4 |
| verification-and-release — The stand is unavailable | `e2e_required=false`; named offline gates remain mandatory and no live fixture is added | 5.3 |
| verification-and-release — Evidence is published | Multica read-back checks exact SHA, links, commands, exits, and assertions only | 5.4 |

## Evidence and cleanup contract

- Git contains normal implementation, exact reviewed fixtures, tests, generated
  projection, docs, and CI changes only.
- Multica contains final exact SHA, PR/commit/file and CI links, commands, exit
  codes, assertions, and review findings with read-back.
- No live logs, stand diagnostics, screenshots, terminal text/PNG, environment
  dumps, private URLs, hostnames, credentials, or personal data are created.
- Routine cleanup may remove local build/test output. It SHALL preserve PR #101,
  its branch and commits, the consolidated implementation branch/PR, and all
  ordinary source/test commits. Merge, close, branch deletion, and duplicate
  cancellation require separate authorization.

## Estimate contract

The `estimate-openspec` assessment uses one experienced developer familiar with
the project stack, without AI acceleration, and measures active hours for the
remaining work from exact PR #101 head. Exact optimistic, weighted, and
pessimistic totals are authoritative only in the planning issue properties
`Estimate min, hours`, `Estimate, hours`, and `Estimate max, hours`.

Confidence is medium: the exact baseline and repository analogues are inspectable,
but PR #101 conflict reconciliation and source-wide contract classification can
move effort within the recorded property range. Tests were not run to estimate;
existing implementation, tests, workflows, history, and planning artifacts were
read as evidence. Unattended CI time, approval queues, and external waiting are
excluded.

The integration-target clarification fixes identities and assertions for work
already included in baseline reconciliation. It changes no remaining behavior,
task, work package, or effort assumption, so the authoritative estimate
properties remain unchanged.

The read-back `Estimate, hours` property is above the authoritative threshold,
so `delivery_mode=dag`. The graph below is the transitive reduction and has a
real parallel frontier.

## Work packages and stages

| WP | Stage | Direct `depends_on` | OpenSpec task coverage |
|---|---:|---|---|
| `WP-01-baseline-contract` | 1 | none | 1.1–1.6 |
| `WP-02-property-project` | 2 | `WP-01-baseline-contract` | 2.1–2.5 |
| `WP-03-wakeup-conflict` | 2 | `WP-01-baseline-contract` | 3.1–3.2 |
| `WP-04-runtime-workspace` | 2 | `WP-01-baseline-contract` | 4.1–4.5 |
| `WP-05-integration-release` | 3 | `WP-02-property-project`, `WP-03-wakeup-conflict`, `WP-04-runtime-workspace` | 5.1–5.4 |

### WP-01-baseline-contract

- **Deliverable:** an implementation line composed by merging the exact verified
  planning revision into exact PR #101 head, with fixed integration target
  `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`, published OpenSpec input and
  accepted `0.6.2` behavior preserved before the contract advances to `0.7.0`.
- **Owned responsibility scope:** branch/integration reconciliation;
  `contracts/sdk-contract.json`; contract schema/loader/validator/generator;
  `src/multica_py/_generated/approved_sdk.py`; source-link, provenance,
  inventory, response-closure, compatibility, mutation, ancestry, and retained
  baseline tests. Related fixtures and scripts are included.
- **Critical shared files:** the approved contract and generated projection are
  single-writer foundation files. Stage-2 packages consume their stabilized
  identifiers and SHALL NOT regenerate or edit them concurrently.
- **Contract surface:** exact two-parent composition; integration-target
  ancestry; byte-identical OpenSpec preservation; retained/adapted/excluded
  decisions; target provenance; transport mappings; normalized constraints;
  compatibility interval; deterministic output.
- **DoD/evidence:** both parent identities, integration ancestry and OpenSpec
  subtree equality pass before product edits; conflicts have no unexplained
  retained drift; 209 commands and 196 responses close; contract,
  source-link, mutation, double-render, freshness, and baseline regression checks pass.
- **Parallel safety:** foundation runs alone. It removes all shared contract and
  generated-file writes from later siblings.

### WP-02-property-project

- **Deliverable:** reviewed property comparison filters plus project workflow
  identity/write behavior, retaining PR #101 list-property and partial-update semantics.
- **Owned responsibility scope:** issue property-filter parser/adapter; project
  wire/public models, entities, resources, bindings and exports; workflow-aware
  issue/project adapters; domain unit/resource/component/bound tests, fixtures,
  and focused docs snippets. Shared contract/generated files are read-only.
- **Contract surface:** operator/type/value validation and ordering;
  `Project.workflow_id`; authoritative workflow remap, assignment, move, and
  run-handoff results; no workflow-management method.
- **DoD/evidence:** positive/negative cases prove exact argv/query, zero-I/O
  failures, UUID/null/omitted/legacy decode, success/conflict outcomes, no retry,
  and no unrelated mutation.
- **Parallel safety:** owns no wakeup, runtime, agent, workspace, shared error,
  contract, generated, or final shared-doc files.

### WP-03-wakeup-conflict

- **Deliverable:** PR-conflict wakeup creation/update through the existing
  exactly-one condition model with PR #101 diagnostics retained.
- **Owned responsibility scope:** wakeup condition types, create/update adapters,
  wakeup-specific case tables, payload fixtures, compatibility and parity tests.
  Shared contract/generated files are read-only.
- **Contract surface:** PR-conflict condition token, eager/command exact argv,
  exactly-one validation, typed results, legacy diagnostic compatibility.
- **DoD/evidence:** positive and conflicting-condition rows pass, invalid calls
  perform zero transport, and retained diagnostic/clearing tests remain green.
- **Parallel safety:** wakeup-only write zone is disjoint from WP-02 and WP-04.

### WP-04-runtime-workspace

- **Deliverable:** runtime sharing/privacy and agent grant semantics plus the
  target workspace allowlist conflict, using the existing sanitized exceptions.
- **Owned responsibility scope:** runtime and agent models/resources/decoders;
  workspace create/update error adapter; existing shared transport/exception
  primitives only where the approved payload requires a common decode change;
  domain unit/resource/component/bound/conflict/redaction tests and fixtures.
  Shared contract/generated files are read-only.
- **Contract surface:** `shared_with`; explicit grants; atomic revocation;
  busy blockers; structured safe conflict context; workspace allowlist failure;
  generic fallback and PR #101 error retention.
- **DoD/evidence:** ordered/omitted/malformed identity rows, allowed/denied/revoked
  agent paths, atomic/no-retry conflict cases, workspace allowlist fixtures, and
  private-data redaction assertions pass.
- **Parallel safety:** owns runtime/agent/workspace/error files as one package so
  siblings never contend for shared exception decoding.

### WP-05-integration-release

- **Deliverable:** one coherent candidate with shared tables, docs, package
  metadata, ordinary CI and exact-SHA Multica evidence aligned to the remaining delta.
- **Owned responsibility scope:** shared canonical vectors and coverage tables;
  README/API/compatibility/migration/service/changelog/contributing/releasing
  docs; package assertions; existing ordinary GitHub workflows; final generated
  reconciliation and evidence publication. Behavior fixes return to their owning
  predecessor before reconsolidation.
- **Contract surface:** public discovery/exports, retained and excluded policy,
  offline gate set, package contents, rollback, exact-SHA evidence.
- **DoD/evidence:** focused and complete non-live tests, contract/source/render,
  lint/types, compatibility and wheel/sdist checks pass on one clean SHA;
  required CI points to that SHA; Multica read-back contains links, commands,
  exits and assertions with no live/image/private evidence.
- **Parallel safety:** final join starts only after every stage-2 predecessor;
  it is the sole owner of cross-domain tables, shared docs, packaging, and CI reconciliation.

## Coverage and graph checks

- Every task 1.1 through 5.4 appears exactly once across five work packages.
- Stages are contiguous: stage 1 foundation, three independent stage 2 domain
  packages, and stage 3 integration. Every predecessor has a lower stage.
- The direct graph contains only foundation-to-domain and domain-to-integration
  edges; no direct edge is transitively redundant.
- Stage 2 has three disjoint write zones and is a genuine parallel frontier.
- Responsibility scopes include directly related tests, fixtures, snapshots,
  docs, generated files, and service files unless an active sibling explicitly
  owns the shared file; they are not exhaustive allowlists.

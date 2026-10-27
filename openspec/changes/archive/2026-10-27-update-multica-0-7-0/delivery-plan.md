## Delivery basis

- `change_id`: `update-multica-0-7-0`
- `task_key`: `MYL-557`
- `revision_base`: accepted integration
  `9b5d112830831f9e727b35f4936f923ec9429cc7`
- `immutable_composition`: `1f8083040d862669e65b875e7bc9555de96a7346`
- `composition_first_parent`: PR #101 head
  `b1c350ce22941a66871f11e0c5830a6ec542878c`
- `composition_planning_parent`:
  `4a83aa817cc2539bee60fe1f1a3996753428a28e`
- `accepted_wp01`: `b189631ad2cbc33e9ecfd5cd616052400e8f89aa`
- `accepted_wp03`: `c24d6ac48b0a0cedfca59a54ed6e6f0e2d5a8fd1`
- `accepted_wp02`: `ddeb824b16359dce86bc1ed6fbe3b327166dbf76`
- `target`: Multica `0.7.0` at
  `dbdbb299164347586e2650bb67684a490726a798`
- `scope_basis`: remaining work after accepted WP-01/02/03, including correction
  of their preserved contract snapshot where pinned CLI source disproves the
  runtime write/response mapping

The revision is published on a separate normal ref. Existing PR, planning,
feature, WP, and accepted refs remain unchanged. A future incorporation is a
normal forward operation owned by Manager after independent approval; force,
reset, amend, rebase, history replacement, and silent ACCEPT reuse are forbidden.

## Pinned CLI and source mapping

| Concern | Pinned source fact | Revised SDK decision |
|---|---|---|
| Runtime list | `server/cmd/multica/cmd_runtime.go::runRuntimeList` calls `GET /api/runtimes` and prints JSON | decode `RuntimeDefinition.visibility/shared_with` |
| Runtime rename | `runRuntimeRename` PATCHes custom name and prints the returned runtime JSON | decode the same runtime-definition fields |
| Runtime update | `runRuntimeUpdate` accepts only `--target-version`/`--wait`, POSTs `/update`, and returns update status/result | retain `RuntimeUpdateResult`; remove `shared_with` response claim |
| Runtime access writes | `UpdateAgentRuntime` and `RevokeRuntimeWorkspaceAccess` are HTTP handlers with no CLI command/flag | `not_sdk_surface`; no HTTP bypass |
| Runtime delete | `runRuntimeDelete` deletes; `--cascade` unbinds agents, cancels runs, and deletes | separate lifecycle behavior; never a revoke substitute |
| Agent runtime selection | `agent create/update --runtime-id` uses existing CLI operations | retain mapping; classify reviewed access denial only |
| Workspace allowlist | workspace create/update use existing CLI HTTP wrapper | classify reviewed safe failure; unknown shapes fall back |

The contract correction SHALL update response registry/source links, generated
projection, mutation checks, and docs together. A server handler alone never
authorizes a public SDK operation.

## Accepted-history and graph migration contract

Tasks 1.1–3.2 are complete at the accepted SHAs above. Their commits and evidence
remain valid historical inputs, but their old graph revision is not authority
for remaining work.

- Manager SHALL record `COMPOSITION_PLANNING_SHA` as the immutable composition's
  original second parent and the newly approved revision separately as
  `VERIFIED_PLANNING_SHA`.
- Final OpenSpec equality SHALL compare candidate `HEAD` with the new
  `VERIFIED_PLANNING_SHA`; composition parent assertions SHALL continue to
  compare against `4a83aa817cc2539bee60fe1f1a3996753428a28e`.
- The revised implementation input SHALL descend from current accepted
  integration `9b5d112830831f9e727b35f4936f923ec9429cc7` and contain all three
  accepted result SHAs.
- The blocked WP-04 attempt on MYL-576 has no result SHA or ACCEPT and SHALL NOT
  be reused. MYL-576 and unstarted MYL-577 cannot be converted to the revised
  topology because Multica `0.7.0` has no supported operation that clears their
  stored stages.
- Manager SHALL create exactly one new unstaged parked child for the sole
  remaining package, then retire and cancel MYL-576 and MYL-577 as duplicates
  of that replacement. Their terminal historical stage values do not belong to
  the revised topology and cannot hold fan-in open.

### Safe platform migration procedure

Manager SHALL execute this procedure only after the new revision is READY and
receives fresh human approval. It is a migration gate, not product execution:

1. Keep product execution paused. Run
   `multica issue runs MYL-576 --active --output json` and the equivalent for
   MYL-577; both arrays SHALL be empty. Run
   `multica issue children MYL-558 --output json` and inspect every direct child
   description for the exact new `graph_revision` plus
   `wp_id=WP-04-05-cli-surface-release`. More than one match blocks migration.
2. Write the complete replacement contract to workspace-local
   `./myl-558-remaining-wp.md`. It SHALL contain `issue_role=wp_child`, exact
   implementation/planning parent ids, new graph and verified-planning SHA,
   exact incorporated `input_sha`, `wp_id=WP-04-05-cli-surface-release`, task
   coverage 4.1–5.4 exactly once, `delivery_mode=single_wp_no_dag`, scope,
   contract surface, DoD and evidence. It SHALL contain no `stage=`,
   `depends_on=`, frontier, DAG, old ACCEPT, or execution authority.
3. If preflight found zero matches, create one parked replacement with
   `multica issue create --title "WP-04-05-cli-surface-release: Multica 0.7.0" --parent 01a1714f-ae1e-72b7-8de8-664565c7f72a --assignee-id b1d7c209-0c04-449e-9c8b-f38373a8e068 --status backlog --priority high --project 89afff1c-d2f9-43d1-a50d-c6930f3491e3 --description-file ./myl-558-remaining-wp.md --output json`.
   The omitted `--stage` is the supported create path to `stage=null`; `backlog`
   prevents assignment from starting a run. Capture the returned id as
   `NEW_WP_ID`. If local capture fails after successful creation, recover the
   unique graph-revision/wp-id match from `issue children`; never retry create.
   If preflight found one match, set `NEW_WP_ID` to that existing id and skip
   creation.
4. Read `multica issue get "$NEW_WP_ID" --output json` and active runs. Assert
   exact `parent_issue_id=01a1714f-ae1e-72b7-8de8-664565c7f72a`, `stage=null`,
   `status=backlog`, WP Delivery assignment, exact project, graph/input/wp/task
   contract, no forbidden topology fields, and zero active runs. Any mismatch
   blocks migration; keep and repair this same parked id rather than creating
   another.
5. Write retired-child records for MYL-576 and MYL-577 from workspace-local
   files, naming `NEW_WP_ID`, the new graph revision, their old stage and
   non-acceptance. Apply each description with `issue update --description-file
   ... --no-start`, read it back, then run
   `multica issue status <old-id> cancelled --duplicate-of "$NEW_WP_ID"`.
   Read-back SHALL show both old issues under the unchanged implementation
   parent with `status_category=cancelled`, `duplicate_of.id=NEW_WP_ID`, and no
   active run. The replacement already exists nonterminal, so partial retirement
   cannot close parent fan-in prematurely.
6. Run `multica issue children MYL-558 --output json` and read every direct child.
   MYL-573/574/575 SHALL be successful terminal history; MYL-576/MYL-577 SHALL be
   cancelled duplicates of `NEW_WP_ID`; and `NEW_WP_ID` SHALL be the only
   nonterminal child and appear in `unstaged` with `stage=null`. There SHALL be
   exactly one revised wp-id/graph match and no dependency/DAG contract. When
   this replacement becomes terminal, every direct child is terminal and the
   parent's children-done fan-in closes.

Every write is followed by read-back. On a failed assertion Manager SHALL stop,
keep the replacement parked, SHALL NOT launch implementation, and SHALL NOT
create another replacement. Old children are cancelled only after replacement
verification. Temporary description files are removed only after successful
read-back and are never committed.

## E2E decision

`e2e_required=false`.

The revision removes unsupported runtime writes instead of trying to exercise
them. Remaining results are deterministic contract classification, JSON decoding,
CLI error mapping, redaction, documentation, packaging, and ancestry. Source-link
checks, fake-CLI/unit/resource/component tables, mutation tests, package imports,
and ordinary CI prove them completely. No case requires a database, browser,
external service, persistent identity, interactive TTY, changed visible output,
or image.

No local E2E script, stand provisioning, live fixture, identity, before/after
text, PNG, terminal renderer, image attachment, or live cleanup is planned.
If implementation introduces a direct HTTP path, new CLI output, or another
irreducibly live behavior, it violates this revision and returns to planning.

## Scenario and verification mapping

| Case | Requirement / scenario | Verification decision | Exact assertions and ownership |
|---|---|---|---|
| R01 | public parity / target inventory | lower-level sufficient | contract closure keeps 209 CLI nodes classified; task 4.1/5.2 |
| R02 | public parity / upstream-only behavior | lower-level sufficient | forbidden-symbol and `not_sdk_surface` mutation rows; task 4.1/4.5 |
| R03 | public parity / response belongs elsewhere | lower-level sufficient | `runtimes.update` response type rejects runtime-definition fields; task 4.1 |
| R04 | public parity / accepted operation drift | accepted regression | WP-01/02/03 discovery, vectors, bindings, fixtures; task 5.2/5.3 |
| R05 | public parity / remaining adaptation | lower-level sufficient | every corrected row carries source, task, tests, docs; task 4.1/5.2 |
| R06 | public parity / accepted mapping correction | lower-level sufficient | preserved accepted SHA plus corrective mutation case; task 4.1/5.3 |
| R07 | property / ordered comparisons | accepted regression | accepted WP-02 exact argv/order rows; task 5.3 |
| R08 | property / invalid comparison | accepted regression | accepted WP-02 zero-I/O negative rows; task 5.3 |
| R09 | project / workflow omitted or null | accepted regression | accepted WP-02 wire/public fixtures; task 5.3 |
| R10 | project / write succeeds | accepted regression | accepted WP-02 resource/component rows; task 5.3 |
| R11 | project / write rejected | accepted regression | accepted WP-02 conflict/no-retry rows; task 5.3 |
| R12 | wakeup / PR conflict | accepted regression | accepted WP-03 eager/command exact argv rows; task 5.3 |
| R13 | wakeup / condition conflict | accepted regression | accepted WP-03 exactly-one zero-I/O rows; task 5.3 |
| R14 | runtime / sharing identities | lower-level sufficient | list/rename JSON decode, order, omission, malformed cases; task 4.2 |
| R15 | runtime / target update result | lower-level sufficient | target-version argv and `RuntimeUpdateResult`; negative field ownership; task 4.1/4.2 |
| R16 | agent / runtime access denied | lower-level sufficient | create/update exact argv plus safe authorization error/no retry; task 4.3 |
| R17 | runtime / access management sought | reasoned exclusion | discovery contains no access write; contract records server route as `not_sdk_surface`; task 4.1/4.5 |
| R18 | runtime / delete inspected | reasoned exclusion | delete/cascade lifecycle source and no-revocation assertion; task 4.5 |
| R19 | workspace / allowlist failure | lower-level sufficient | reviewed CLI stderr status/code/message, typed exception, redaction; task 4.4/4.5 |
| R20 | workspace / unknown failure | lower-level sufficient | malformed/unknown body preserves generic failure; task 4.4 |
| R21 | contract / historical composition changes | Git assertion | exact immutable commit and parents; task 5.3 |
| R22 | contract / revised planning incorporated | Git assertion | accepted integration/new revision/candidate ancestry and final subtree equality; task 5.3 |
| R23 | contract / accepted behavior migration drift | accepted regression | exact accepted SHAs and focused tables; task 5.3 |
| R24 | contract / provenance mixed | contract mutation | release/tag/commit/assets/source links; task 5.2 |
| R25 | contract / missing target decision | contract mutation | 209/196 closure and duplicate/missing rejection; task 5.2 |
| R26 | contract / accepted work reimplemented | accepted regression | retained references and diff review; task 5.2/5.3 |
| R27 | contract / server-only runtime write | contract mutation | non-surface row and forbidden public binding; task 4.1/4.5 |
| R28 | contract / candidate untraced | contract mutation | destination/response/source validation; task 4.1 |
| R29 | contract / wrong operation response | contract mutation | runtime update/list/rename ownership cases; task 4.1 |
| R30 | contract / generated drift | deterministic check | double render and generated freshness; task 5.2/5.3 |
| R31 | compatibility / reviewed endpoint | lower-level sufficient | `0.6.2`/`0.7.0` preflight rows; task 5.3 |
| R32 | compatibility / above ceiling | lower-level sufficient | strict/warn boundary rows; task 5.3 |
| R33 | verification / accepted history and topology migration | Git + child/managed-contract read-back | identities, ancestry, no old ACCEPT reuse; one unstaged replacement; MYL-576/MYL-577 cancelled duplicates; reachable fan-in; task 5.3/5.4 |
| R34 | verification / old result reused | managed-contract assertion | revised result must use new graph/input; task 5.4 |
| R35 | verification / coverage closure | contract/test audit | 196 responses and all revised scenarios close once; task 5.2 |
| R36 | verification / deterministic drift | ordinary CI | source, contract, render, tests, types, lint, package; task 5.3 |
| R37 | verification / exact-SHA CI | ordinary CI | required jobs point to candidate SHA; task 5.3/5.4 |
| R38 | verification / stand unavailable | reasoned exclusion | `e2e_required=false`, no live node/fixture; task 5.3 |
| R39 | verification / evidence published | Multica read-back | links, commands, exits, assertions, limitations, cleanup; task 5.4 |

All cases use existing repository tests and fixtures. Implementer owns any
necessary contract, generated, test, fixture, documentation, package, or CI
edits. Independent verification reads and executes the agreed checks but does
not edit implementation fixtures or manufacture evidence.

## Verification commands and CI ownership

| Gate | Concrete command / assertion | CI disposition |
|---|---|---|
| Historical composition | `test "$(git rev-parse 1f8083040d862669e65b875e7bc9555de96a7346^1)" = b1c350ce22941a66871f11e0c5830a6ec542878c` and equivalent second-parent check | final CI |
| Accepted ancestry | `git merge-base --is-ancestor` for composition, WP-01, WP-03, WP-02, and accepted integration against candidate `HEAD` | before resumed edits and final CI |
| Revised planning ancestry | new `VERIFIED_PLANNING_SHA` descends from `9b5d112830831f9e727b35f4936f923ec9429cc7` and is an ancestor of candidate `HEAD` | before resumed edits and final CI |
| Final OpenSpec | `git diff --exit-code "$VERIFIED_PLANNING_SHA" -- openspec/changes/update-multica-0-7-0/` | before resumed edits and final CI |
| Topology migration | `multica issue get "$NEW_WP_ID"`, old-child reads, active-run reads, and `multica issue children MYL-558 --output json` | before replacement promotion: exactly one graph/wp match, exact parent, sole nonterminal child unstaged, both old children cancelled duplicates, accepted history terminal, fan-in reachable |
| Contract/source | `make contract` | existing `contract-check` job |
| Generated freshness | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` | existing contract job |
| Focused correction | `uv run pytest -o addopts="" -q tests/unit/resources tests/unit/test_transport.py tests/component/test_transport_errors.py tests/contract/test_sdk_contract.py` | existing unit/component/contract jobs |
| Accepted WP regression | focused property/project/wakeup and contract tests named by accepted evidence | same candidate CI revision |
| Lint/types | `make lint && make types` | existing CI jobs |
| Complete offline | `make test && make compat` | existing CI; local run obeys the workspace test-time limit |
| Package | `make package` | existing package workflow |
| OpenSpec | `openspec validate update-multica-0-7-0 --strict && openspec validate --specs --strict` | planning and implementation preflight |

## Estimate contract

The mandatory `estimate-openspec` assessment measures remaining active hours for
one experienced developer familiar with the project stack, without AI
acceleration, from accepted integration SHA to revised acceptance. Exact
optimistic, weighted, and pessimistic totals are authoritative only in planning
issue properties `Estimate min, hours`, `Estimate, hours`, and
`Estimate max, hours`.

Confidence is medium: the CLI/source boundary and current implementation are
inspectable, but corrective contract propagation, accepted-regression repair,
and final integration can still move effort within the property range. Tests
were not run to estimate; source, artifacts, tests, workflows, and accepted
history were read as evidence. Unattended CI, approval queues, and external
waiting are excluded.

## Delivery mode and work package

`delivery_mode=single_wp_no_dag`.

Tasks 1.1–3.2 are accepted historical work and are not assigned again. Every
remaining task 4.1–5.4 is covered exactly once by the single package below. No
`depends_on`, stage, frontier, parallel sibling, or DAG metadata exists. This is
required because contract correction must precede runtime/error implementation,
which must precede final reconciliation; no remaining execution front contains
two independent packages. Platform read-back SHALL distinguish this remaining
topology from terminal history: exactly one new or recovered replacement is the
only nonterminal child and is unstaged; MYL-576 and MYL-577 are cancelled
duplicates and are not executable packages.

### WP-04-05-cli-surface-release

- **Task coverage:** 4.1–4.5 and 5.1–5.4, exactly once.
- **Deliverable:** one accepted candidate that corrects the runtime contract,
  implements only CLI-backed runtime reads and agent/workspace failures,
  documents exclusions, and completes package/CI/evidence reconciliation while
  preserving immutable composition and accepted WP history.
- **Owned responsibility scope:** `contracts/sdk-contract.json`; contract
  schema/loader/validator/generator and generated projection; runtime models,
  entities, resources, bindings, exports; agent/workspace transport-error paths;
  domain and cross-domain unit/resource/component/contract tables and fixtures;
  shared canonical vectors, docs, package assertions, existing ordinary CI, and
  Multica evidence. Directly coupled support files follow this package.
- **Critical shared files:** there are no active sibling writers. Contract,
  generated projection, shared error parsing, docs, packaging, and CI are owned
  end-to-end by this package.
- **Contract surface:** runtime list/rename read fields; target-version update
  response; server-only write exclusions; delete-not-revoke boundary; safe
  authorization/allowlist failures; accepted-history and final OpenSpec gates.
- **DoD/evidence:** all R01–R39 mappings are closed; contract/source/mutation,
  focused and complete offline, lint/type, compatibility, package, ancestry, CI,
  topology/fan-in and evidence read-back checks pass at one clean exact SHA; no
  old ACCEPT, direct HTTP method, live/image/private evidence, or duplicate
  executable child exists.
- **Parallel safety:** single remaining writer; no parallel topology applies.

## Evidence and cleanup contract

- Git contains normal product/test/fixture/generated/docs/CI commits only.
  Tests and functional outputs are separated by commits only when the verified
  functionality itself produces a distinct artifact requiring that separation.
- Multica contains exact planning/candidate/accepted SHAs, PR/commit/file/CI
  links, commands, exits, assertions, limitations, cleanup, and read-back.
- Images, terminal text, real logs, diagnostic JSON, environment dumps, private
  URLs/hosts, credentials, and personal data are neither created nor committed.
- Routine cleanup may remove local build/test output. It preserves PR #101, all
  existing refs/commits, the revision ref, implementation branch/PR, accepted
  evidence, and ordinary source/test commits. Merge, close, branch deletion,
  child deletion, and destructive composition rollback require separate authority.

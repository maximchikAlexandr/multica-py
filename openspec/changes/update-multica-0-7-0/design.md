## Context

The verified planning input is `4a83aa817cc2539bee60fe1f1a3996753428a28e`.
WP-01 composed it with exact PR #101 head in immutable merge
`1f8083040d862669e65b875e7bc9555de96a7346`, then published accepted foundation
`b189631ad2cbc33e9ecfd5cd616052400e8f89aa`. WP-03 and WP-02 were accepted at
`c24d6ac48b0a0cedfca59a54ed6e6f0e2d5a8fd1` and
`ddeb824b16359dce86bc1ed6fbe3b327166dbf76`; current integration is
`9b5d112830831f9e727b35f4936f923ec9429cc7`.

WP-04 stopped before changes because pinned Multica source
`dbdbb299164347586e2650bb67684a490726a798` proves two different surfaces:

- `runtime update <id>` accepts only `--target-version`, `--wait`, and output;
- runtime visibility/share PATCH and atomic revoke are server HTTP routes with no
  CLI command or flag;
- runtime delete/cascade unbinds agents, cancels runs, and deletes the runtime;
  it is destructive lifecycle management, not privacy revocation;
- runtime list and rename JSON return runtime-definition fields including
  `visibility` and `shared_with`;
- agent create/update select an existing runtime through `--runtime-id`, so
  authorization rejection is observable through the existing CLI error path;
- workspace create/update likewise expose their allowlist failure through the
  existing CLI error path.

The accepted contract incorrectly attached `shared_with` to `runtimes.update`
and described unavailable runtime write behavior. This revision corrects future
work without rewriting the accepted foundation or any existing ref.

## Goals / Non-Goals

**Goals:**

- make the remaining SDK behavior exactly match pinned CLI operations and JSON;
- retain accepted WP-01/02/03 commits and prove their behavior under the revised
  final candidate;
- preserve immutable composition history while moving final OpenSpec equality
  to the new Plan-Verifier-approved planning revision;
- complete contract repair, CLI-backed runtime reads/errors, documentation,
  packaging, and release verification in one remaining package;
- keep all verification deterministic and offline.

**Non-Goals:**

- direct HTTP access, a second transport, or new runtime access-management SDK
  methods;
- treating runtime delete/cascade as share removal or privacy revocation;
- modifying, rebasing, force-pushing, resetting, deleting, or recreating PR #101,
  the original planning ref, the implementation feature ref, WP refs, accepted
  commits, composition parents, or existing child issues;
- rerunning accepted WP-01/02/03 implementation or accepting old markers under
  the new graph revision;
- live stand, identity provisioning, browser, TTY, screenshots, or images.

## Decisions

### Decision 1: Enforce the CLI boundary

The SDK SHALL expose only behavior reachable through the pinned CLI. Runtime
visibility/share/revoke HTTP operations SHALL be recorded as
`not_sdk_surface`. No implementer choice remains: adding an HTTP bypass would
violate the repository's approved-contract and CLI transport architecture.

Alternative: add an SDK HTTP client. Rejected because it is a new transport,
authentication model, error contract, and public surface outside this change.

### Decision 2: Separate runtime reads, updates, and deletion

`RuntimeDefinition.visibility` and `RuntimeDefinition.shared_with` SHALL decode
only from CLI operations returning runtime definitions, currently list and
rename. `runtimes.update` SHALL retain its target-version request and
`RuntimeUpdateResult` response. Runtime delete SHALL retain its independently
approved lifecycle contract; cascade SHALL not satisfy any privacy scenario.

Alternative: attach all runtime fields and actions to the existing
`RuntimeResource.update` name. Rejected because matching resource names do not
prove transport or response mapping.

### Decision 3: Keep observable authorization and allowlist failures

Agent create/update SHALL continue to select runtimes through existing
`--runtime-id` mappings. Reviewed denial diagnostics SHALL map through the
existing exception hierarchy without retry or private structured context.
Workspace create/update allowlist failures SHALL follow the same fail-closed
pattern. Unknown shapes retain the generic command failure.

Alternative: add grant management so tests can construct the server state.
Rejected because grant writes have no CLI surface; deterministic payload cases
are sufficient to verify SDK decoding/classification.

### Decision 4: Preserve composition and migrate the preservation gate

Immutable `COMPOSITION_SHA=1f8083040d862669e65b875e7bc9555de96a7346`
and its exact parents SHALL remain unchanged. The new planning revision SHALL be
a descendant of accepted integration SHA
`9b5d112830831f9e727b35f4936f923ec9429cc7` on a separate normal ref. After
independent approval, Manager may incorporate that revision without rewriting
history and SHALL record both identities:

- `COMPOSITION_PLANNING_SHA=4a83aa817cc2539bee60fe1f1a3996753428a28e`
  remains the composition's immutable second parent;
- `VERIFIED_PLANNING_SHA=<new revision>` becomes the final OpenSpec source of
  truth.

Final CI SHALL prove the composition's historical parents, composition ancestry,
new revision ancestry from current accepted integration, accepted result SHAs,
and byte-identical OpenSpec against the new `VERIFIED_PLANNING_SHA`.

Alternative: amend composition or overwrite the feature branch. Rejected
because it would invalidate accepted evidence and the preservation contract.

### Decision 5: Migrate the remaining topology without duplicate children

Accepted tasks 1.1–3.2 are recorded complete and are not reassigned. Tasks
4.1–5.4 form one remaining deliverable because contract correction precedes
runtime/error implementation and final integration; no independent parallel
frontier remains. The revised delivery mode is `single_wp_no_dag` with one WP,
no `depends_on`, stage, frontier, or DAG metadata.

After approval, Manager SHALL reuse existing MYL-576 for the sole revised
package, bind it to the new graph revision and incorporated input SHA, and
invalidate its old blocked attempt as non-accepted. MYL-577 SHALL not launch or
count as a revised package. Operational status handling is Manager-owned; no
duplicate child is created.

Alternative: preserve two sequential WPs. Rejected because the planning policy
requires one WP when no frontier can execute two independent packages.

### Decision 6: Offline verification remains sufficient

`e2e_required=false`. Source links and contract closure prove exclusions and
mappings; fake-CLI/unit/resource/component tables prove decoding and failures;
package and ordinary CI checks prove integration. No revised scenario depends
on a real service, persistent state, visible output, or interactive client.

Alternative: use the unavailable stand to manufacture grant/revocation state.
Rejected because those writes are excluded and a stand cannot create an SDK
surface missing from the CLI.

### Decision 7: Ponytail full gate

No new subsystem is needed. Existing contract/schema/generator,
`RuntimeDefinition`, runtime/agent/workspace resources, CLI transport,
sanitized exceptions, frozen case tables, docs, packaging, and CI are necessary
and retained. A direct HTTP client, access-management abstraction, grant model,
second registry, E2E runner, identity provisioner, renderer, and evidence store
are unnecessary and removed from the plan.

## Risks / Trade-offs

- **Accepted WP-01 contract contains the bad mapping** → correct it in the sole
  remaining package, preserve the accepted SHA, and add mutation/negative-closure
  cases so the historical error cannot return.
- **Old and new planning SHAs can be confused** → record separate composition
  and final verified-planning identities and assert both roles explicitly.
- **A server-only capability remains unavailable to SDK callers** → document the
  honest exclusion; a future CLI command plus separately approved SDK change is
  required before exposure.
- **Existing children reflect the old DAG** → reuse MYL-576 only, do not launch
  MYL-577, and require managed-contract read-back before resumed implementation.
- **Error bodies may drift** → admit only reviewed status/code/message fields;
  unknown or malformed payloads fall back without exposing backend detail.

## Migration Plan

1. Publish this OpenSpec-only commit on a new normal ref descended from exact
   accepted integration `9b5d112830831f9e727b35f4936f923ec9429cc7`.
2. Plan Verifier independently checks source mappings, artifacts, estimate
   properties, visual, remote SHA, and human approval for the new revision.
3. Manager incorporates the approved revision without force, reset, amend, or
   rewriting any existing ref; records historical and new planning identities;
   and read-backs the updated implementation contract.
4. Manager reuses MYL-576 as the sole remaining all-covering WP. Old blocked
   evidence is retained but is not an ACCEPT; MYL-577 does not launch.
5. The remaining WP corrects the contract/generated projection first, then
   implements read-only runtime fields and CLI-backed errors, reconciles docs
   and package surfaces, and publishes one final candidate.
6. Final checks prove immutable composition parents/ancestry, accepted WP SHAs,
   new OpenSpec equality, complete offline gates, ordinary CI, and Multica
   evidence read-back.
7. Product commits roll back normally. Composition rollback remains
   `git revert -m 1 1f8083040d862669e65b875e7bc9555de96a7346` only with separate
   authority; planning and accepted refs remain preserved.

## Open Questions

None. A future decision to expose runtime access-management writes requires an
upstream CLI surface and a separate approved change.

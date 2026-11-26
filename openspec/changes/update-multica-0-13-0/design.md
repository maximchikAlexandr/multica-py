## Context

The planning base is SDK commit `b268e3bec0436fe51727fda50583344f57663284`, whose approved contract target and maximum tested CLI are `0.7.1`. The verified target is stable Multica `0.13.0`, release `457951728`, commit `35b54a3742bb51bdf5ffa688655367ec98044862`. The audited range is exactly `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0..35b54a3742bb51bdf5ffa688655367ec98044862`: binary help grows from `209` to `277` nodes, one node is removed, `36` nodes change, and all `196` supported response work items have a reviewed disposition.

The SDK already has the required seams: one approved JSON contract, deterministic generation, direct resource methods plus command previews, frozen/open msgspec models, private presence-aware wires, shared typed-error decoding, and frozen table-driven test cases. The upgrade therefore changes data and existing adapters rather than adding an architecture.

## Goals / Non-Goals

**Goals:**

- Deliver one direct `0.7.1` to `0.13.0` contract migration with exact release/source/binary provenance.
- Preserve backward decoding for omitted fields from older supported servers while exposing approved `0.13.0` semantics.
- Make blocker privacy, lifecycle validation, task document attribution, and squad handoff behavior explicit and testable.
- Keep generated artifacts deterministic and verification independently reproducible from an exact revision.

**Non-Goals:**

- Publishing every new upstream command, especially `squad briefs`, inbox, views, workflows, quick actions, docs, environments, issue status administration, batch updates, or chat wakeups.
- Delivering intermediate versions separately or depending on the unpublished `0.12.1` planning branch.
- Generating public behavior from collector output, source heuristics, or live evidence.
- Changing upstream Multica, adding a second generator/test framework, or implementing during this planning change.

## Decisions

### 1. Preserve one approved-contract lineage

`contracts/sdk-contract.json` remains the only production generator input. The implementation SHALL append exact `0.13.0` release, archive, executable, version-output, command, and response provenance; set maximum tested to `0.13.0`; and use `0.13.1` as the exclusive compatibility ceiling. Existing validated history and the current minimum SHALL remain intact.

Alternative: rebuild a new contract from the target inventory. Rejected because it would discard reviewed lineage and let extraction evidence redefine public policy.

### 2. Add blockers to the existing issue model/resource seam

Issue decoding SHALL expose ordered `blocked_by` and `blocking` references plus privacy-safe `blocked_count`. Missing arrays SHALL decode as empty; explicit malformed values SHALL fail. Hidden blockers SHALL affect `blocked_count` without synthesizing identities. Manual and stage-derived references SHALL retain an open kind value with known `manual` and `stage` spellings.

Blocker mutations SHALL use the existing eager/command pair pattern, typed issue references, bound entities, shared transport, and shared errors. Local validation SHALL reject self-reference and an over-100 request before spawning; authoritative cycle, cross-workspace, and visibility validation SHALL remain server errors with typed propagation. Successful mutations SHALL invalidate only affected bound relation state.

Alternative: introduce a graph subsystem or eagerly hydrate every reference. Rejected because existing bound relations and immutable replacement cover the requirement without N+1 calls or cache duplication.

### 3. Replace legacy rerun without a compatibility alias

The obsolete `issue rerun` method/operation SHALL be removed from approved public inventories, resources, exports, cases, and docs. `issue rerun-task` SHALL be the sole supported successor with exact target argv, presence, result, and typed-error behavior.

Alternative: keep a deprecated alias. Rejected because upstream removed the command and the approved migration explicitly requires one replacement path.

### 4. Keep new values open and new command families deferred

Squad `handoff_mode` SHALL be represented by the existing open-string model policy: known values are `manual` and `stage`, omission from older payloads remains compatible, and unknown future strings decode unchanged. Task-run document attribution/kind SHALL be added to the existing agent-task/run wire and public model without creating a public document resource. `squad briefs` and all other unapproved command families remain contract dispositions only.

Alternative: add closed enums and public resources for each discovered command. Rejected because source discovery is not public API approval and closed values would turn forward expansion into decode failures.

### 5. Retain action-result boundaries and privacy

Delete operations SHALL keep their existing `ActionResult[None]` boundary even when the server performs additional cleanup. Response models SHALL never infer hidden blocker identities from counts, errors, logs, or adjacent relationships. Standard error redaction and malformed-success handling remain shared.

Alternative: expose server cleanup details as a new result model. Rejected because no stable successful response contract supports it.

### 6. Ponytail full gate before design

Every substantial addition maps to a distinct requirement or risk and an existing seam:

- Blocker projections/mutations are required by privacy and lifecycle acceptance; seam: `src/multica_py/entities/issues.py`, `resources/issues.py`, and private wire decoders. Existing issue relations lack blocker kind/count semantics.
- Handoff mode is required by squad assignment behavior; seam: `entities/squads.py` and `resources/squads.py`. The current squad model has no field or update flag.
- Task document attribution is required by run provenance/access; seam: `models/agents.py`, `_internal/agent_wires.py`, and issue task/run resources. Current wires cannot retain the new fields.
- Rerun replacement is required by an upstream removal; seam: existing issue operation tables and resource method. Retention would execute a nonexistent command.
- Contract/generator/test/doc work is required to keep the approved contract authoritative and releaseable; existing seams are sufficient and no parallel framework is justified.

Duplicate per-version adapters, a blocker graph cache, closed provider enums, an SDK docs subsystem, and generic inventory-generated methods are intentionally omitted.

### 7. Verification combines lower-level coverage with focused live evidence

Most mappings, omission/nullability/open-value behavior, deterministic rendering, and typed errors SHALL be proved by existing unit, contract, component, and CI gates. Focused local E2E is required only for behavior that cheaper checks cannot establish across a real CLI/backend: hidden blocker counts without identity leakage, manual/stage lifecycle and mutation failures, handoff mode round-trip, task document attribution/access, and rerun replacement.

The Tester SHALL use the isolated project stand and `multica-test`, a dedicated checkout/profile/data namespace, and the repository's focused script. Evidence SHALL be attached to Multica, not committed: command logs, assertions, diagnostic JSON, revisions, hashes, and genuine before/after terminal PNGs for changed read output. Test scripts and safe fixtures belong in Git; secrets, hostnames, raw logs, and images do not.

## Risks / Trade-offs

- **Large accumulated delta** → Require closed `277 + 1` command disposition and `196/196` response registry before generation.
- **Privacy regression from blocker projections** → Keep identities and counts separate; test hidden rows and sanitized errors at lower and live boundaries.
- **Older server omissions** → Use presence-aware private wires and explicit absent/null/empty cases instead of making new fields required.
- **Unknown values introduced after `0.13.0`** → Decode handoff/reference/document kinds as open strings and test unknown values.
- **Live evidence flakiness or leakage** → Gate readiness, isolate resources/profile, sanitize artifacts, preserve failed evidence, and clean only test-owned data.
- **Parallel implementation conflicts** → Put contract/generator foundation first; partition issue, squad/task, retained-mapping, verification, and documentation write zones.

## Migration Plan

1. Update and validate the approved contract and deterministic projection from exact pinned evidence.
2. Implement issue blocker/rerun, squad/task-run, and retained mapping changes on the common contract foundation.
3. Extend lower-level tables, live script, documentation, migration notes, and package/release checks.
4. Run focused checks and the complete offline gate locally within the automatic-test limit; run longer suites in GitHub Actions on the published exact revision.
5. Independently verify the exact revision on the isolated stand, attach evidence, and stop before merge/release unless separately authorized.

Rollback is a normal revert before release. No database migration or server mutation is introduced by the SDK package itself.

## Open Questions

None. Public support, compatibility, enum openness, deferred candidates, and evidence boundaries are resolved by this change.

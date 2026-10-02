## Delivery contract

- `delivery_mode`: `single_wp_no_dag`
- `planning_issue`: `MYL-374`
- `change_id`: `update-multica-0-6-1`
- `graph_revision`: `1`
- `approved_base`: `48745d2fe9e80ee9c027293ef22971ff5723f5f5`
- `estimate_authority`: custom properties `Estimate, hours`,
  `Estimate min, hours` and `Estimate max, hours` on the planning issue; numeric
  totals are intentionally not duplicated in this artifact.
- `estimate_basis`: remaining active developer effort for one experienced
  developer familiar with this Python SDK, without AI acceleration. Confidence is
  medium and calibration is uncalibrated: the exact source snapshot, previous
  direct-upgrade package, existing issue mutation seams and table-driven fixtures
  are inspectable, while the large approved-contract registry, complete source-link
  reconciliation and full-gate repair loops have no comparable measured execution
  history. Tests were not run to manufacture estimating evidence.

The authoritative estimate selects one execution unit. This package therefore
contains exactly one work package covering every OpenSpec task. Operational WIP,
assignee and live status are intentionally absent from this planning artifact.

## WP-01 — Complete Multica 0.6.1 SDK upgrade

- `id`: `WP-01`
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`, `2.1`, `2.2`,
  `2.3`, `2.4`, `3.1`, `3.2`, `3.3`, `3.4`, `3.5`, `3.6`, `4.1`, `4.2`,
  `4.3`
- `deliverable`: One coherent direct `0.6.0 → 0.6.1` SDK upgrade in which the
  approved contract, generated projection, existing issue mutations, compatible
  response semantics, table-driven evidence, documentation and package claims all
  agree and can be rolled back together.
- `owned responsibility scope`: exact provenance and inventories in
  `contracts/sdk-contract.json`; any strictly required schema/validator/generator
  support under `contracts/schema/` and `tools/upstream_contract/`; the single
  generated runtime projection; existing direct/bound issue resource/entity
  methods; directly related operation/response/compatibility tests, fixtures and
  helpers; README, changelog and API/coverage/compatibility/migration/contributing/
  service-usage/releasing documentation; final verification and package evidence.
  Related tests, fixtures, snapshots, docs and service files are included when
  needed to satisfy the task even if not named individually.
- `critical shared files`: `contracts/sdk-contract.json`,
  `src/multica_py/_generated/approved_sdk.py`,
  `src/multica_py/resources/issues.py`, `src/multica_py/entities/issues.py`,
  `tests/cases/operations.py`, `tests/unit/resources/test_operations.py`, shared
  response/provenance fixtures and public documentation are owned by this WP for
  the complete change.
- `contract_surface`: exact baseline/target identities and direct compatibility;
  205 command-node dispositions; four direct/bound issue mutation entrypoints with
  optional `duplicate_of`; existing `Issue.duplicate_of`; 196 response-entrypoint
  verdicts; open quota reasons; server-owned usage precision; repository checkout
  path/error behavior; deterministic generation, documentation and package claims.
- `definition_of_done/evidence`: all OpenSpec checkboxes are complete exactly once;
  strict OpenSpec succeeds; approved-contract collect/source-aware validate/double
  render/check and pinned source-link audit succeed; focused and full offline tests,
  Ruff, mypy, build, sdist/wheel, isolated import/package and forbidden-content
  audits succeed with exact commands/exits recorded; rerender and Git tree are
  clean; live status is explicit; no evidence, binary, source checkout, transient
  render or visual HTML is tracked or packaged.
- `parallel_safety`: a single executor owns every shared contract, fixture,
  resource and documentation seam, eliminating conflicting writers and integration
  handoffs for this bounded upgrade.

## Coverage proof

`WP-01` covers all tasks `1.1–1.5`, `2.1–2.4`, `3.1–3.6` and `4.1–4.3`
exactly once. No task is omitted or assigned to another work package.

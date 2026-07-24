# Contract: Generation, State, Promotion, and Provenance

## Generator Interface

Writing:

```bash
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json
```

Checking:

```bash
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json \
  --check
```

The approved contract is the only decision input. Check mode writes nothing,
reports every missing, extra governed, or byte-different output, and returns
non-zero on any difference.

## Governed Outputs and Fixed Write Order

1. `src/multica_py/_generated/approved_sdk_contract.json`
2. `src/multica_py/_generated/approved_sdk_bindings.py`
3. `src/multica_py/_generated/approved_sdk_enums.py`
4. `src/multica_py/_generated/approved_sdk_validators.py`
5. `src/multica_py/_generated/approved_sdk_api.pyi`
6. `src/multica_py/_generated/approved_sdk_compatibility.json`
7. `docs/generated/approved-sdk-v0.4.9.md`
8. `tests/cases/generated/approved_sdk_cases.py`
9. `tests/fixtures/provenance/approved-sdk-v0.4.9.json`

`contracts/generated-output-formats.json` is the byte-format authority. Python
outputs export only the listed symbols in listed order. JSON is UTF-8,
two-space indented, key-sorted, and has one trailing LF. Markdown uses its
listed headings, LF, and one trailing LF. No output contains timestamps.
Golden files use the destination path below
`tests/fixtures/upstream_contract/v2/` plus suffix `.golden`. T009 creates all
nine goldens before renderer implementation; `generate --check` compares
bytes, not parsed values.

Render all bytes in memory first. A write run creates same-directory temporary
files, fsyncs/closes them, then replaces destinations in this order. On render
or validation failure, no destination changes.

## Integration Boundary

- `multica_py.enums` re-exports generated approved enums.
- Governed handwritten resources import generated bindings and validators.
- Complex command sequences and response decoding remain handwritten.
- The generated stub and contract tests validate public signatures.
- Generated cases feed existing table-driven runners.
- Entire resource modules are not generated because they contain unrelated
  operations outside the 16-ID boundary.

## Canonical Active Paths

- state: `src/multica_py/_generated/upstream_state.json`;
- candidate: `src/multica_py/_generated/upstream_candidate_contract.json`;
- supported: `src/multica_py/_generated/upstream_supported_contract.json`;
- coverage: `src/multica_py/_generated/upstream_coverage.json`.

Collection always materializes the canonical candidate. Caller `--output`
receives byte-identical convenience output but state always records the
canonical path.

For this release, raw collection is not promotable because the binary lacks
`__contract` and the captured evidence is `help-degraded`. The sole staging
path is the exact `stage-reviewed-candidate` command in `quickstart.md`. It:

1. requires evidence trust exactly `help-degraded`;
2. verifies archive SHA-256
   `7413ada5907a7cf9e8618ca9c348160b015d5b21beb34b7d96af8705018aaaf4`,
   executable SHA-256
   `e92149ee958db469ac75c3d79b955f5f97c8753f740e7da0138d28431e9de4f8`,
   release ID, tag, commit, exact version JSON
   `{"arch":"arm64","commit":"ecbdbda09","date":"2026-07-23T10:22:51Z","go":"go1.26.1","os":"darwin","version":"0.4.9"}`,
   and provenance
   digest from the release-provenance file;
3. validates the approved contract and all pinned source refs;
4. rejects any governed evidence operation that contradicts the approved
   command path; missing help rows remain non-authoritative;
5. writes a candidate containing both evidence and approved semantic hashes
   with trust exactly `approved-contract-bound`.

`approved-contract-bound` is promotable only with the maintainer decision
below. It is never renamed to `verified`.

## Promotion Preconditions

Promotion dry-check must verify:

- canonical candidate exists and strictly decodes;
- candidate kind, version, tag, commit, and recomputed semantic hash match
  state;
- decision binds candidate semantic hash;
- decision binds approved contract semantic hash;
- decision binds exact release provenance;
- previous supported identity matches current state;
- generator `--check` is green;
- cross-artifact validation is green.

The decision file is external authority. It must pre-exist, contain the real
maintainer identity, decision `approve`, candidate and approved hashes, target
tuple, provenance ref/hash, previous supported identity, and
`review_ref="specs/007-upstream-v0-4-9-migration/contracts/operation-decisions.md"`.
Automation and implementation agents must not create or edit it.

Successful promotion uses a rollback-capable transaction to replace the
canonical supported artifact/state
and their approved coverage, CLI-manifest, and live-target projections, then
clears candidate state. The five promotion destinations are:

1. `src/multica_py/_generated/upstream_supported_contract.json`;
2. `src/multica_py/_generated/upstream_state.json`;
3. `src/multica_py/_generated/upstream_coverage.json`;
4. `src/multica_py/_generated/cli_manifest.json`;
5. `contracts/multica-live-target.toml`.

`promote --check` renders all five bytes in memory and runs
`validate_promotion_projection`; it does not require the pre-promotion active
files to already identify `v0.4.9`. A writing promotion uses the same validated
bytes, replaces all five through one staged write boundary, then
`validate_supported_target` checks the active result.

Cross-directory atomicity is not claimed. The selected failure contract is:

1. acquire exclusive `.devlocal/upstream-promotion.lock`;
2. render and validate all five byte strings;
3. write/fsync `.devlocal/upstream-promotion-journal.json` containing the
   transaction ID, ordered destinations, original existence/hash, staged hash,
   completed ordinal, and state `prepared`;
4. beside every destination write/fsync a stage file and, if it exists, a
   byte-identical backup;
5. replace in the five-file order above; after each replace fsync the parent
   and journal the completed ordinal;
6. on any caught failure restore completed destinations in reverse order,
   deleting destinations originally absent, fsync parents, mark `rolled_back`,
   clean stage/backups, and raise `PromotionTransactionError`;
7. on success mark `committed`, fsync, remove journal/stage/backups, release;
8. command startup recovers a `prepared` journal with the same reverse restore;
   `committed`/`rolled_back` journals require cleanup only.

Failure-injection tests cover before and after each replace ordinal 1..5 and
after each journal update; every original SHA-256 must be restored.

## Exact Target Provenance

- target tag: `v0.4.9`;
- version: `0.4.9`;
- commit: `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`;
- release ID: `358605496`;
- Darwin arm64 archive SHA256:
  `7413ada5907a7cf9e8618ca9c348160b015d5b21beb34b7d96af8705018aaaf4`;
- Darwin arm64 executable SHA256:
  `e92149ee958db469ac75c3d79b955f5f97c8753f740e7da0138d28431e9de4f8`;
- backend manifest digest:
  `sha256:6e1527dd54c55c46e8b1f781d1ae118976a377a009b8a67f1de92e10bb6cf434`;
- backend Linux amd64 digest:
  `sha256:645199276fa75927fca835a2a8cddbfa476f32cf97337fd7f2c113b650606438`.

Other platform CLI checksums must be copied exactly from
`.devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/release-provenance.json`,
never inferred.

## Cross-Artifact Coherence

One fail-closed validator, invoked by `upstream_contract check` and an offline
contract test, compares:

- approved schema-v2 target and hash;
- generated compatibility projection;
- semantic supported contract and generated state;
- corresponding coverage bindings for the 16 IDs;
- CLI manifest metadata;
- live target TOML;
- release provenance;
- canonical refs and semantic hashes.

It requires each governed ID exactly once, matching bindings, exact target
identity/checksums/digests, and either a valid canonical candidate or no
candidate. Unrelated existing coverage remains present but unapproved.
Evidence presence cannot approve any of the 35 target additions.

Any mismatch is `INVALID_ARTIFACT` and blocks support. Candidate state has
exactly two accepted coherent states: `null`, or a valid reference to
`src/multica_py/_generated/upstream_candidate_contract.json`; no other path or
partially populated state is accepted.

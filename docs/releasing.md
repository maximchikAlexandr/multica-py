# Releasing

## Release gates

Before a release, run the Ruff, mypy, offline pytest, coverage, contract, and
wheel/package checks from `docs/contributing.md`. The package must import from
a clean isolated wheel without the repository on `PYTHONPATH`.

## Upstream contract review

For a pinned upstream release, maintainers collect review evidence, edit the
approved contract in Git, validate the pinned source, render the generated
runtime, and run the deterministic check:

```text
collect → validate --source-checkout → render → check
```

The current approved target is `v0.7.1` with compatibility interval
`[0.6.2, 0.7.2)`. The pinned commit, release asset/checksum, and exact
commands for this review are maintained in
[docs/compatibility.md](compatibility.md).
The direct comparison source is `0.6.2` at commit
`7ab92d7622ecd81d179a8d83ae2dea74835a5069`; the target source commit is
`aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` (release `425269384`). Verify
runtime response ownership:
list and rename may decode visibility and sharing identities, while update
returns `RuntimeUpdateResult`; server-only access writes are not SDK operations.
Release archive SHA-256 values must be checked against official manifests
separately from extracted executable SHA-256 values. Run
`scripts/audit_source_links.py` and the contract `validate -> render -> check`
sequence before packaging.

The composition gate verifies the immutable composition parents against
`COMPOSITION_PLANNING_SHA` and OpenSpec byte equality against
`VERIFIED_PLANNING_SHA`. It also checks accepted WP commits and candidate
ancestry. Keep these identities separate in release automation.

Git review and merge are the only promotion action. The repository keeps one
committed generated runtime projection; transient documentation, compatibility,
provenance, evidence, and build outputs are not golden copies.

## Package provenance

The published distribution is `multica-py`, imported as `multica_py`. Public
operation coverage and approved source references are recorded in
`contracts/sdk-contract.json` and the baseline specifications under
`openspec/specs/`.

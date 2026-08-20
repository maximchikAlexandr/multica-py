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

The current approved target is `v0.4.28` with compatibility interval
`[0.4.28, 0.4.29)`. The pinned commit, release asset/checksum, and exact
commands for this review are maintained in [docs/compatibility.md](compatibility.md).

Git review and merge are the only promotion action. The repository keeps one
committed generated runtime projection; transient documentation, compatibility,
provenance, evidence, and build outputs are not golden copies.

## Package provenance

The published distribution is `multica-py`, imported as `multica_py`. Public
operation coverage and approved source references are recorded in
`contracts/sdk-contract.json` and the baseline specifications under
`openspec/specs/`.

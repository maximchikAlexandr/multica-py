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

The current approved target is `v0.6.1` with compatibility interval
`[0.6.0, 0.6.2)`. The pinned commit, release asset/checksum, and exact
commands for this review are maintained in [docs/compatibility.md](compatibility.md).
The target source commit is
`2ea01ae4ef55de4310b99af192d2dbd367832883`; the `0.6.0` source commit
`48745d2fe9e80ee9c027293ef22971ff5723f5f5` is comparison provenance only.
Release archive SHA-256 values must be checked against official manifests
separately from extracted executable SHA-256 values. Run
`scripts/audit_source_links.py` and the contract `validate -> render -> check`
sequence before packaging.

Git review and merge are the only promotion action. The repository keeps one
committed generated runtime projection; transient documentation, compatibility,
provenance, evidence, and build outputs are not golden copies.

## Package provenance

The published distribution is `multica-py`, imported as `multica_py`. Public
operation coverage and approved source references are recorded in
`contracts/sdk-contract.json` and the baseline specifications under
`openspec/specs/`.

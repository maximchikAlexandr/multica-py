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

The current approved target is `v0.6.0` with compatibility interval
`[0.5.3, 0.6.1)`. The pinned commit, release asset/checksum, and exact
commands for this review are maintained in [docs/compatibility.md](compatibility.md).
The target source commit is
`ea94c7cd5bbce9c8e1f28c5fa049c47ee7651d02`; the `0.5.3` source commit
`c1842ae2dfcd0cc5e739b7785d3209d5e72d01ed` is comparison provenance only.
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

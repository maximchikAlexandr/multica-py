# Decision Log

## 2026-07-12 — Initial SDK specification

- Scope is the complete documented Multica CLI.
- Architecture is one client plus resource classes plus immutable typed models.
- The library wraps the CLI only; no direct REST client is included.
- Runtime models and decoding use `msgspec`, not Pydantic or dataclasses.
- All code must be precisely typed and pass strict mypy without `Any`.
- Development and publishing workflows use `uv`.
- Built wheel and source distribution must remain installable through standard `pip`.
- Ruff configuration starts from the supplied rule set, removes Odoo-only configuration and disables `COM812`.
- MIT is the selected license.

## 2026-07-12 — PyPI distribution with uv-first usage

- `multica-py` is published as a normal PyPI distribution.
- Primary consumer installation is documented through `uv add multica-py` and `uv pip install multica-py`.
- Standard `pip install multica-py` remains supported as a compatibility path, but is not the primary workflow.


## 2026-07-12 — uv tool as the primary consumer workflow

- The package remains a PyPI distribution and Python library.
- Primary end-user installation is `uv tool install multica-py`.
- Primary ad-hoc execution is `uvx multica-py`.
- Project-level SDK use is supported through `uv add multica-py`.
- `uv pip install` and `pip install` remain compatibility paths.
- The distribution exposes a `multica-py` console entry point implemented on top of the same typed resource and transport layers.

## 2026-07-12 — Source-pinned implementation plan

- Pinned Multica upstream baseline to `48b8dbf43971e5ea974bf827220cd212a1240c72`.
- Python package/import name is `multica_py`; PyPI distribution and tool name are `multica-py`.
- Python 3.12+; Linux and macOS supported in v1; Windows not promised.
- Hatchling is the build backend; uv drives all development/build/release commands.
- v1 public SDK is synchronous only.
- The installed uv tool provides doctor/version/coverage/exec utilities rather than duplicating the entire Multica CLI.
- Error subclasses are used only when exact source/structured behavior supports classification; no localized string guessing.
- Full command registration and method placement are fixed in `contracts/cli-coverage.md`.

## 2026-07-12 — Task decomposition finalized

- Implementation is split into 112 dependency-ordered tasks.
- The MVP is transport + pinned manifest + complete issue-family support.
- Every command family must be implemented vertically with source provenance, exact models, command tests, fixture contracts, and fake-binary integration tests.
- No command, flag, model field, retry behavior, async API, or packaging decision is left to the implementer.
- The SDK remains sync-only in v1 and service callers own thread offloading, Temporal Activities, and workflow idempotency.

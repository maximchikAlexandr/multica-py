# Releasing

## Release workflow

1. Update version in `pyproject.toml` `[project] version = "X.Y.Z"`
2. Commit with message `release X.Y.Z`
3. Tag: `git tag vX.Y.Z && git push --tags`
4. Create a GitHub Release for the tag
5. The `.github/workflows/release.yml` workflow:
   - Builds wheel and sdist via `uv build`
   - Installs wheel with `uv tool install --from dist/*.whl multica-py` and runs `multica-py version`
   - Installs in a clean venv with pip and verifies import
   - Publishes to PyPI via `uv publish` (Trusted Publishing)

## Release gating

- Tag validation: only semver tags matching `v*` trigger the release workflow
- Environment protection: PyPI publish requires the `pypi` environment with approval
- Artifact reuse: workflow builds once and reuses the same artifacts for all checks
- No long-lived tokens: uses OIDC Trusted Publishing

## Versioning

- SDK `1.x` targets pinned upstream `multica-ai/multica@48b8dbf`
- Patch: bug fixes, test additions, documentation
- Minor: new resource methods, backward-compatible model additions
- Major: breaking API changes, upstream baseline change

## Prerequisites

- PyPI Trusted Publishing configured at https://pypi.org/manage/project/multica-py/settings/
- GitHub environment `pypi` with `id-token: write` permission

## CI validation before release

All CI jobs must pass before a release tag is created:
- `lint`: Ruff check and format check on `src/`, `tests/`, `scripts/`
- `types`: strict mypy on `src/` (65 files, 0 errors) and `tests/scripts` (75 files, 0 errors)
- `test`: pytest on Python 3.12 and 3.13, Linux and macOS
- `build`: wheel and sdist produced, importable, entry point verified

## Package provenance

All model and command coverage is traceable to the pinned upstream source:
- `specs/001-full-cli-sdk/contracts/cli-coverage.md` — command-to-SDK mapping with upstream source URLs
- `specs/001-full-cli-sdk/contracts/model-source-map.md` — model struct mapping with Go source paths
- `src/multica_py/_generated/cli_manifest.json` — machine-readable command manifest with output modes and SDK methods
- `tests/fixtures/json/` — fixture responses with known exit codes and stdout shapes

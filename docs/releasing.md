# Releasing

## Release workflow

1. Update version in `pyproject.toml` `[project] version = "X.Y.Z"`
2. Commit with message `release X.Y.Z`
3. Tag: `git tag vX.Y.Z && git push --tags`
4. Create a GitHub Release for the tag

The `.github/workflows/release.yml` workflow on tag push:
- Builds wheel and sdist via `uv build`
- Verifies the wheel installs into a clean venv and `import multica_py` works
- Uploads the build artifacts to the GitHub Release

Distribution channel: **GitHub Releases** (no PyPI publish yet). Consumers install with `uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@vX.Y.Z"` or `pip install "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@vX.Y.Z"`. See README.md.

## Release gating

- Tag validation: only semver tags matching `v*` trigger the release workflow
- No PyPI publish in the loop — no long-lived tokens required
- Artifact reuse: workflow builds once and reuses the same artifacts for install/import checks

## Versioning

- SDK `1.x` targets pinned upstream `multica-ai/multica@48b8dbf`
- Patch: bug fixes, test additions, documentation
- Minor: new resource methods, backward-compatible model additions
- Major: breaking API changes, upstream baseline change

## CI validation before release

All CI jobs must pass before a release tag is created:
- `lint`: Ruff check and format check on `src/`, `tests/`, `scripts/`
- `types`: strict mypy on `src/` and `tests/scripts`
- `test`: pytest on Python 3.12 and 3.13, Linux and macOS
- `build`: wheel and sdist produced, importable in a fresh venv

## Package provenance

All model and command coverage is traceable to the pinned upstream source:
- `specs/001-full-cli-sdk/contracts/cli-coverage.md` — command-to-SDK mapping with upstream source URLs
- `specs/001-full-cli-sdk/contracts/model-source-map.md` — model struct mapping with Go source paths
- `src/multica_py/_generated/cli_manifest.json` — machine-readable command manifest with output modes and SDK methods
- `tests/fixtures/json/` — fixture responses with known exit codes and stdout shapes

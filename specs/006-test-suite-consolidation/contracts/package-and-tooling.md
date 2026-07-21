# Contract: Packaging and Tooling Boundary

## Package workflow

`.github/workflows/package-test.yml` содержит два jobs.

### `build-and-validate`

1. checkout;
2. setup uv and Python 3.12;
3. `uv sync --frozen --all-groups`;
4. `uv build` ровно один раз;
5. `uv run pytest -o addopts="" -q tests/packaging/test_artifacts.py`;
6. upload ровно один wheel и один sdist.

### `install`

1. download тот же artifact set;
2. pip install wheel в Ubuntu/macOS × Python 3.12/3.13;
3. `uv pip install` wheel один раз на Ubuntu/Python 3.12;
4. `uv add` wheel один раз на Ubuntu/Python 3.12.

Total install paths: `6`.

`.github/workflows/ci.yml` не содержит distribution build job и `uv build` в compatibility cells. Default pytest selection исключает marker `packaging`; artifact tests запускаются только job `build-and-validate` с `-o addopts=""`.

## Artifact test

`tests/packaging/test_artifacts.py` fails, если `dist/` не содержит ровно один wheel и один sdist. Skip запрещён.

Wheel assertions:

- содержит package metadata и `multica_py/py.typed`;
- не содержит `tests`, `scripts`, `tools`, `specs`, `.specify`, `.agents`, `.opencode`, local artifacts.

Sdist assertions:

- содержит `src`, `tests`, `scripts`, `tools/live_support`, docs, README, LICENSE, pyproject and lock;
- не содержит local state/cache/build directories.

## Shared tooling

- `tools/live_support/environment.py`: `LiveSetupError`, `CompatibilityTarget`, shared settings/target parsing.
- `tools/live_support/diagnostics.py`: `VERIFICATION_CODE`, shared scan/redaction functions.
- Scripts import only these modules for shared live support.
- Test-only fixtures/hooks/assertions остаются в `tests/`.
- `tools/live_support` включён в sdist и исключён из wheel.

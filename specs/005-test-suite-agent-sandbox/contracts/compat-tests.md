# Contract: Compatibility Marker Assignment

## Minimum collected tests

`pytest --collect-only -q -m compat` MUST report at least four items before PR-07 merge.

## Required modules

| Module | Purpose | Marks |
|---|---|---|
| `tests/packaging/test_import_smoke.py` | `import multica_py` succeeds after install | `compat` |
| `tests/packaging/test_wheel_install.py` | wheel install smoke on matrix Python | `compat` |
| `tests/unit/test_path_normalization.py` | canonical absolute path behavior | `compat` |
| `tests/component/test_project_resources.py` | one project-resource argv smoke case marked `compat` | `compat` |

## CI gate

Each compatibility matrix cell runs:

```bash
uv run pytest -q -m compat
```

If collected item count is zero, the job MUST fail with an explicit message naming this contract.

## Platform coverage

Four cells MUST exist: Ubuntu/macOS × Python 3.12/3.13. No full offline suite and no live tests run in compatibility jobs.

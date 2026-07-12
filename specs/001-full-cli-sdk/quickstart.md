# Quickstart and Validation Scenarios

## Consumer installation

```bash
uv tool install multica-py
multica-py doctor
```

Ephemeral:

```bash
uvx multica-py version
```

Library:

```bash
uv add multica-py
```

The upstream `multica` executable must be installed separately.

## Contributor workflow

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests scripts
uv run pytest
uv build
```

## Required validation scenarios

1. Fake binary receives global flags in exact order and command flags exactly as source requires.
2. Missing binary raises `ExecutableNotFoundError` without importing or initializing external state.
3. Issue JSON decodes into immutable models and ignores additive unknown fields.
4. Missing required issue field raises `OutputShapeError`.
5. Repeated metadata/attachment flags preserve caller order.
6. Mutually exclusive description inputs cannot be constructed as a valid request.
7. Timeout terminates a spawned child process tree.
8. Token arguments are redacted from exception text and logs.
9. `uv tool install` of the local wheel exposes `multica-py`.
10. `uvx --from <wheel> multica-py version` works.
11. Standard pip can install the wheel and import `multica_py`.
12. Coverage audit fails when a Cobra command is added to the pinned manifest without an SDK row.

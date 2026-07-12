# Contributing

## Setup

```bash
uv sync --frozen --all-groups
```

## Quality gates

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests scripts
uv run pytest
uv build
```

## Adding a new command

1. Add the command entry to `src/multica_py/_generated/cli_manifest.json`
2. Create or update the resource method in `src/multica_py/resources/`
3. Create the model in `src/multica_py/models/`
4. Add tests under `tests/unit/resources/`, `tests/contract/`, `tests/integration/`
5. Update `specs/001-full-cli-sdk/contracts/cli-coverage.md`

# Contract: Mutation Scope

## Tool configuration

Dependency group: `mutation` (`mutmut>=3,<4`).

`pyproject.toml` MUST contain:

```toml
[tool.mutmut]
paths_to_mutate = [
  "src/multica_py/_internal/transport/",
  "src/multica_py/_internal/decoding/",
  "src/multica_py/_internal/errors/",
  "src/multica_py/_internal/redaction/",
  "src/multica_py/config.py",
]
tests_dir = "tests/unit tests/component"
runner = "uv run pytest -x -q -m 'not live and not serial'"
```

## Included logic categories

- argv construction and flag ordering;
- wire JSON decoding and error mapping;
- presence semantics helpers;
- secret redaction helpers;
- timeout and non-zero exit construction in pure helpers.

## Explicit exclusions

- `src/multica_py/models/**`
- `tests/**`
- `scripts/**`
- generated CLI manifest files
- live helpers and Docker/bootstrap code

## Execution constraints

- no Docker Compose startup;
- no live marker collection;
- no mutation-score or survivor-count merge gate;
- complete textual `mutmut results` uploaded as CI artifact.

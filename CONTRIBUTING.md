# Contributing to multica-py

## Setup

```bash
git clone https://github.com/maximchikAlexandr/multica-py.git
cd multica-py
uv sync --frozen --all-groups
git config core.hooksPath .githooks
```

## Style & quality

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests scripts
uv run pytest -m "not live"
uv build
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) and are enforced by the local `commit-msg` hook.

## Tests

Default suite is offline: `uv run pytest -m "not live"` stays green and needs no backend or network. See [tests/live/README.md](tests/live/README.md) for the live smoke setup.

New or changed tests must be table-driven (`@pytest.mark.parametrize`) over shared case containers in `tests/unit/resources/` and `tests/component/resources/cases.py`. Reuse shared fixtures and factories (`make_target`, `make_settings`, `mock_transport`, the fake-CLI client fixture, `register_resource`, `test_identity`) — do not re-copy local helpers. Assert precisely with a complete `expected_argv` value and the exact transport method. Full rules are in [AGENTS.md](AGENTS.md) under "Writing Tests".

## Pull requests

1. Create a feature branch (`git checkout -b feat/your-feature`).
2. Make your changes; ensure the commands above pass locally.
3. Push and open a PR against `main`. CI must pass before merge.
4. Use [GitHub Issues](https://github.com/maximchikAlexandr/multica-py/issues) for bug reports and feature requests.

## Upstream contract workflow

The approved SDK contract in `contracts/sdk-contract.json` is the only reviewed input that may change generated public SDK behaviour. Maintainer sequence and policy are documented in [docs/contributing.md](docs/contributing.md).

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
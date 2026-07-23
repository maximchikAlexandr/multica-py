# multica-py

Python SDK wrapping the [Multica CLI](https://github.com/multica-ai/multica). Library-only — embed it in FastAPI, Temporal workers, scripts, anything that already drives the upstream `multica` binary via subprocess. No CLI of its own.

## Prerequisites

Install the upstream `multica` binary separately (see its README). The SDK finds it on `$PATH` or via `ClientConfig(executable=...)`.

## Installation

Not yet on PyPI. Install directly from GitHub.

`uv` (recommended):

```bash
# pinned to a tag
uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@v0.1.0"
# or follow main
uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py"
```

`pip`:

```bash
pip install "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@v0.1.0"
```

Lock reproducibility: this repo pins every transitive dep in `uv.lock`. For `uv`, `uv sync --frozen` verifies the lockfile; for `pip`, prefer the `--require-hashes` flow once hashes are exported.

## Usage

```python
from multica_py import ClientConfig, MulticaClient

client = MulticaClient(ClientConfig())
for issue in client.issues.list():
    print(issue.title)
```

`ClientConfig` is an immutable `msgspec.Struct` (`executable`, `server_url`, `workspace_id`, `profile`, `cwd`, `environment`, `timeout`, `compatibility`, `debug`, `encoding`, `max_processes`). The client exposes derived constructors: `with_profile`, `with_workspace`, `with_timeout`, `with_cwd`, `with_environment`.

### Self-hosted / local

```python
from multica_py import ClientConfig, MulticaClient

config = ClientConfig(
    executable="/usr/local/bin/multica",
    server_url="http://localhost:8080",
    workspace_id="ws_local",
    profile="self-hosted",
)
client = MulticaClient(config)
```

Interactive first-time local setup is process-backed:

```python
process = client.setup.self_host("http://localhost:8080")
process.wait()
```

### FastAPI

```python
from datetime import timedelta
from fastapi import FastAPI
from multica_py import ClientConfig, MulticaClient

app = FastAPI()
client = MulticaClient(ClientConfig(timeout=timedelta(seconds=30)))

@app.get("/issues")
def list_issues():
    return [i.title for i in client.issues.list()]
```

Full pattern catalog: [docs/service-usage.md](docs/service-usage.md). API surface: [docs/api.md](docs/api.md). Resource coverage: [docs/cli-coverage.md](docs/cli-coverage.md).

## Security notes

- The SDK wraps an external `multica` binary via `subprocess`. The upstream `auth login` accepts the token only on argv, so the token is briefly visible to other local users via `ps`/`/proc/<pid>/cmdline` while the login process is running. Redaction scrubs it from logs and `CommandExecutionError` payloads, but on a shared host treat the live process as observable.
- `ClientConfig.server_url` must be `https://...`; `http://localhost`, `http://127.0.0.1`, `http://[::1]` are allowed for local dev.
- Output from the `multica` binary is JSON-decoded via `msgspec` (strict, no `eval`/`pickle`).

## Development

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests scripts
uv run pytest
uv build
```

`uv.lock` is the integrity gate — it pins exact versions and SHA-256 hashes. Use `uv sync --frozen` for verified reproducible installs.

### Test architecture gate

The test suite ships a five-stage architecture gate that protects the
behavioral manifest, duplicate-removal map, and the final LOC/file budgets
declared in `specs/006-test-suite-consolidation/contracts/quality-gates.md`.
Each stage activates a strict superset of the previous one's checks.

```bash
# gate stages, in order
uv run python scripts/check_test_architecture.py --stage pr1
uv run python scripts/check_test_architecture.py --stage pr2
uv run python scripts/check_test_architecture.py --stage pr3
uv run python scripts/check_test_architecture.py --stage pr4
uv run python scripts/check_test_architecture.py --stage final

# baseline compare for any non-pr1 stage
uv run python scripts/check_test_baseline.py --baseline tests/quality-baseline.json --stage <stage>
```

The `final` stage verifies three budgets: `tests_python ≤ 10500`,
`live_support_python ≤ 2500`, and max single-file LOC `≤ 800`. By default
the gate prints `WARN` / `NOTE` lines on exceedance and exits 0 (the
slim-down is best effort and the limits are aspirational at this
snapshot). Add `--strict-final` to either script to hard-fail on
exceedance:

```bash
uv run python scripts/check_test_architecture.py --stage final --strict-final
uv run python scripts/check_test_baseline.py --baseline tests/quality-baseline.json --stage final --strict-final
```

The manifest (`tests/behavioral-coverage.json`) and baseline
(`tests/quality-baseline.json`) are immutable after `pr1`; only
stage-gated invariant keys may be added at `pr3` and later stages per
`specs/006-test-suite-consolidation/data-model.md` rule 5.

### Live integration tests

Live tests exercise the SDK against a real Multica CLI and an isolated backend. Default
`uv run pytest` excludes them via `-m "not live"`.

Prerequisites: Docker, a Multica checkout at the pinned commit, and the matching CLI binary.
See [tests/live/README.md](tests/live/README.md) for environment variables and safety rules.

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
uv run python scripts/run_live_tests.py --resolve-cli
```

Blocking PR smoke (CI): `pytest -m live_smoke tests/live`. Extended compatibility tests use
`-m "live_smoke or live_extended"` and run on a separate schedule (post-MVP).

Compatibility target updates require editing `contracts/multica-live-target.toml`, running
contract checks, extended smoke, and digest verification — see
[tests/live/README.md](tests/live/README.md).

## License

MIT

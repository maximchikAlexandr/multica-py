# multica-py

[![CI Status](https://github.com/maximchikAlexandr/multica-py/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/maximchikAlexandr/multica-py/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Python SDK wrapping the [Multica CLI](https://github.com/multica-ai/multica).

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
from multica_py import IssueStatus, MulticaClient

client = MulticaClient()
page = client.issues.list(limit=50)
for issue in page:
    print(issue.title)

# Read results are bound Issue values, so an entity action is available
# immediately without a second get call.
if page.items:
    preview = page.items[0].set_status_command(IssueStatus.in_progress)
    updated = preview.run()
```

The default client is suitable for a first local workflow. For an integration,
configure one immutable `ClientConfig` at the composition boundary and pass a
small adapter to application code. Derived views created by `with_options`
(or its `with_profile`, `with_workspace`, `with_timeout`, `with_cwd`, and
`with_environment` delegators) retain independent routing/execution settings
while sharing the same process limit.

```python
from datetime import timedelta

from multica_py import ClientConfig, CompatibilityPolicy, MulticaClient

client = MulticaClient(
    ClientConfig(
        server_url="https://multica.example.com",
        profile="automation",
        compatibility=CompatibilityPolicy.strict,
        max_processes=4,
    )
)
scoped = client.with_options(profile="worker", timeout=timedelta(seconds=30))
page = scoped.issues.list(status=IssueStatus.backlog, limit=50)
```

### Traverse related resources

```python
workspace = client.workspaces.get("ws_123")

# Property access is passive. all(), page(), refresh(), iteration, and
# prefetch() are explicit load points.
projects = workspace.projects.all()
client.prefetch(projects, lambda project: project.issues, max_parallel=4)

for project in projects:
    for issue in project.issues:
        print(project.name, issue.title)
```

Bound entities retain their originating client context and own their lazy
cache. Use `entity.to_dict()` or `entity.to_json()` when you need a passive
immutable snapshot for serialization, comparison, or a message boundary.

Successful actions return `ActionResult[T]`; inspect payloads through
`.value` (void actions use `ActionResult[None]`). Canonical/direct-resource
collections expose immutable `Page[T]` values and `.items`; relation
`.all()` snapshots intentionally remain tuples.

### Reliable automation patterns

For long-running workers and service integrations:

- use `CompatibilityPolicy.strict` so an unreviewed CLI version fails early;
- filter and page on the server before doing local selection;
- read the current issue before a guarded status transition;
- store an external idempotency key in issue metadata;
- use a stable marker when a retried workflow must not duplicate a comment;
- catch typed `MulticaError` subclasses at the adapter boundary.

See the runnable examples:

- [production client and scoped views](examples/production_client.py);
- [server-filtered queue selection](examples/issue_queue.py);
- [idempotent metadata, comments, and guarded status changes](examples/issue_workflow.py);
- [bound resource graph](examples/resource_relations.py);
- [local self-hosted setup](examples/self_hosted_local.py).
- [direct inputs, scoped options, raw CLI, uploads, and permalinks](examples/public_workflow.py).

The full pattern catalog is in [docs/service-usage.md](docs/service-usage.md).
See also the [API surface](docs/api.md), [migration guide](docs/migration.md),
and [CLI coverage](docs/cli-coverage.md).

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

### Live smoke

Live smoke uses a prepared target and the public SDK only. Default `uv run pytest` excludes
it via `-m "not live"`. Set the five runner values documented in
[tests/live/README.md](tests/live/README.md), then run:

```bash
uv run pytest -o addopts="" -q -m live_smoke tests/live/test_smoke.py
```

## License

MIT

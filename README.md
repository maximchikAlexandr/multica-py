# multica-py

Python SDK for the [Multica CLI](https://github.com/multica-ai/multica).

## Installation

```bash
uv tool install multica-py
```

Ephemeral execution:

```bash
uvx multica-py version
```

Library use:

```bash
uv add multica-py
```

The upstream `multica` executable must be installed separately.

## Usage

```python
from multica_py import MulticaClient, ClientConfig

config = ClientConfig()
client = MulticaClient(config)

issues = client.issues.list()
for issue in issues:
    print(issue.title)
```

## Self-hosted Example

```python
from multica_py import ClientConfig, MulticaClient

config = ClientConfig(
    executable="/usr/local/bin/multica",
    server_url="http://localhost:8080",
    workspace_id="ws_local",
    profile="self-hosted",
)
client = MulticaClient(config)

status = client.auth.status()
print(status.authenticated)

for project in client.projects.list():
    print(project.name)
```

For first-time interactive setup against a local self-hosted instance:

```python
process = client.setup.self_host("http://localhost:8080")
process.wait()
```

## Development

Dependencies are hash-pinned in `uv.lock`; use `uv sync --frozen` for verified, reproducible installs.

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests scripts
uv run pytest
uv build
```

## License

MIT

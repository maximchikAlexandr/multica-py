# Execution backends

`MulticaClient` runs commands locally by default. To use another target, create
an executor explicitly and inject it into the client. There is no plugin
registry, entry-point discovery, automatic provider activation, or runtime
package installation.

```python
from multica_py import MulticaClient
from multica_py.execution.ssh import SshExecutor

with SshExecutor(host="vps.example", username="deploy") as executor:
    with MulticaClient(executor=executor) as client:
        client.issues.list()
```

The common API is `CommandExecutor`, `ExecutionRequest`, `ExecutionResult`,
`ProcessHandle`, and `LocalExecutor`, imported from `multica_py.execution`.
Optional adapters are intentionally imported only from their submodules:
`multica_py.execution.microsandbox` and `multica_py.execution.ssh`.

## Installation

Base installation stays lightweight:

```bash
uv add multica-py
pip install multica-py
```

Install exactly one optional build when it is needed:

```bash
uv add "multica-py[microsandbox]"
uv add "multica-py[vps]"
pip install "multica-py[microsandbox]"
pip install "multica-py[vps]"
```

For this repository's Git distribution, use:

```bash
uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py"
uv add "multica-py[microsandbox] @ git+https://github.com/maximchikAlexandr/multica-py"
uv add "multica-py[vps] @ git+https://github.com/maximchikAlexandr/multica-py"
```

Pin either build to a release tag or commit SHA:

```bash
uv add "multica-py[microsandbox] @ git+https://github.com/maximchikAlexandr/multica-py@<tag-or-commit>"
uv add "multica-py[vps] @ git+https://github.com/maximchikAlexandr/multica-py@<tag-or-commit>"
```

For an existing Git dependency, retain its source and enable the selected
extra:

```bash
uv add --extra microsandbox multica-py
uv add --extra vps multica-py
```

`microsandbox` is tested with `microsandbox>=0.6,<0.7`; `vps` is tested with
`paramiko>=3,<4`. Constructing a provider without its extra raises an
actionable `ImportError` naming the corresponding `multica-py[...]` install.

## Target boundaries and lifecycle

`ClientConfig.executable` and `cwd` name paths on the execution target. Use
strings for remote paths. `ClientConfig.environment` contains only explicit
target-process overrides; controller environment is not forwarded. Preview is
provider-independent and conservatively redacts controller secrets without
executing, staging, or reading files.

Uploads and runtime temporary content are read on the controller, staged on
the target through `executor.stage(label, content)`, then removed as the
staging context exits. The staged path is target-local.

A client closes only its default local executor. A caller-supplied executor
outlives root and scoped clients and should be closed by its owner. `ManagedProcess.id`
is provider identity; `.pid` is an integer only where a controller-visible Unix
PID exists.

Process control is provider-specific:

- Local execution terminates the process group and guarantees descendant cleanup.
- Microsandbox sends per-command `SIGTERM` or native `SIGKILL`; descendant cleanup is not guaranteed.
- SSH closes its channel as best effort; the remote process may continue and descendant cleanup is not guaranteed.

`SshExecutor` rejects unknown host keys by default. Enable unknown keys only
when the trust decision is explicit (`allow_unknown_host_key=True`).
It also disables the legacy SHA-1 `ssh-rsa` host-key and public-key algorithms;
this secure default is not configurable by callers.

## Adding a provider adapter

1. Implement the public `CommandExecutor` protocol in one isolated adapter module.
2. Map target connection, missing-target, and unavailable failures to the common execution errors; keep reachable executable failures as the existing executable errors.
3. Preserve target-local argv, cwd, explicit environment, stdin, timeout, staging, and non-destructive `close()` semantics.
4. State and test the provider's own streaming, collection, process-control, and descendant-cleanup guarantees.
5. Add focused provider tests plus a factory row to the shared executor-conformance suite; do not branch transport, command plans, resources, or models by provider.
6. If first-party, add a bounded optional extra, lazy import at constructor time, explicit-import documentation, and an opt-in live smoke test.

CubeSandbox is only compatibility-gated in this change. It has no adapter,
extra, image/template build, or automatic fallback here.

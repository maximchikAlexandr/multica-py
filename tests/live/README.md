# Prepared-target live smoke

The live suite uses an externally prepared Multica target and the public SDK
only. It is excluded from offline verification.

Set these five runner environment values before collecting or running the
suite:

- `MULTICA_LIVE_CLI`
- `MULTICA_LIVE_EXPECTED_VERSION`
- `MULTICA_LIVE_SERVER_URL`
- `MULTICA_LIVE_WORKSPACE_ID`
- `MULTICA_LIVE_PROFILE`

The profile is preauthenticated by the prepared environment owner. No
credential is copied into the repository, pytest environment, artifacts, or
command line.

The prepared workspace must contain at least one member, agent, skill, squad,
autopilot with a task-backed run, and issue with a task run. The suite creates
only uniquely named project/issue/comment/metadata records and reports their
IDs in captured proof output; project cleanup removes the test-owned graph.

Run the smoke suite with:

```bash
uv run pytest -o addopts="" -q -rP \
  -m live_smoke tests/live
```

Executor smoke tests in `test_executor_smoke.py` additionally require either
the prepared SSH variables or `MULTICA_LIVE_MICROSANDBOX`; unconfigured
backend rows skip without affecting the ordinary prepared-target smoke.

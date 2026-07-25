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

Run the smoke suite with:

```bash
uv run pytest -o addopts="" -q \
  -m live_smoke tests/live/test_smoke.py
```

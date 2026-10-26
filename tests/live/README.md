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

The prepared CLI MUST be `0.7.0`. The fixture uses
`CompatibilityPolicy.strict` with the generated compatibility bounds
`[0.6.2, 0.7.1)` and no local version override. Client construction is
I/O-free; the first public SDK operation performs the JSON version preflight.

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

## Protected GitHub smoke

The `Live smoke` workflow is manually dispatched with `pr_number` and a full
`candidate_sha`. Its uncredentialed authorization job resolves the open
same-repository PR head before the protected `multica-live` job starts. The
protected job checks out that immutable SHA with persisted Git credentials
disabled, requires CLI `0.7.0`, and uploads only sanitized SHA, status, and
cleanup evidence. A default-branch checkout, fork head, or SHA mismatch is
rejected and is not release evidence.

## Isolated local walkthrough

From an independently authorized local test context, run the repository-native
walkthrough with an output directory outside the Git checkout:

```bash
uv run python scripts/e2e/verify_multica_test.py --output <run-owned-directory>
```

The script fixes the executable to wrapper-owned `multica-test` and does not
accept profile, server, workspace, token, or primary-CLI overrides. It performs
the strict `0.7.0` preflight, creates uniquely named disposable resources,
checks direct and create-time list-property assignments plus public read-back,
and archives/deletes only those resources on success or error. It writes
sanitized `manifest.json`, `stdout.txt`, `stderr.txt`, and `cleanup.json`
artifacts; it never writes credentials or raw target output.

## Required protected-controller setup

The controller is fail-closed unless dispatched from the trusted default
branch with repository variable
`MULTICA_LIVE_TRUSTED_WORKFLOW_REF=refs/heads/<default-branch>`. Before the
protected job starts it verifies that `multica-live` exists with at least one
named required reviewer, protected-branch deployment policy, and an active
default-branch ruleset requiring deployments. The runner label must resolve to
a repository-restricted isolated `multica-live` runner group; credentialed
execution requires an ephemeral runner. The required-reviewer identity must be
recorded by the repository owner/admin; this repository assumes none.

The current repository has no `multica-live` environment. This PR also cannot
supply a trusted default-branch controller before merge: a dispatch from the
PR ref is rejected, while a dispatch from the current default branch uses the
pre-merge workflow file. Therefore the protected job and V-12 evidence remain
blocked until the owner provisions the environment, reviewer, branch/ruleset
restrictions, isolated runner group, and trusted workflow variable above.

# Contract: Agent Runtime Live Helpers

Live sandbox helpers in `tests/live/backend.py` and `tests/live/resources.py` use the patterns below. Public SDK agent models MUST NOT gain new fields in this feature.

## Daemon start (subprocess, not `client.daemon.start()`)

Invoke the resolved Multica CLI binary from the pinned live target:

```text
multica daemon start --foreground
```

Environment (exact names):

| Variable | Value |
|---|---|
| `HOME` | `<temp_root>/home` |
| `MULTICA_PROFILE` | `<profile_name>` |
| `MULTICA_DAEMON_ID` | `<daemon_id>` |
| `MULTICA_WORKSPACES_ROOT` | `<workspaces_root>` |
| `MULTICA_OPENCODE_PATH` | absolute path to fake or real executable |
| `MULTICA_OPENCODE_MODEL` | `multica-test/fake` for deterministic workflow; canary model from env |
| `MULTICA_DAEMON_POLL_INTERVAL` | `1s` |
| `MULTICA_DAEMON_HEARTBEAT_INTERVAL` | `2s` |

Readiness: daemon subprocess is running and `multica daemon status` returns `running=true` within 10 seconds.

## Runtime readiness

Poll `client.runtimes.list()` every 1 second for up to 60 seconds.

Ready when:

1. exactly one runtime is returned;
2. oracle helper confirms that runtime is online OpenCode for `<daemon_id>` (bootstrap/API JSON fields `provider == "opencode"` and `daemon_id == <daemon_id>`).

Store returned runtime ID in `LiveRunContext.runtime_id`.

## Agent create

```python
client.agents.create(AgentCreateRequest(name=f"{prefix}-agent"))
```

No provider or runtime flags are passed. Routing is established by issue assignment to the created agent.

## Issue assignment

Exactly one call:

```python
client.issues.assign(
    IssueAssignmentRequest(issue_id=issue_id, agent_id=agent_id)
)
```

CLI argv:

```text
issue assign <issue_id> --to-id <agent_id>
```

## Run selection after assignment

1. Record `assigned_at = time.monotonic()` immediately after assign returns.
2. Poll `client.issues.runs(issue_id)` every 1 second.
3. Consider runs whose first observed timestamp is not before assignment.
4. Select the run with the greatest `started_at` among post-assignment runs; treat missing `started_at` as less than any present timestamp; fail if all candidates lack `started_at` after timeout.
5. Fail if more than one new run appears unless they share the same selected ID on consecutive polls.
6. Timeout after 120 seconds from assignment.

## Issue usage cost (canary)

Add optional field to public model:

```python
class IssueUsage(...):
    cost_usd: float | None = None
```

Canary failure when `cost_usd is None` or `cost_usd > 0.10`.

Upstream source for decode shape: Multica tag `v0.3.10`, command `issue usage`, file `cmd_issue.go`.

## Non-routable agent audit

Postcondition MUST call bootstrap/oracle helper `assert_agent_non_routable(agent_id)` which queries backend agent state and requires `routable == false` or HTTP 404.

## Upstream provenance note

Project-resource and issue `--project` mappings are documented in `contracts/project-resources-sdk.md`. Agent create/archive and runtime list remain on existing supported SDK methods without new public methods.

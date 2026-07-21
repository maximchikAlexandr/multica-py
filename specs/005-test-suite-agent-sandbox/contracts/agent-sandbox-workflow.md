# Contract: Agent Sandbox Live Workflow

## Profile

- pytest marker: `live_smoke`
- test name: `test_agent_executes_issue_in_local_directory`
- parallelism: forbidden
- workflow deadline: 120 seconds from assignment to terminal run
- runtime ready deadline: 60 seconds
- runtime deregistration deadline: 30 seconds

## Setup order

1. Create `LiveRunContext` and artifact directory.
2. Create isolated HOME, workspaces root and sandbox directory.
3. Write exact initial target/control files.
4. Start existing Compose backend and wait ready.
5. Create identity/token/workspace through `BootstrapApiClient`.
6. Write isolated CLI profile for that workspace.
7. Start foreground daemon per `contracts/agent-runtime-live-helpers.md` §Daemon start.
8. Poll public runtimes list until exactly one online matching runtime exists.
9. Create OpenCode agent by name only; runtime association is implicit via daemon registration and issue assignment.
10. Create project.
11. Create issue with project ID and no assignee.
12. Attach `local_directory` through public project-resource SDK.
13. List project resources and assert one exact matching record.
14. Record filesystem before manifest.
15. Assign issue to agent once via `IssueAssignmentRequest(issue_id=..., agent_id=...)`.
16. Poll runs to terminal using post-assignment selection rules from `contracts/agent-runtime-live-helpers.md`.
17. Record messages, entity state and filesystem after manifest.
18. Assert routing, status and file policy.

## Issue content

Title:

```text
Agent sandbox edit <run_id>
```

Description:

```text
Edit target.txt in the attached local directory.
Replace the exact current content with the exact replacement below.
Do not modify control.txt or any other user file.
MULTICA_TEST_ACTION={"schema":1,"path":"target.txt","before":"before:<run_id>\n","after":"after:<run_id>\n"}
```

## Cleanup registration

Register immediately after each side effect, but execute by the fixed sequence below.

## Fixed cleanup sequence

1. If latest run is nonterminal, call `issues.cancel_task(issue_id, run_id)` and wait terminal for up to 10 seconds.
2. Remove project resource through public SDK.
3. Archive agent through public SDK.
4. Delete project through public SDK.
5. Stop daemon process; send graceful stop, wait 10 seconds, then terminate, then kill after 5 seconds.
6. Poll runtimes until matching runtime is absent/non-routable, deadline 30 seconds.
7. Delete workspace through `BootstrapApiClient`; this is final containment for issue and archived agent records.
8. Remove isolated HOME/workspaces/sandbox directories.
9. Run postcondition audit.

Every step executes even if a prior step failed. Cleanup errors are accumulated.

## Postcondition audit

Assert workflow-owned leftovers are gone:

- daemon PID absent;
- matching runtime absent or explicitly offline/non-routable;
- no active/routable agent with run prefix;
- project resource not listable;
- project not gettable;
- workspace not returned by bootstrap oracle;
- isolated paths absent.

Compose backend lifecycle is session-scoped (`live_environment` fixture). Per-workflow
audit MUST NOT require compose project absence; session teardown runs
`audit_postconditions` after `compose down`.
## Failure variants

| Case ID | Configuration | Expected terminal run | Expected pytest outcome | Required diagnostics |
|---|---|---|---|---|
| `agent-error` | `MULTICA_TEST_AGENT_MODE=error` | `failed` | test passes after asserting failed run and unchanged user files | full bundle |
| `agent-timeout` | `MULTICA_TEST_AGENT_MODE=timeout` | nonterminal until cancel | test passes after deadline cancel and unchanged user files | full bundle |
| `wrong-edit` | `MULTICA_TEST_AGENT_MODE=wrong-edit` | `completed` | test passes after file assertion failure is observed and recorded | full bundle |
| `cleanup-failure` | env `MULTICA_TEST_INJECT_CLEANUP_FAILURE=remove-resource` | success path otherwise | test passes when primary success/failure is preserved, remaining cleanup completes, bundle records injected failure | bundle includes cleanup error |

### Cleanup-failure injection

When `MULTICA_TEST_INJECT_CLEANUP_FAILURE=remove-resource`, the cleanup adapter MUST raise `LiveCleanupError("remove-resource")` on the project-resource removal step only. Subsequent cleanup steps MUST still execute. Primary test outcome MUST remain the outcome that would occur without injection.

## Extended outcomes reference

Mode env values (`error`, `timeout`, `wrong-edit`) are distinct from pytest case IDs (`agent-error`, `agent-timeout`, `wrong-edit`).

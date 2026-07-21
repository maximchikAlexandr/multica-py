# Data Model — Spec 005

## 1. CommandCase

Immutable test descriptor.

| Field | Type | Required | Rule |
|---|---|---:|---|
| `id` | `str` | yes | `<resource>.<operation>.<variant>`, globally unique |
| `invoke` | callable | yes | invokes one public SDK operation |
| `expected_argv` | `tuple[str, ...]` | yes | literal expected tokens |
| `stdout` | `str` | no | default empty |
| `stderr` | `str` | no | default empty |
| `exit_code` | `int` | no | default 0 |
| `expected` | object | no | decoded result or sentinel |
| `expected_error` | error descriptor | no | mutually exclusive with success expected |
| `marks` | tuple | no | layer/compat/serial only |

Invariant: a case cannot define both `expected` success and `expected_error`.

## 2. CrudDescriptor

Immutable live CRUD descriptor.

| Field | Type | Rule |
|---|---|---|
| `resource_id` | `str` | unique stable name |
| `operations` | tuple enum | subset of create/get/list/update/delete |
| `make_create_request` | callable | deterministic minimal payload |
| `make_update_request` | callable | deterministic changed payload |
| `normalize` | callable | removes server-generated nondeterminism only |
| `fetch_oracle` | callable | independent backend/API read |
| `register_cleanup` | callable | registered immediately after create |
| `case_marks` | tuple | one of live_smoke/live_extended |
| `capabilities` | frozen set | pagination, naming, workspace_scope, presence |

Invariant: descriptor contains no orchestration loop and never calls another descriptor.

## 3. ProjectResourceRecord

Public typed model.

| Field | Type | Rule |
|---|---|---|
| `id` | `str` | non-empty |
| `project_id` | `str` | non-empty |
| `resource_type` | `str` | `local_directory` for this feature |
| `resource_ref` | `LocalDirectoryResourceRef` | decoded by discriminator |

## 4. LocalDirectoryResourceRef

| Field | Type | Rule |
|---|---|---|
| `local_path` | `str` | canonical absolute path |
| `daemon_id` | `str` | exact daemon ID |
| `label` | `str | None` | optional display label |

## 5. ProjectResourceAddLocalDirectoryRequest

| Field | Type | Rule |
|---|---|---|
| `local_path` | `str | Path` | resolved before argv construction |
| `daemon_id` | `str` | required |
| `label` | `str | None` | omitted means no `--ref-label` |

## 6. ProjectResourceUpdateLocalDirectoryRequest

| Field | Type | Rule |
|---|---|---|
| `local_path` | `str | Path` | required and resolved |

## 7. AgentSandboxInstruction

JSON object embedded after literal prefix `MULTICA_TEST_ACTION=`.

```json
{
  "schema": 1,
  "path": "target.txt",
  "before": "before:<run_id>\n",
  "after": "after:<run_id>\n"
}
```

Validation:

- exactly four keys;
- `schema == 1`;
- `path` is relative POSIX path;
- no empty segment, `.` or `..`;
- resolved path is inside provided `--dir`;
- target is regular file;
- current bytes equal UTF-8 encoding of `before` exactly.

## 8. LiveRunContext

| Field | Type | Rule |
|---|---|---|
| `run_id` | string | 32 lowercase hex chars |
| `prefix` | string | `multica-py-live-<run_id>` |
| `temp_root` | Path | created by pytest temp facility |
| `home` | Path | `<temp_root>/home` |
| `workspaces_root` | Path | `<temp_root>/workspaces` |
| `sandbox_dir` | Path | `<temp_root>/sandbox/project` |
| `profile_name` | string | prefix |
| `daemon_id` | string | prefix |
| `artifact_dir` | Path | configured root/run_id |
| `workspace_id` | optional string | set after bootstrap create |
| `project_id` | optional string | set after SDK create |
| `resource_id` | optional string | set after attach |
| `runtime_id` | optional string | set after daemon registration |
| `agent_id` | optional string | set after SDK create |
| `issue_id` | optional string | set after SDK create |
| `run_execution_id` | optional string | set after assignment |

## 9. DaemonRuntimeContext state machine

States:

`NEW → STARTING → PROCESS_RUNNING → RUNTIME_ONLINE → STOPPING → RUNTIME_DEREGISTERED → STOPPED`

Failure from any active state transitions to `FAILED`, then cleanup attempts `STOPPING → STOPPED`.

Rules:

- agent creation allowed only in `RUNTIME_ONLINE`;
- resource attach allowed only after daemon ID and runtime ID exist;
- temp path deletion allowed only after `STOPPED`.

## 10. Agent task state machine

Observed states:

`NOT_ASSIGNED → QUEUED → DISPATCHED/RUNNING → COMPLETED | FAILED | CANCELLED | TIMED_OUT`

Rules:

- assignment happens once;
- polling deadline 120 seconds;
- active state at deadline triggers cancel;
- only `COMPLETED` enters file success assertions.

## 11. FileManifest

Map from relative POSIX path to:

| Field | Type |
|---|---|
| `kind` | `file | directory | symlink` |
| `size` | integer |
| `sha256` | string for regular file |
| `symlink_target` | string for symlink |

Comparison policy:

- `target.txt`: must change to exact expected bytes;
- `control.txt`: no field may change;
- `AGENTS.md`: create/update allowed;
- `.multica/**`: create/update allowed;
- `.opencode/**`: create/update allowed (OpenCode native skills tree);
- `.agent_context/**`: create/update allowed (issue context files);
- every other path: create/remove/update forbidden.

## 12. CleanupAction

| Field | Type | Rule |
|---|---|---|
| `name` | string | stable diagnostic ID |
| `execute` | callable | idempotent |
| `registered_at` | monotonic timestamp | audit only |
| `status` | pending/succeeded/failed/already_absent | final record |
| `error` | sanitized string | only on failed |

Fixed execution order is defined by workflow contract, not inferred from registration order.

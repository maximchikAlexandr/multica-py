# Contract: Live Diagnostics Bundle

## Directory

Every live failure bundle directory is:

```text
<artifact-root>/<run_id>/
```

## Required files

| File | Content |
|---|---|
| `target.json` | Resolved live target metadata (tag, commit, digests) |
| `run-context.json` | `LiveRunContext` fields safe for diagnostics |
| `entities.json` | Sanitized workspace, project, issue, agent, resource, runtime snapshots |
| `runtime.json` | Runtime list/get state at failure time |
| `run-messages.json` | Issue run messages when available |
| `filesystem-before.json` | `FileManifest` before run |
| `filesystem-after.json` | `FileManifest` after run |
| `filesystem.diff` | Unified diff for `target.txt` and `control.txt` only |
| `daemon-status.json` | Daemon status JSON or subprocess exit metadata |
| `daemon.log.tail` | Last 200 lines of daemon logs |
| `compose-ps.txt` | `docker compose ps` output for the run compose project |
| `cleanup.json` | Ordered cleanup action results |
| `failure.json` | Primary failure classification, message, and accumulated cleanup errors |

## Redaction

Before write, replace values equal to token, JWT, database password, provider API keys, and every configured canary secret name with `<redacted>`.

## Reference

`spec.md` FR-046 MUST reference this contract verbatim. Implementers MUST NOT invent additional or alternate filenames.

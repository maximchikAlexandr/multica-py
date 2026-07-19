# Presence semantics and exception mapping

**Version:** 2  
**Pinned upstream CLI:** `server/cmd/multica/cmd_project.go`, `server/internal/cli/errors.go` @ `v0.3.35`  
**Pinned upstream HTTP:** `server/internal/handler/project.go` @ `v0.3.35`

## 1. SDK prerequisite (mandatory before US-003 / US-004 live asserts)

### 1.1 Presence / CLI flags

Current `ProjectUpdateRequest` uses `str | None = None`, so omit and explicit clear are indistinguishable. Before T042–T045:

1. Change `ProjectUpdateRequest` fields that participate in partial update to default `Unset` (`multica_py.sentinels.Unset`).
2. Align CLI flags with upstream: `project create/update` use `--title` (not `--name`). Public Python field may remain `name` only if argv mapping to `--title` is explicit and unit-tested.
3. Argv builder rules for `description`:
   - `Unset` → do not pass `--description`
   - `""` → pass `--description` `""` (flag Changed)
   - non-empty `str` → pass `--description` `<value>`
   - `None` → **unsupported on CLI path for MVP**; public API raises `ValidationError`

### 1.2 Exit-code → exception subclass mapping

Current transport raises only `CommandExecutionError`. Before T047–T051, map Multica CLI exit codes (`server/internal/cli/errors.go`) in SDK transport:

| CLI exit | SDK exception |
|---|---|
| `3` (ExitAuth; HTTP 401/403) | `AuthenticationError` |
| `4` (ExitNotFound; HTTP 404) | `NotFoundError` |
| `5` (validation family as used by CLI for 400/422) | `ValidationError` |
| `2` (ExitNetwork) | `NetworkError` |
| other nonzero without JSON protocol error | `CommandExecutionError` |

If CLI exit numbering for validation differs at pin time, unit-test against `multica` help/error paths and update this table in the same PR — do not leave OR forks in live asserts.

## 2. Presence matrix (project.description) — MVP live asserts

Initial oracle state: `description = "keep-me"`, title/name = `"base-title"`.

| Case ID | SDK update | CLI argv fragment | Oracle JSON `description` after | Other fields |
|---|---|---|---|---|
| P-OMIT | `ProjectUpdateRequest(name="only-title")` with `description=Unset` | `--title only-title` and no `--description` | `"keep-me"` | title updated |
| P-EMPTY | `description=""` | `--description` `""` | `""` | unrelated fields unchanged |
| P-SET | `description="new"` | `--description new` | `"new"` | unrelated fields unchanged |
| P-NULL-HTTP | oracle `PUT` body `{"description":null}` (not via SDK) | n/a | JSON `null` / DB cleared | documents backend capability only |

Empty **collection** MVP case (not on project model):

| Case ID | Action | Oracle assert |
|---|---|---|
| C-EMPTY | Create issue, attach two labels via SDK, detach both, then `GET /api/issues/{id}/labels` | JSON array length `0` (`[]`) |

## 3. Exception mapping matrix (exactly one class each)

| Stimulus | Expected public exception | Forbidden in message/repr |
|---|---|---|
| Invalid / revoked PAT on SDK call | `AuthenticationError` | raw PAT, JWT |
| Primary-workspace resource fetched via secondary `MulticaClient` (access collapse) | `NotFoundError` | PAT |
| Missing resource id | `NotFoundError` | PAT |
| Invalid field value (e.g. bad status enum) | `ValidationError` | PAT |
| Backend port closed / connection refused | `NetworkError` | full env dump |
| Synthetic nonzero CLI exit `2` without JSON (wrapper executable) | `NetworkError` | PAT, env |
| Synthetic nonzero CLI exit `99` without JSON (wrapper executable) | `CommandExecutionError` | PAT, env |
| Backend killed mid-operation (`destructive`+`serial`) | `NetworkError` | PAT; CLI child process must not remain |

All exception tests also assert operation context is retained where the SDK already exposes it, and that `str(exc)` / diagnostic bundle pass the secret scanner from `contracts/live-test-interface.md` §8.

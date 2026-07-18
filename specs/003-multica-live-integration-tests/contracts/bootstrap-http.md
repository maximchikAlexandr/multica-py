# Bootstrap and oracle HTTP contract

**Version:** 1  
**Pinned upstream:** `multica-ai/multica` tag `v0.3.35` (`4416313f8f7f801df8b7f5072087da8a6502a89c`)  
**Authority:** Multica `CONTRIBUTING.md`, `server/cmd/server/router.go`, `server/cmd/server/health.go`, `docker-compose.selfhost.yml`  
**Rule:** implementers MUST use these paths as written. Discovery-time alternate routes are forbidden for MVP.

## 1. Compose env allowlist (harness-generated)

Harness writes a temporary Compose env file with exactly these keys (no others required for smoke):

| Key | Rule |
|---|---|
| `APP_ENV` | `development` (must not be `production`) |
| `MULTICA_DEV_VERIFICATION_CODE` | `888888` |
| `JWT_SECRET` | 32+ random URL-safe bytes, unique per run |
| `POSTGRES_DB` | `multica` |
| `POSTGRES_USER` | `multica` |
| `POSTGRES_PASSWORD` | 24+ random URL-safe bytes, unique per run |
| `MULTICA_BACKEND_IMAGE` | from compatibility target |
| `MULTICA_IMAGE_TAG` | from compatibility target tag (never `latest` in blocking mode) |
| `BACKEND_PORT` | host port published as `127.0.0.1:<BACKEND_PORT>:8080`; MUST equal the dynamic port in `APP_URL` |
| `APP_URL` | `http://127.0.0.1:<dynamic-port>` (same port as `BACKEND_PORT`) |

Services started: `postgres`, `backend` only. Compose file name: `docker-compose.selfhost.yml`. Ports publish only on `127.0.0.1`. Harness MUST set `BACKEND_PORT` so readiness probes to `APP_URL/readyz` hit the published mapping (upstream default `8080` alone is insufficient when the harness allocates a free port).

## 2. Bootstrap sequence

| Step | Method | Path | Auth | Body | Success | Next value |
|---|---|---|---|---|---|---|
| 1 | `POST` | `/auth/send-code` | none | `{"email":"<run-email>"}` | `2xx` | — |
| 2 | `POST` | `/auth/verify-code` | none | `{"email":"<run-email>","code":"888888"}` | `2xx` JSON with `token` (JWT) | JWT |
| 3 | `POST` | `/api/tokens` | `Authorization: Bearer <JWT>` | `{"name":"multica-py-live-<run-id>","expires_in_days":1}` | `201` JSON with `token` (PAT) | PAT |
| 4 | `POST` | `/api/workspaces` | `Authorization: Bearer <JWT>` only (PAT not used for workspace create) | `{"name":"<name>","slug":"<slug>"}` × 2 | `2xx/201` with workspace `id` | workspace A/B ids |

Run email format: `multica-py-live+<run-id>@localhost`.  
If any bootstrap step fails: setup error (not skip), include redacted status and body excerpt.

## 3. Readiness

| Item | Value |
|---|---|
| Method/path | `GET /readyz` |
| Success predicate | HTTP status `200` AND JSON `status == "ok"` AND `checks.db == "ok"` AND `checks.migrations == "ok"`. Extra keys under `checks` are ignored. Missing `status`/`checks.db`/`checks.migrations` → not ready. |
| Default timeout | `MULTICA_LIVE_READY_TIMEOUT=120` seconds |
| Allowed timeout range | `10`–`600` inclusive; out of range → setup error |
| Poll schedule | `0.5s`, then `1.0s`, then `2.0s` repeated until timeout |
| Jitter | disabled |
| Failure | setup error + last status/body + compose diagnostics |

## 4. Oracle REST routes (raw JSON)

All oracle calls use these headers on every workspace-scoped request:

| Header | Value |
|---|---|
| `Authorization` | `Bearer <PAT>` |
| `Content-Type` | `application/json` |
| `X-Workspace-ID` | workspace UUID (primary or secondary as required by the test) |

Do not use `X-Workspace-Slug` in the oracle for MVP (ID header only). Source: Multica `server/internal/middleware/workspace.go`, `server/internal/cli/client.go`, `e2e/fixtures.ts` @ `v0.3.35`.

| Resource op | Method | Path |
|---|---|---|
| Label create | `POST` | `/api/labels` |
| Label get | `GET` | `/api/labels/{id}` |
| Label list | `GET` | `/api/labels` |
| Label update | `PUT` | `/api/labels/{id}` |
| Label delete | `DELETE` | `/api/labels/{id}` |
| Project create | `POST` | `/api/projects` |
| Project get | `GET` | `/api/projects/{id}` |
| Project update | `PUT` | `/api/projects/{id}` |
| Project delete | `DELETE` | `/api/projects/{id}` |
| Issue create | `POST` | `/api/issues` |
| Issue get | `GET` | `/api/issues/{id}` |
| Issue update | `PUT` | `/api/issues/{id}` |
| Issue delete | `DELETE` | `/api/issues/{id}` |
| Issue list | `GET` | `/api/issues/?limit=<n>&cursor=<c>` (query names as accepted by pinned ListIssues; default smoke uses `limit`) |
| Comment create | `POST` | `/api/issues/{id}/comments` |
| Comment list | `GET` | `/api/issues/{id}/comments` |
| Comment delete | `DELETE` | `/api/comments/{commentId}` |
| Attach label | `POST` | `/api/issues/{id}/labels` |
| Detach label | `DELETE` | `/api/issues/{id}/labels/{labelId}` |
| List issue labels | `GET` | `/api/issues/{id}/labels` |
| Upload file | `POST` | `/api/upload-file` (multipart; fields per upstream handler at pin) |
| Attachment meta | `GET` | `/api/attachments/{id}` |
| Attachment download | `GET` | `/api/attachments/{id}/download` |
| Attachment content | `GET` | `/api/attachments/{id}/content` |
| Attachment delete | `DELETE` | `/api/attachments/{id}` |
| Issue attachments list | `GET` | `/api/issues/{id}/attachments` |

Oracle MUST NOT call SDK resource methods for assert independence.

## 5. CLI profile `config.json` schema (pinned)

Path: `$HOME/.multica/profiles/live-<run-id>/config.json`  
Source: `server/internal/cli/config.go` `CLIConfig` @ `v0.3.35`.

Required JSON keys written by harness:

```json
{
  "server_url": "http://127.0.0.1:<port>",
  "app_url": "http://127.0.0.1:<port>",
  "workspace_id": "<primary-workspace-uuid>",
  "token": "<PAT>"
}
```

Rules:

- Omit `backends` and `profile_command_overrides` in MVP.
- File mode `0600` when the OS supports it.
- Never attach this file to CI artifacts.
- `watched_workspaces` is NOT a CLI config field for this pin; do not invent it.

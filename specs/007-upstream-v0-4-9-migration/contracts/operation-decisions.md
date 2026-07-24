# Contract: Governed Operation Decisions

Exactly these 16 operations are governed. An implementation must encode each
row once in schema v2 and must not infer additional approved operations.

| Operation ID | Outcome | Binding / target destination / required behavior |
| --- | --- | --- |
| `issues.comments.add` | compatible | `issue comment add`; issue ID resolves into path `/api/issues/{id}/comments`, content is JSON body `content`; reject empty inline body before spawn; no file/stdin/attachment expansion |
| `issues.comments.delete` | compatible | `issue comment delete`; comment ID is path `/api/comments/{id}` for DELETE; return `None`; preserve validation/not-found/auth mapping |
| `issues.comments.list` | intentionally_changed | `issue comment list`; issue ID is request path, `since`, `recent`, `thread`, `tail`, `before`, and `before-id` are query-driving CLI inputs; basic unchanged, flat keeps issue/since only, thread/recent use atomic cursor pair, return composite cursor pages |
| `issues.create` | compatible | `issue create`; title/description and existing approved fields enter POST `/api/issues` JSON body; description file/stdin paths are local-control inputs; ordered `label_ids` drive post-create `issue label add` steps and one `issue get` refresh |
| `issues.labels.add` | compatible | `issue label add`; issue ID is path, label ID is POST JSON body; duplicate relation idempotent; malformed refresh output fails closed |
| `issues.labels.list` | compatible | `issue label list`; issue ID is GET path `/api/issues/{id}/labels`; tuple including empty; malformed output fails decode |
| `issues.labels.remove` | compatible | `issue label remove`; issue and label IDs are DELETE path components; absent valid relation idempotent; malformed refresh output fails closed |
| `issues.list` | compatible | `issue list`; existing filters plus sort/direction map to query parameters; direction requires non-position sort; no invented positive range for existing limit |
| `issues.set_status` | compatible | Only `issue status <id> <status>`; issue ID is PUT path `/api/issues/{resolved-id}`, status is JSON body `status`; stale `set-status` metadata removed; no fallback/probe |
| `projects.create` | compatible | `project create`; name maps to JSON body title and description to JSON body description for POST `/api/projects`; non-empty name; empty/None description omitted |
| `projects.resources.add_local_directory` | compatible | `project resource add`; project ID is path; nonblank absolute local path and nonblank daemon ID are required; type is fixed `local_directory`; label is optional and None/blank omits `--ref-label`; path normalization is local control |
| `projects.resources.list` | compatible | `project resource list`; project ID is GET path; JSON list response |
| `projects.resources.remove` | compatible | `project resource remove`; project/resource IDs are scope/path inputs for DELETE; return `None` |
| `projects.resources.update_local_directory` | compatible | `project resource update`; project/resource IDs and nonblank local path are the only public inputs; target CLI performs list-before-PUT and preserves daemon/label; SDK exposes no daemon/label update or clear |
| `projects.set_status` | compatible | Only `project status <id> <status>`; project ID is PUT path and status is JSON body; no fallback/probe |
| `projects.update` | compatible | `project update`; project ID is PUT path, name maps to body title, description to body description; `Unset` omits, empty string clears, `description=None` and all-omitted update reject before spawn |

## Exact Comment Pagination Contract

- `CommentCursor(before, before_id)` requires two non-empty strings.
- Flat request removes obsolete scalar cursor and limit; optional `since`
  remains.
- Thread request accepts optional non-negative limit mapped to `--tail`;
  cursor requires limit.
- Recent request requires positive limit, default 10.
- A cursor emits both flags atomically.
- Only exact target stderr cursor forms for thread or reply are accepted.
- Partial/malformed cursor output is an output-shape error.

## Issue List Contract

- `IssueSort`: `position`, `title`, `created_at`, `start_date`, `due_date`,
  `priority`.
- `SortDirection`: `asc`, `desc`.
- Direction without sort is invalid.
- Direction with `position` is invalid.
- Sort without direction emits only `--sort`.
- Existing optional `None` values remain omitted.

## Presence and Errors

- SDK process timeout remains distinct from target CLI HTTP timeout.
- `timeout=None` means no SDK kill deadline.
- The SDK does not parse `MULTICA_HTTP_TIMEOUT`.
- Exit 2/3/4/5 remain network/auth/not-found/validation.
- Exit 1, including rate limit/conflict/server failures without a stable
  semantic exit, remains `CommandExecutionError`.
- Wrong response shapes never become empty success values or hidden refetches.

## Required Test Authorities

Use rows in `tests/cases/argv_data.py` and the existing generic runners first.
Focused authorities are:

- `tests/unit/resources/test_operations.py`;
- `tests/component/test_cli_roundtrip.py`;
- `tests/contract/test_full_cli_coverage.py`;
- `tests/unit/resources/test_issues.py`;
- `tests/unit/test_project_resource_models.py`;
- `tests/unit/test_path_normalization.py`;
- `tests/unit/test_transport.py`;
- `tests/component/test_process_contract.py`;
- `tests/live/test_issue_workflow.py`;
- `tests/live/test_projects.py`;
- `tests/live/extended/test_pagination.py`.

Every changed constraint requires a valid and invalid case. Optional flag
behavior uses complete expected argv.

## Binding Source Authorities

All refs use commit `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`:

- issue create/list/status/comment declarations, flags, validation, and
  execution: `server/cmd/multica/cmd_issue.go:20-89,219-269,361-519,574-658,1052-1192,1423-1454,1756-1992`;
- issue label list/add/remove:
  `server/cmd/multica/cmd_issue_label.go:16-139`;
- project create/update/status/resource declarations, flags, and execution:
  `server/cmd/multica/cmd_project.go:54-184,304-934`;
- shared timeout and semantic error categories:
  `server/internal/cli/client.go:72-180,258-540` and
  `server/internal/cli/errors.go:1-492`.

Schema-v2 entries split these ranges into the smallest symbol-specific
`SourceRef` records. Do not cite a whole range when the exact Go symbol has a
narrower range already listed in `HANDOFF.md`.

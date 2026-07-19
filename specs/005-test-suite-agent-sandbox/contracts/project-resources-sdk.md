# Contract: Public Project Resources SDK

## Public access

```python
client.projects.resources
```

The existing top-level project collection remains `client.projects`. It constructs one nested `ProjectResourceCollection` in its initializer. Methods take `project_id` explicitly; this is not a per-project handle property in v1.

## Upstream source references (tag v0.3.10)

| SDK method | CLI command | Upstream file | Notes |
|---|---|---|---|
| `list` | `project resource list` | `cmd_project_resource.go` | JSON list output |
| `add_local_directory` | `project resource add` | `cmd_project_resource.go` | `--type local_directory` |
| `update_local_directory` | `project resource update` | `cmd_project_resource.go` | `--local-path` |
| `remove` | `project resource remove` | `cmd_project_resource.go` | text exit |
| issue create/update `--project` | `issue create`, `issue update` | `cmd_issue.go` | optional flag |

Full upstream commit MUST match `contracts/multica-live-target.toml` resolved commit for tag `v0.3.10`.

## Methods

### list

```python
client.projects.resources.list(project_id: str) -> tuple[ProjectResourceRecord, ...]
```

CLI argv:

```text
project resource list <project_id>
```

### add_local_directory

```python
client.projects.resources.add_local_directory(
    project_id: str,
    request: ProjectResourceAddLocalDirectoryRequest,
) -> ProjectResourceRecord
```

Required argv order:

```text
project resource add <project_id>
--type local_directory
--local-path <resolved-absolute-path>
--daemon-id <daemon_id>
```

When `label is not None`, append:

```text
--ref-label <label>
```

### update_local_directory

```python
client.projects.resources.update_local_directory(
    project_id: str,
    resource_id: str,
    request: ProjectResourceUpdateLocalDirectoryRequest,
) -> ProjectResourceRecord
```

CLI argv:

```text
project resource update <project_id> <resource_id>
--local-path <resolved-absolute-path>
```

### remove

```python
client.projects.resources.remove(project_id: str, resource_id: str) -> None
```

CLI argv:

```text
project resource remove <project_id> <resource_id>
```

## Issue project association

`IssueCreateRequest.project_id` and `IssueUpdateRequest.project_id` are optional strings.

When present, argv appends:

```text
--project <project_id>
```

The flag is emitted once. Empty string is invalid at model construction.

## Error behavior

All methods use existing `CliTransport` and existing exception mapping. No project-resource-specific exception hierarchy is introduced.

## Required tests

- exact argv for all four methods;
- optional label omitted/present;
- response decoding to local-directory reference;
- malformed response uses existing decode exception;
- non-zero CLI exit uses existing command exception;
- issue create/update project flag;
- public surface/export checks.

# CLI Coverage

Pinned upstream: `multica-ai/multica@48b8dbf43971e5ea974bf827220cd212a1240c72`

## Coverage Matrix

See `specs/001-full-cli-sdk/contracts/cli-coverage.md` for the full 108-row manifest-backed matrix with command-level source locations, output modes, aliases, and unsupported rows.

## Summary

| Resource | Commands | Status |
|----------|----------|--------|
| auth | status, login, logout | ✅ (`login(token)` is text-backed, `login()` is process-backed) |
| setup | cloud, self-host | ✅ |
| daemon | status, start, stop, restart, logs, disk-usage | ✅ |
| workspaces | list, get, members, switch, watch, unwatch | ✅ |
| issues | list, get, pull-requests, children, create, update, assign, set-status, reorder, search, runs, run-messages, usage, rerun, cancel-task | ✅ |
| issues.comments | list, add, reply, delete, resolve, unresolve | ✅ |
| issues.metadata | list, get, set, delete | ✅ |
| issues.subscribers | list, add, remove | ✅ |
| issues.labels | list, add, remove | ✅ |
| projects | list, get, create, update, delete, set-status | ✅ |
| labels | list, get, create, update, delete | ✅ |
| agents | list, get, create, update, archive, restore, tasks, avatar | ✅ |
| agents.skills | list, set | ✅ |
| skills | list, get, create, update, delete, import | ✅ |
| skills.files | list, upsert, delete | ✅ |
| autopilots | list, get, create, update, delete, run, history, get-run | ✅ |
| autopilots.triggers | list, create, delete | ✅ |
| repos | list, get, checkout | ✅ |
| runtimes | list, get | ✅ |
| attachments | list, upload, download | ✅ |
| config | show, get, set | ✅ |
| squads | list, get | ✅ |
| users | list, get | ✅ |
| maintenance | version, update | ✅ |

Total: 108 manifest command rows, with 107 supported SDK rows and 1 explicit unsupported/deprecated upstream row.

# CLI Coverage

Pinned upstream: `multica-ai/multica@48b8dbf43971e5ea974bf827220cd212a1240c72`

## Coverage Matrix

See `specs/001-full-cli-sdk/contracts/cli-coverage.md` for the full 108-row manifest-backed matrix with command-level source locations, output modes, aliases, and unsupported rows.

## Coverage Levels

| Level        | Meaning |
|--------------|---------|
| `typed`      | SDK method with input/output contract, source provenance, and tests. |
| `raw`        | Sequence-of-arguments access; never shell-interpolated; reported separately from typed. |
| `process`    | Long-running foreground/streaming process handled via process abstraction. |
| `unsupported`| Explicitly not supported by the SDK with a `reason`. |
| `legacy`     | Legacy alias retained with a `reason`. |
| `incomplete` | Required fields missing or pending maintainer decision; never satisfies the gate. |

Raw coverage is reported separately from typed coverage and never implies
stable typed public support. Incomplete rows are surfaced as
`coverage_level=incomplete` and the gate emits a `COVERAGE_INCOMPLETE`
failure. The gate never passes while any row is `incomplete`.

## Generated Facts vs Maintainer Decisions

The `prepare-upgrade` and `apply-manifest-suggestions` commands produce
incomplete manifest suggestions, test suggestions, implementation
tasks, and a changelog fragment. These are *generated facts*. They
never pass the coverage gate and are never auto-applied. The maintainer
must explicitly mark them complete in the approved SDK contract
(`contracts/sdk-contract.json`).

The approved SDK contract is the only valid production generator
input. Source evidence, candidate diffs, and generated upgrade bundles
are never generator input.

## Checked-in Artifact Locations

| Artifact | Required path |
|---|---|
| Upstream state | `src/multica_py/_generated/upstream_state.json` |
| Coverage manifest | `src/multica_py/_generated/upstream_coverage.json` |
| Supported contract | `src/multica_py/_generated/upstream_supported_contract.json` |
| Approved SDK contract | `contracts/sdk-contract.json` |
| Generated report | explicit `--output PATH` only |
| Upgrade bundle | `artifacts/upstream-upgrades/<from>..<to>/` |

## Generated Artifact Boundaries

- Source evidence and candidate diffs are never committed as SDK
  behavior; they may be committed as review artifacts.
- Upgrade bundles are never committed as SDK behavior; they may be
  committed as review artifacts.
- The supported contract, state file, and coverage manifest are the
  only checked-in artifacts that drive the offline gate.

## Summary

| Resource | Commands | Status |
|----------|----------|--------|
| auth | status, login, logout | ✅ (`login(token)` is text-backed, `login()` is process-backed) |
| setup | cloud, self-host | ✅ |
| daemon | status, start, stop, restart, logs, disk-usage | ✅ |
| workspaces | list, get, members, switch, watch, unwatch | ✅ |
| issues | list, get, pull-requests, children, create, update, assign, set-status, reorder, search, runs, run-messages, usage, rerun, cancel-task | ✅ (`create`/`update` optional `--project`) |
| issues.comments | list, add, delete, resolve, unresolve | ✅ (`reply` maps to `add --parent`) |
| issues.metadata | list, get, set, delete | ✅ |
| issues.subscribers | list, add, remove | ✅ |
| issues.labels | list, add, remove | ✅ |
| projects | list, get, create, update, delete, set-status | ✅ |
| projects.resources | list, add, update, remove (`local_directory`) | ✅ |
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

Total: 112 manifest command rows, with 111 supported SDK rows and 1 explicit unsupported/deprecated upstream row.

Collector subprocesses run with an allowlisted environment only; `observe` and
network-backed collection may still reach release hosts, so treat untrusted
binaries and release URLs as out-of-scope for full network isolation in 002.

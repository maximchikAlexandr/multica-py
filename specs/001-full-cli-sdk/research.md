# Research and Architecture Decisions

## R-001 — Pin upstream source

**Decision:** Baseline the SDK on `multica-ai/multica@48b8dbf43971e5ea974bf827220cd212a1240c72`.

**Rationale:** The current command tree includes sub-issue stages and comment resolve/unresolve behavior relevant to automation. Pinning prevents implementation drift while the SDK is built.

**Alternatives considered:** Track `main` continuously. Rejected because command and JSON contracts could change during implementation.

## R-002 — Source authority

**Decision:** Cobra declarations and Go implementations under `server/cmd/multica`, plus request/response structs under `server/internal/cli`, are authoritative. `CLI_AND_DAEMON.md` is explanatory only.

**Rationale:** Documentation omits some registered commands and can lag implementation.

## R-003 — Resource-oriented public API

**Decision:** One `MulticaClient`, resource classes as stateless procedure namespaces, frozen msgspec models as returned values.

**Rationale:** Mirrors the CLI hierarchy while keeping subprocess side effects explicit.

**Rejected:** Active Record models (`issue.save()`), a single giant client, and free functions.

## R-004 — Sync-only v1

**Decision:** Provide only synchronous resource methods and process handles.

**Rationale:** Subprocess lifecycle and cancellation are already complex. FastAPI/Temporal workers can isolate synchronous Activities. A second async transport would double surface and testing burden.

## R-005 — No guessed error classification

**Decision:** Use exact domain exceptions only where source or structured output supports them; otherwise raise `CommandExecutionError` with raw diagnostics.

**Rationale:** Parsing localized human error strings is brittle and violates the exactness requirement.

## R-006 — msgspec model policy

**Decision:** Frozen, keyword-only `msgspec.Struct`; additive unknown fields ignored; required field drift fails.

**Rationale:** Supports fast strict decoding and forward-compatible additive changes without `Any`.

## R-007 — uv tool positioning

**Decision:** The package remains a library, while the installed `multica-py` tool is a doctor/coverage utility, not a complete reimplementation of the upstream CLI.

**Rationale:** `uv tool install` needs an entry point, but duplicating Multica's command syntax would create another compatibility burden.

## R-008 — Build system

**Decision:** Hatchling backend, managed and invoked by uv.

**Rationale:** Small source-layout package, standards-compliant wheel/sdist, no runtime build dependency.

## R-009 — Python support

**Decision:** Python 3.12 and 3.13 for v1.

**Rationale:** Enables modern typing and `StrEnum`, reduces compatibility complexity, and is appropriate for a new package.

## R-010 — Platform support

**Decision:** Linux and macOS supported/tested for v1. Windows is not promised.

**Rationale:** Correct process-group termination and daemon lifecycle need native Windows design and CI; pretending support would weaken reliability.

## R-011 — Upstream drift detection

**Decision:** Maintain a machine-readable command manifest generated from the pinned source and a scheduled audit workflow that reports, but does not automatically adopt, upstream drift.

**Rationale:** Upstream is active; explicit review is safer than hidden model changes.

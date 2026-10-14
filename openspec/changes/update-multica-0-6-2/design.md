## Context

The repository currently approves Multica `0.6.1` at source commit `2ea01ae4ef55de4310b99af192d2dbd367832883`, renders a single generated runtime module from `contracts/sdk-contract.json`, and accepts CLI versions in the reviewed direct-patch interval. Multica `0.6.2` is the next stable release at `7ab92d7622ecd81d179a8d83ae2dea74835a5069`. The reviewed delta contains four new CLI nodes under `daemon autostart`, no removals, changes to property list types, and response/behavior changes across daemon status, wakeups, upload failures, search, project updates, and HTTP error text.

The upstream dossier establishes 209 target CLI nodes and 196 supported response entrypoints. Evidence and generated suggestions remain review-only; the approved contract remains the sole production generator input. Graph revision 2 follows independent rejection of candidate `adc56e3cb9a7c057f5b71efa1e120a073941df77`: it accepted `value=("not-a-url",)` because neither public tuple boundary carried the property type needed for URL-specific pre-I/O validation. The candidate is diagnostic evidence only, is not an approved implementation baseline, and SHALL NOT be merged. This planning change edits no production code, tests, or main specs.

## Goals / Non-Goals

**Goals:**

- Define a direct `0.6.1` to `0.6.2` compatibility strategy with exact source, release, archive, executable, and version provenance.
- Specify complete command and response reconciliation, typed adaptations, deterministic generation, table-driven tests, documentation, packaging, and release checks.
- Preserve backward decoding for legacy omissions while exposing new target fields without fabricated fallbacks.
- Keep every changed behavior on the existing resource/model/transport/generator paths.

**Non-Goals:**

- Exposing `daemon autostart enable|disable|status` in the Python SDK.
- Promoting extractor suggestions, collector files, audit JSON, binaries, or transient renders into Git.
- Adding another generator, runtime registry, validation framework, or dependency.
- Supporting intermediate release stages; the only compatibility comparison is `0.6.1` to `0.6.2`.

## Decisions

### 1. Advance one approved contract and one generated projection

Update the existing contract target to `0.6.2`, retain the repository minimum CLI version and existing operation-level gates, set `0.6.2` as maximum tested, and set `0.6.3` as the exclusive next-patch ceiling. Every changed contract row will cite full `0.6.1` and `0.6.2` source commits and tests. Existing validate/render/check commands remain the only promotion path.

Alternative considered: generate directly from the collected target evidence. Rejected because evidence does not approve public names, mappings, presence semantics, validators, or compatibility policy.

### 2. Require an explicit discriminator for list-property input

Keep `PropertyDefinition.type` open as `str`, add `multi_text` and `multi_url` to documented accepted definitions, and extend property value typing to immutable `tuple[str, ...]` only for these list types. Add the same keyword-only `property_type: Literal["multi_text", "multi_url"] | None = None` discriminator to `IssuePropertyResource.set[_command]` and `IssuePropertyAssignment`. A string or string sequence intended as a list property requires the discriminator. Omitting it preserves the existing scalar-string contract; passing it with a scalar non-string or with any other type name fails before I/O.

One shared list-value normalizer parses a discriminated string using the target grammar (JSON array when it begins with `[`, otherwise comma form), accepts a discriminated Python sequence, validates before command construction, applies stable first-occurrence de-duplication, and emits one compact JSON array. `multi_text` requires 1–20 nonblank strings of at most 2000 characters. `multi_url` requires 1–20 HTTP(S) URL strings of at most 2048 characters. `None` is rejected; unset remains the separate unset operation. Exact-element filtering keeps one list element as one predicate token, and display values remain literal strings without actor resolution.

Alternatives considered: infer property type with a server read, apply URL rules to every tuple, add tagged wrapper classes, or widen the global `MetadataValue` alias. Server lookup violates pre-I/O validation; tuple-wide URL rules reject valid text; wrappers add avoidable public concepts; widening metadata changes an unrelated API. The discriminator reuses the existing property type vocabulary and one shared validation path.

### 3. Add target fields with explicit legacy semantics

Add `DaemonStatus.cli_commit: str | None = None`. A target full SHA remains exact, an explicit empty string remains empty/unknown, and a missing legacy field decodes to `None`; no value is synthesized from `cli_version`.

Add `IssueWakeup.last_error: str | None = None`. Create/get/list/update/disable use the same decoder. The three recoverable pull-request condition diagnostics remain visible while pending and decode to `None` after recovery clears the upstream field.

Alternative considered: normalize empty and absent daemon commits to the version string, or drop wakeup diagnostics. Rejected because both erase source-significant states.

### 4. Preserve retained public methods and tighten their behavior at existing boundaries

The upload path maps an interrupted response-body read to `NetworkError` through the current transport classifier. Issue search retains its method/signature and adds regression coverage for digit-prefixed keys and cancellation. Project update retains `Unset` omission versus explicit `None` clearing and carries the existing revision/concurrency control. Redacted HTTP 500 responses preserve the stable typed exception without asserting backend raw text.

Alternative considered: add version-specific methods or wrappers. Rejected because the commands and public operations are retained; only their reviewed target semantics changed.

### 5. Defer daemon autostart as one indivisible local-control family

The approved inventory records all three new nodes and their source semantics, but marks them deferred with no public symbol, binding, model, docs example, or generated method. Enable/disable modify per-user OS login registration and refuse unmanaged entries; status exposes local mechanism/location/command details. A separate human-approved change is required to define platform support and safety.

Alternative considered: expose read-only status now. Rejected because splitting the family would create an incomplete local-control policy and still require OS-specific guarantees.

### 6. Ponytail full gate

No new subsystem is necessary. The existing approved contract, deterministic generator, frozen models, resource adapters, shared transport exceptions, frozen case tables, and repository verification commands cover every required change. For the confirmed ambiguity, the existing public keyword/model field plus one shared normalizer is sufficient; tagged value wrappers, property-definition lookups, parallel parsers, registries, and new test frameworks are removed from scope.

### 7. E2E decision

`e2e_required=false`. The affected outputs are structured JSON decoded behind the Python SDK, and every externally observable change can be proven by deterministic contract validation, table-driven argv/decoder/error tests, fake-CLI component tests, packaging checks, and the existing separately gated live smoke. No changed human-facing table, log, progress display, browser UI, real multi-process lifecycle, or environment-only interaction leaves a verification gap. Therefore no local E2E script, independent live stand, or before/after PNG is required; the delivery plan maps every scenario to lower-level or existing gated coverage.

## Risks / Trade-offs

- **Wide upstream source diff can hide SDK-relevant behavior** → Reconcile every target CLI node and supported response entrypoint, retain full-SHA source links, and fail closed on unresolved mappings.
- **List-property parsing can conflate commas, brackets, and literal values** → Canonicalize SDK sequences as JSON arrays and test both accepted CLI forms plus ambiguous/invalid inputs.
- **Callers can omit the discriminator for a string whose remote property is list-valued** → Treat that call as the unchanged legacy scalar/raw string contract; only discriminated input receives SDK list parsing and validation, and documentation makes this boundary explicit.
- **Open property types reduce static exhaustiveness** → Preserve forward-compatible `str` definitions while applying type-specific decoding only to the two reviewed list types.
- **Legacy fixtures omit new fields** → Use explicit optional defaults and test missing, empty, null, and populated states separately.
- **Backend error wording may drift** → Assert typed/redacted classification and stable safe detail, never raw server messages.
- **Deferred autostart leaves a CLI capability without SDK coverage** → Record the defer decision and all nodes in the inventory so omission is intentional and auditable.

## Migration Plan

1. Update the approved contract provenance, compatibility metadata, inventory, mappings, schemas, response catalog, and source/test references.
2. Run contract validation, render the committed runtime projection, and prove check-mode freshness from the approved contract alone.
3. Extend existing public models, decoders, validators, resource adapters, and transport classification; add the same optional discriminator to direct set and create-time assignment and route both through one normalizer.
4. Add table rows and focused regressions, then run all repository offline, typing, lint, contract, documentation, packaging, and collect-only gates.
5. Update user documentation for the direct `0.6.1` to `0.6.2` migration and deferred autostart family.
6. Roll back as one commit range: contract, generated projection, models/adapters, tests, and docs revert together to the reviewed `0.6.1` ceiling.

## Open Questions

None. The list-property input discriminator and daemon-autostart deferral are explicit rather than left for implementation judgment.

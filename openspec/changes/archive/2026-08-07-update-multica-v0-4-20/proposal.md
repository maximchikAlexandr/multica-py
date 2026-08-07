## Why

The approved SDK contract is pinned to Multica `v0.4.9`, so it neither certifies
the current `v0.4.20` CLI nor exposes compatibility changes that affect runtime
deletion, agent copying, issue search results, and actionable CLI failures. The
`v0.4.20` release is now the required baseline, and the SDK needs a reviewed,
source-traced delta rather than accepting all changes from upstream `main`.

## What Changes

- Move the reviewed upstream target from Multica `v0.4.9` to tagged release
  `v0.4.20` (`93342d04a7a9f788fec921e5aa736f86c7f22d8f`) and regenerate the
  approved runtime compatibility projection for `[0.4.20, 0.4.21)`.
- Reconcile every retained approved operation against the pinned source and
  verified release binary, adding reviewed contract coverage for `agent copy`
  and the changed `issue search` response while excluding unreleased commands.
- Document and test `runtimes.delete(..., cascade=True)` as unbinding dependent
  agents, cancelling their active work, and deleting the runtime while
  preserving agent configuration, chats, and task history.
- Add `agents.copy()` and `agents.copy_command()` with same-runtime copying,
  cross-runtime targeting, portable overrides, invocation-permission controls,
  optional skill omission, and command preview. For cross-runtime copies, an
  omitted model is represented by `--model ""` under the settled upstream
  policy, while omitted thinking-level and service-tier values remain absent.
  Secret and machine-local configuration is never copied or implicitly supplied
  by the SDK operation.
- Preserve the existing tuple-returning `issues.search(query)` API while
  decoding the `v0.4.20` result envelope and exposing optional, open-string
  `IssueSummary.match_source` values. Responses that omit the field remain
  valid.
- Map HTTP/CLI `409` failures to `ConflictError` and preserve actionable,
  redacted upstream detail in `str(exc)` and exception diagnostics. Apply the
  same detail-preservation rule to known validation failures mapped to
  `ValidationError`.
- Keep upstream-owned runtime, provider, model, thinking-level, and service-tier
  values forward-compatible as strings rather than introducing closed enums.
- Retain and revalidate the already-correct public
  `autopilots.trigger()` / `autopilot trigger` mapping on current `main`; do not
  restore the legacy `autopilots.run()` surface.
- Update API, compatibility, migration, and maintainer documentation plus
  table-driven unit, contract, component, and command-preview coverage.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `sdk-surface`: add agent copy, extend issue-search decoding, define runtime
  cascade semantics, and retain open upstream-owned string values.
- `subprocess-transport`: classify conflicts and preserve redacted actionable
  conflict/validation details in typed exceptions.
- `upstream-contract`: promote `v0.4.20` as the pinned authority, govern the new
  and changed operations, and require full source/binary reconciliation.
- `autopilot-resource`: revalidate the existing trigger mapping against
  `v0.4.20` and keep the legacy run spelling absent.
- `verification-and-release`: cover the new method, changed response and error
  contracts, compatibility interval, docs, and focused/full offline gates.

## Impact

- Approved/generated contract: `contracts/sdk-contract.json`, generated runtime
  projection, compatibility reports/docs, provenance fixtures, and contract
  validator/render/check workflows.
- Public SDK: `AgentResource`, `IssueSummary`, issue-search wire adaptation,
  runtime deletion documentation, and existing exception classes; no existing
  eager method or return type is removed.
- Transport: failure classification and construction of redacted exception
  messages and attributes, including redacted argv, without changing subprocess
  execution, command-plan, or secret redaction boundaries. The actual argv is
  supplied only to the executed subprocess invocation.
- Tests/docs: table-driven operation inventory, source-contract and model
  decoding tests, transport/component failure cases, compatibility policy,
  API/migration/service documentation, and live-smoke inventory where
  applicable.
- External authority: tagged Multica `v0.4.20` source and verified release
  assets only; later upstream `main` behavior and UI-only changes remain out of
  scope.

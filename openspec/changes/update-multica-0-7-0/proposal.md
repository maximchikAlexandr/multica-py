## Why

WP-04 exposed a mismatch between the approved plan and pinned Multica `0.7.0`
CLI source: runtime visibility, sharing, and atomic revocation exist only as
server HTTP behavior, while `multica runtime update` changes only the CLI
version. The remaining plan must stay CLI-backed, preserve accepted WP-01/02/03
commits, and remove the unsupported write contract without rewriting history.

## What Changes

- Preserve immutable composition `1f8083040d862669e65b875e7bc9555de96a7346`
  and accepted/integrated WP-01, WP-02, and WP-03 results. Publish this planning
  correction on a separate normal ref descended from accepted integration SHA
  `9b5d112830831f9e727b35f4936f923ec9429cc7`.
- Correct runtime response classification: `visibility` and `shared_with` are
  reviewed read-only fields of runtime-definition responses such as list and
  rename; `runtimes.update` remains the target-version update result and SHALL
  not claim those fields.
- Explicitly classify runtime visibility/share/revoke HTTP writes as
  `not_sdk_surface` because the pinned CLI has no corresponding command or flag.
  Do not add an HTTP bypass and do not treat destructive delete/cascade as a
  privacy-revocation substitute.
- Retain CLI-backed agent create/update authorization failures and workspace
  allowlist failures through the existing sanitized exception boundary.
- Replace the unstarted WP-04/WP-05 graph remainder with one all-covering
  remaining package. Reuse existing child MYL-576 after approval; do not create
  duplicate children or reuse prior ACCEPT markers under the new revision.
- Keep `e2e_required=false`: all revised behavior is closed by source-link,
  contract, fake-CLI, unit/resource/component, package, and ordinary CI checks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: preserve the immutable historical composition while
  making the new planning revision and corrected CLI/source mapping authoritative.
- `sdk-surface`: expose only CLI-backed runtime reads and typed failures, with
  explicit exclusions for runtime access-management writes.
- `public-cli-parity`: require response-shape decisions to match the actual CLI
  operation rather than a related server endpoint.
- `verification-and-release`: migrate accepted and remaining work safely to one
  revised graph revision and update OpenSpec-preservation assertions.

## Impact

- Accepted commits remain immutable: WP-01/integration
  `b189631ad2cbc33e9ecfd5cd616052400e8f89aa`, WP-03
  `c24d6ac48b0a0cedfca59a54ed6e6f0e2d5a8fd1`, WP-02
  `ddeb824b16359dce86bc1ed6fbe3b327166dbf76`, and current integration
  `9b5d112830831f9e727b35f4936f923ec9429cc7`.
- The approved contract, generated projection, runtime models/resources,
  agent/workspace error fixtures, shared docs, packaging, and CI assertions are
  affected by the remaining corrective package.
- Existing PR #101, its branch, old planning ref, WP refs, accepted commits,
  implementation children, and immutable composition parents are preserved.
- No direct HTTP transport, new public runtime access-management method,
  dependency, persistence layer, live stand, image flow, force-push, reset, or
  history rewrite is introduced.

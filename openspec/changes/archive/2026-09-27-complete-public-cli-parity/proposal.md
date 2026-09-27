## Why

The SDK's approved-operation subset is not equivalent to the public Multica
CLI at the pinned `v0.5.3` target: supported methods contain transport and
response mismatches, public command families and behavior-affecting inputs are
missing, and emitted fields are discarded. GitHub issue #93 supersedes prior
deferrals and requires a source- and help-reconciled parity contract before
implementation can be considered complete.

Review of the integrated implementation at
`c9429d82500a961fa2bac238ff6611da7dd33ef9` found that the inventory still
certifies 136 public domain command leaves as generic raw transport and that an
approved `AutopilotResource.trigger_list` entry has no public implementation.
This revision closes those planning ambiguities without weakening the original
parity boundary.

## What Changes

- Establish a complete inventory of every public runnable CLI leaf, positional
  input, inherited or leaf flag, output/transport variant, nested response
  field, mutation acknowledgement, and error behavior at
  `multica-ai/multica@ff8b285497809e084915016c40c2bc5e5991ffbc`.
- Require every inventory row to have one evidence-backed disposition:
  `typed`, `typed-equivalent`, `transport`, `presentation-only`, or
  `outside-public-scope`; public `partial`, `unknown`, deferred, and unreviewed
  rows block completion.
- Fix advertised contracts that currently pass unsupported `--output` flags,
  use incorrect positional arguments, parse the wrong cursor syntax, or decode
  incompatible daemon, comment, attachment, and project-resource payloads.
- Add typed coverage for missing public operations, including repository
  checkout, agent environment and additive skills, workspace and squad
  mutations, issue timeline and wakeups, chat reads, autopilot trigger URL
  rotation, and runtime profiles.
- Extend existing operations with all behavior-affecting CLI inputs and
  presence semantics, while using one safe content/file/stdin abstraction and
  one typed daemon configuration instead of duplicating CLI spellings.
- Preserve all public CLI-emitted response variants and nested fields with
  explicit absence, nullability, redaction, secret opt-in, and lifecycle
  semantics.
- Extend the reviewed approved contract and deterministic tooling so source
  evidence remains review-only, dynamic registrations and aliased flags are
  reconciled, and CI fails on unclassified public drift.
- Add offline, source-linked public-operation regression coverage and update
  API, coverage, compatibility, migration, and release documentation.
- Reclassify every public command leaf against the actual SDK surface: a domain
  leaf MUST resolve to a typed or proven typed-equivalent public operation;
  `transport` is reserved for genuinely process-, terminal-, text-, or
  byte-oriented leaves whose public contract is the controlled transport
  abstraction itself. Generic `client.cli.command_command(...)` is never a
  parity disposition.
- Implement the already approved `AutopilotResource.trigger_list` and
  `trigger_list_command` surface, with an exact canonical vector and strict
  symbol/discovery equality; removing or deferring this entry is not approved.
- Preserve all remaining round-one review findings as required remediation on
  the existing implementation parent and draft PR before release readiness.
- **BREAKING**: correct public return types and models where the existing SDK
  promises shapes the pinned CLI cannot emit; retain compatibility only where
  it does not perpetuate a false transport or data contract.

## Capabilities

### New Capabilities

- `public-cli-parity`: Defines the complete public-CLI inventory boundary,
  allowed dispositions, parity dimensions, exclusion evidence, and the
  no-unknown completion gate.

### Modified Capabilities

- `upstream-contract`: Expands the approved contract from a selected operation
  subset to reviewed coverage of every public CLI leaf, input, output, field,
  transport, and dynamic/aliased registration at the pinned target.
- `sdk-surface`: Requires typed or proven equivalent SDK surfaces for every
  public domain capability, including the formerly deferred chat, wakeup, and
  runtime-profile families, with complete input and response contracts.
- `subprocess-transport`: Defines truthful JSON, text, bytes, streaming,
  foreground, and interactive execution instead of appending unsupported
  output flags or fabricating JSON responses.
- `verification-and-release`: Adds closed inventory, source-linked fixture,
  argv, shape, redaction, generated-freshness, documentation, and packaging
  gates for full public parity.

## Impact

- `contracts/sdk-contract.json`, its schema/validation/rendering code, and the
  generated approved runtime projection become complete public-CLI parity
  authorities rather than approved-subset authorities.
- Public resources, entities, models, exports, decoders, command builders, and
  bound relations under `src/multica_py/` change across most resource families.
- Existing table-driven unit, contract, component, packaging, and gated live
  tests expand; destructive daemon/auth lifecycle behavior remains verified by
  source evidence and safe process fixtures rather than a developer machine.
- Documentation must distinguish API coverage, transport coverage,
  presentation equivalence, test coverage, and version compatibility.
- No new runtime dependency, workflow engine, generic resource framework, Go
  interpreter, checkout-registry clone, server-only capability, or direct
  generation from unreviewed evidence is introduced.

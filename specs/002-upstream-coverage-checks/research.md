# Research: Versioned Upstream CLI Contract and SDK Upgrade Workflow

## Decision: Split Supported, Observed, and Candidate Upstream State

The repository should distinguish supported baseline, latest observed upstream
release, and candidate baseline under review.

**Rationale**: Supported state drives blocking offline CI. Observed state is an
informational signal that a newer upstream release exists. Candidate state is a
reviewable contract and impact map prepared for promotion. Keeping one
baseline field for all three states would either make CI chase latest upstream
or hide release lag.

**Alternatives considered**:

- Single baseline field: rejected because it conflates support, observation,
  and review.
- Automatically promote latest release: rejected because public SDK semantics
  require maintainer decisions.
- Manual-only release discovery: rejected because frequent upstream releases
  create avoidable operational work.

## Decision: Store Version, Tag, Full Commit, Provenance, and Semantic Hash

Every checked-in contract artifact should carry schema version, release
version, tag when available, full source commit, generator identity, collection
method, semantic hash, and reproducibility metadata.

**Rationale**: Version is useful for humans, but full commit is required for
source URLs and reproducibility. Semantic hash lets maintainers distinguish a
provenance-only release from an actual CLI contract change.

**Alternatives considered**:

- Store only release version: rejected because source identity would be
  ambiguous.
- Store only full commit: rejected because reports become harder to match to
  installed CLI releases.
- Include `generated_at` in semantic hash: rejected because timestamp-only
  changes would create noisy diffs.

## Decision: Move from Command Name Inventory to Semantic CLI Contract

The upstream inventory should be a versioned semantic contract rather than a
list of command strings.

**Rationale**: The SDK can break when an existing command changes arguments,
flags, defaults, inherited options, deprecation state, execution mode, output
shape, or exit behavior. Name-only inventory cannot detect these changes.

**Alternatives considered**:

- Keep command-name set diff: rejected because it misses breaking changes to
  existing commands.
- Parse help text only: rejected because help is human-oriented and can omit
  hidden/deprecated or inherited details.
- Generate public SDK changes directly from inventory: rejected because source
  behavior and API mapping require approval.

## Decision: Use Binary and Source Evidence with Trust Levels

The workflow should support binary, source, verified, and degraded trust levels.
Binary collection observes the release executable. Source extraction provides
declarative Cobra facts and source provenance. Verified contracts require the
sources to agree.

**Rationale**: Binary behavior proves what users install, while source evidence
helps identify hidden/deprecated commands and source locations. Either source
alone can be incomplete or stale.

**Alternatives considered**:

- Binary-only collection: rejected because human help parsing may miss
  structural metadata.
- Source-only collection: rejected because it does not prove the release binary
  matches the source tree.
- Full Go static analyzer: rejected as too broad and fragile for this feature.

## Decision: Limit Source Automation to Declarative Evidence

Source extraction should only collect facts from versioned, reviewable patterns
such as Cobra command literals, `AddCommand`, known flag registration calls,
known argument validators, and declarative flag constraints. Unknown patterns
produce review items.

**Rationale**: Public SDK semantics often require data-flow, control-flow, and
server behavior understanding. Automating those in a source extractor would
create a brittle static analyzer. Evidence should reduce search space, not
approve SDK behavior.

**Alternatives considered**:

- Infer API field mapping automatically: rejected because helpers, resolvers,
  preparatory requests, and patch semantics require review.
- Infer omitted/null/empty behavior automatically: rejected because identical
  syntax can mean different business behavior.
- Infer enum policy automatically: rejected because public enum strictness and
  future-value behavior are SDK decisions.

## Decision: Diff Supported Contract Against Candidate Contract

The coverage workflow should first produce an upstream semantic diff, then map
that diff to SDK operations and coverage decisions.

**Rationale**: Maintainers need to know what changed upstream before deciding
how SDK coverage should change. A candidate with the same semantic hash may be
compatible even when provenance changed. A candidate with a required argument
change is breaking even if command names are unchanged.

**Alternatives considered**:

- Compare candidate inventory directly to SDK manifest: rejected because it
  hides the upstream cause of gaps.
- Treat all absent manifest rows as hard failures: rejected because legacy
  rows and aliases need explicit compatibility decisions.
- Auto-confirm renames: rejected because rename heuristics are suggestions, not
  safe identity changes.

## Decision: Introduce Coverage Levels and Stable Operation IDs

SDK coverage should distinguish typed, raw, process, unsupported, legacy, and
incomplete coverage. Stable operation IDs should own SDK semantics, while
versioned bindings connect operations to upstream command paths.

**Rationale**: A `sdk_method` string alone does not prove typed support. It
does not identify input mapping, output contract, tests, version interval, or
intentional sharing. Operation IDs preserve SDK identity across upstream
renames and avoid false duplicate-ownership failures for aliases.

**Alternatives considered**:

- Keep command path as identity: rejected because command spelling changes are
  common during CLI evolution.
- Treat duplicate SDK methods as always invalid: rejected because aliases and
  shared implementations may be legitimate.
- Count raw access as typed support: rejected because raw/process access has a
  weaker user contract.

## Decision: Make Machine Report the Source of Human Output

Maintainer commands should return a versioned machine-readable report. Human
output and GitHub summaries should render that same model.

**Rationale**: Automation should not parse console text, and human and machine
outputs must not diverge. Exit codes should distinguish compatibility gaps,
invalid artifacts, collector failure, source/binary mismatch, unresolved
breaking candidate, and invalid command usage.

**Alternatives considered**:

- Text-only output: rejected because GitHub Actions and future tools need
  structured status.
- Separate human and JSON logic: rejected because it creates drift.
- Return success on missing executable: rejected as fail-open behavior in
  collection mode.

## Decision: Separate Offline Blocking CI from Networked Observer

Ordinary PR/push CI should validate checked-in artifacts only. A scheduled or
manual observer may use the network to detect upstream releases and prepare
candidate artifacts, but must never promote supported state.

**Rationale**: This preserves offline reproducibility while still surfacing
frequent upstream releases.

**Alternatives considered**:

- Download latest upstream CLI in every PR: rejected because it makes CI
  unstable and network-dependent.
- Never automate release observation: rejected because release lag becomes
  invisible until a maintainer checks manually.

## Decision: Secure Collector Execution and Supply-Chain Provenance

Network-based collection must verify official checksums and execute selected
binaries in a sanitized environment without repository secrets or user
configuration.

**Rationale**: Observer automation downloads and runs external binaries. Even
official assets should not run with repository credentials or real profiles.
Isolation also improves determinism.

**Alternatives considered**:

- Run the binary directly on the maintainer's normal environment: rejected
  because it can read local config and credentials.
- Skip checksum validation for official releases: rejected because supply-chain
  provenance is part of the feature.

## Decision: Generate Upgrade Bundle, Not Only Manifest Stubs

Upgrade preparation should generate summary, diff, impact map, candidate
contract, incomplete manifest suggestions, test suggestions, task suggestions,
and a changelog fragment.

**Rationale**: A bare manifest row saves little work. The maintainer needs
affected operations, severity, source evidence, required tests, docs impact,
and unresolved decisions in one reviewable package.

**Alternatives considered**:

- Only print stubs: rejected because it leaves most triage work manual.
- Auto-apply suggestions as complete rows: rejected because incomplete rows
  must not satisfy coverage.

## Decision: Model Runtime Compatibility Explicitly

The SDK should maintain a compatibility policy mapping SDK versions to tested
Multica CLI contracts and runtime diagnostics.

**Rationale**: Users install the CLI separately. A checked-in drift gate helps
maintainers, but runtime diagnostics help users detect unsupported
combinations before surprising method failures.

**Alternatives considered**:

- Rely only on upstream semantic versioning: rejected because upstream is in
  early version ranges and semantic contract hash is more precise.
- Warn on every method call: rejected because repeated warnings create noise.

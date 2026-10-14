## ADDED Requirements

### Requirement: Multica 0.6.2 coverage extends existing case tables

Verification SHALL extend the existing frozen unit, contract, and component case tables for every changed `0.6.2` contract. It SHALL cover both list-property public inputs; omitted, valid, unsupported, and conflicting discriminators; JSON, comma, and sequence forms; ambiguity, bounds, de-duplication, type-specific text and URL validation before command construction, null/unset, exact-element filtering, literal display values, daemon commit full/empty/missing states, wakeup diagnostic round trips and recovery, upload interruption, digit-prefix and cancellation search, project omission/null concurrency, and redacted server errors.

#### Scenario: Changed behavior has positive and negative rows
- **WHEN** the affected case tables are inspected
- **THEN** each changed mapping, decoder, validator, and error path has precise expected argv/result/error assertions without duplicate one-off test functions

#### Scenario: Legacy compatibility remains covered
- **WHEN** legacy `0.6.1` payloads omit newly introduced fields
- **THEN** focused fixtures prove compatible decoding without fabricated target values

#### Scenario: Invalid list-property input performs no I/O
- **WHEN** either direct set or create-time assignment receives a sequence without a discriminator, an unsupported/conflicting discriminator, overlong text, or an invalid/overlong URL
- **THEN** a table-driven case proves failure before command-plan execution and zero transport calls

### Requirement: Complete inventories and source links are release gates

Release verification SHALL prove all 209 target CLI nodes and all 196 supported response entrypoints reconcile with the approved manifest. Every changed source reference SHALL use a full pinned commit SHA, and a source-link audit SHALL reject mutable or unresolved references.

#### Scenario: Missing inventory coverage blocks release
- **WHEN** a target CLI node, supported response entrypoint, required semantic dimension, or changed/unchanged manifest row lacks a reviewed disposition
- **THEN** verification fails before packaging or release approval

#### Scenario: Mutable source reference blocks release
- **WHEN** an approved changed contract row cites a branch, abbreviated commit, or unresolved line target
- **THEN** the source-link audit fails

### Requirement: Repository and packaging gates remain offline-first

The implementation SHALL pass focused affected tests, the full non-live suite, non-live collection audit, Ruff check and format check, mypy for source and tests, approved-contract validate/render/check and freshness assertions, strict OpenSpec validation, documentation contract checks, source-link audit, wheel/sdist build, artifact packaging tests, and import verification before a CLI invocation. Live smoke SHALL remain separately credential-gated in GitHub CI and SHALL NOT weaken offline acceptance.

#### Scenario: Offline suite excludes live tests
- **WHEN** the non-live suite and collect-only audit run
- **THEN** no `tests/live/*` node is collected and all affected offline layers are present

#### Scenario: Generated runtime is reproducible
- **WHEN** contract render and check run from the approved input
- **THEN** the committed generated runtime is fresh and no review-only evidence file appears in Git

#### Scenario: Distribution artifacts preserve public changes
- **WHEN** wheel and sdist are built and tested
- **THEN** the target compatibility metadata, new model fields, list-property typing, and `py.typed` are present and importable before CLI execution

### Requirement: Migration documentation is direct and bounded

Documentation SHALL describe one direct `0.6.1` to `0.6.2` upgrade, the `0.6.3` exclusive ceiling, list-property input and output semantics, daemon commit and wakeup diagnostic presence, changed error behavior, and the explicit daemon-autostart deferral. It SHALL NOT claim that review evidence is production input or that autostart is supported.

#### Scenario: User guidance matches the approved contract
- **WHEN** API, compatibility, service usage, CLI coverage, migration, changelog, contributing, and release documents are checked
- **THEN** examples and claims agree with actual signatures, types, version gates, and deferred scope

### Requirement: Live verification is split by trust boundary

Release verification SHALL keep the exact-head GitHub CI live smoke separate from the isolated local artifact walkthrough. The CI job SHALL use CLI `0.6.2`, SHALL resolve an open same-repository pull request to a full approved head SHA before entering the protected environment, SHALL check out and test that exact SHA, and SHALL retain a run URL plus SHA comparison evidence. It SHALL NOT treat a default-branch checkout, a mutable branch name, or a mismatched dispatch SHA as evidence for the reviewed head. Credentials SHALL remain in the protected GitHub environment and SHALL NOT be printed, committed, attached, or moved to the local stand.

#### Scenario: Exact reviewed PR head passes live smoke
- **WHEN** the protected live workflow is approved for an open same-repository pull request and full reviewed head SHA
- **THEN** the resolved PR head, approved input, checked-out Git commit, and tested product revision are identical, CLI `0.6.2` passes strict compatibility preflight, and the live suite result is linked to that exact SHA

#### Scenario: Default branch or mismatched head is rejected as evidence
- **WHEN** the dispatch input does not equal the open PR head or the checkout resolves to the default branch instead of the approved head
- **THEN** the protected live test does not run and no resulting workflow execution satisfies the live-smoke release gate

#### Scenario: Local artifact walkthrough remains isolated
- **WHEN** an independent tester runs the repository-native walkthrough in the designated local test context
- **THEN** the SDK invokes only wrapper-owned `multica-test` without profile/server/workspace overrides, the primary Multica and its credentials remain untouched, representative public SDK results are captured as sanitized JSON/text artifacts, and all uniquely named test resources are cleaned on success or failure

#### Scenario: Evidence contains no credentials
- **WHEN** CI logs and local artifacts are inspected before publication
- **THEN** they contain tested revisions, commands, exit codes, assertions, resource IDs or hashes as needed, but no token, password, profile contents, private server setting, or reusable credential

No before/after image SHALL be required because the product's human-facing CLI, log, progress, and browser output is unchanged.

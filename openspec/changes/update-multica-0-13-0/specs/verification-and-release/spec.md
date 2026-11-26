## MODIFIED Requirements

### Requirement: Upgrade verification is layered and traceable

Every affected requirement scenario SHALL map to an existing sufficient check, a new lower-level test, a focused live case, or a reasoned exclusion, with product and evidence revisions recorded separately.

#### Scenario: Lower-level matrices are table-driven

- **WHEN** blocker, rerun-task, handoff, task-document, presence, privacy, command, response, compatibility, or error cases are added
- **THEN** they extend existing frozen dataclass case tables and shared fixtures before adding distinct test functions or files

#### Scenario: Offline gate remains backend-free

- **WHEN** contract validate/render/check, source-link audit, Ruff check/format, `mypy src`, `mypy tests`, package validation, collection-only marker verification, and `pytest -m "not live"` run
- **THEN** they require no backend/network, exclude all live nodes, and pass on the exact candidate revision

### Requirement: Interaction-only behavior has isolated live evidence

Focused live verification SHALL prove only the real CLI/backend interactions that lower-level checks cannot establish: blocker visibility/count privacy, lifecycle failures, handoff round-trip, task document attribution/access, and rerun-task replacement.

#### Scenario: Readiness gate protects the attempt

- **WHEN** the Tester begins live verification
- **THEN** the exact product revision, test-script revision, isolated `multica-test` profile/daemon, dedicated data namespace, stand health, renderer availability, focused offline checks, and evidence destination are recorded before mutation

#### Scenario: Independent walkthrough is not a test rerun

- **WHEN** automated focused cases complete
- **THEN** the Tester independently creates and inspects equivalent resources through public SDK/CLI actions, records expected state and failure observations, and does not substitute a second script invocation for manual inspection

#### Scenario: Evidence is genuine and sanitized

- **WHEN** changed read output is captured on macOS
- **THEN** actual baseline/candidate text and genuine PNG captures use equivalent fixtures, locale, width, and output mode; unsupported ANSI/TTY/progress states are disclosed; private URLs, credentials, and personal data are absent

#### Scenario: Cleanup preserves proof

- **WHEN** live verification ends or fails
- **THEN** only test-owned stand resources are removed, while the evidence branch/MR/commits and Multica attachments remain; no branch, MR, or environment is merged/deleted without separate authorization

### Requirement: Evidence publication is exact-revision and attachment based

Verification results SHALL be published in Multica with read-back and links to normal Git artifacts; raw evidence SHALL not be committed unless it is the tested functional output.

#### Scenario: Tester publishes complete result

- **WHEN** verification finishes
- **THEN** the final comment identifies product/test revisions, commands and exit codes, assertions, MR/commit/file links, image attachments, provenance, cleanup result, and unresolved findings, and read-back confirms attachments

#### Scenario: Planning artifacts do not claim execution

- **WHEN** this planning package is reviewed
- **THEN** all tests and live cases are marked planned, no result is called PASS, and no generated log, image, diagnostic JSON, or transient evidence is tracked

### Requirement: Automatic local runs obey the workspace limit

Automatic local test suites SHALL stop at ten minutes and continue in GitHub Actions on the published exact revision when longer execution is expected or observed; manual agent walkthroughs are not subject to that automatic-suite limit.

#### Scenario: Long suite moves to CI

- **WHEN** an automatic local suite is expected to exceed or reaches ten minutes
- **THEN** only that run's process is stopped, its partial result is recorded, and the complete suite runs through the existing CI job without splitting to evade the limit

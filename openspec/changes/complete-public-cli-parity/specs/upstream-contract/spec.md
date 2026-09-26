## MODIFIED Requirements

### Requirement: D15–D17 public-symbol integrity
The approved contract MUST define immutable public/wire schemas, cardinality,
presence semantics, validators, command mappings, and exact vectors for
profile, repository, and runtime operations. Validation MUST resolve every
approved `public_symbol`, normalize and compare its signature, and require
exactly one canonical vector for every approved operation. Repository checkout
SHALL be a governed native process operation that delegates checkout and
registration to the CLI, accepts the reviewed URL/ref/fresh inputs, returns the
inspectable emitted path/metadata contract, and does not reimplement the daemon
checkout registry. Source and binary evidence remain review-only and MUST NOT
generate public behaviour without approval.

#### Scenario: Contract cannot certify a missing SDK method
- **WHEN** an approved D15–D17 public symbol is absent, has a different signature, or lacks one canonical vector
- **THEN** the contract integrity gate fails before release verification

#### Scenario: Repository checkout delegates to the CLI
- **WHEN** the native checkout operation runs
- **THEN** exact reviewed argv reaches the controlled process transport and the SDK returns the CLI-emitted result without recreating checkout orchestration

### Requirement: Issue wakeup is governed as a complete family
The approved contract SHALL govern the `issue wakeup` parent and public leaves
`events`, `list`, `get`, `disable`, `create`, and `update` as a complete typed
family. It SHALL record exact agent, instruction, kind, mode, event, actor,
task, parent, absolute/delayed/interval/cron schedule, and timezone mappings;
complete-replacement and re-enable behavior; bounded one-shot busy retry;
duration constraints; mutual exclusions; pagination; response shapes; and
loop-protection semantics.

#### Scenario: Every wakeup leaf has typed coverage
- **WHEN** the approved contract is validated, rendered, and compared with public discovery
- **THEN** every public wakeup leaf has one governed operation, source mapping, response contract, and canonical positive and negative vectors

#### Scenario: Wakeup update preserves replacement semantics
- **WHEN** a caller updates a wakeup
- **THEN** the public API makes complete replacement and automatic re-enable behavior explicit and does not present update as an ordinary partial patch

### Requirement: Public chat and runtime-profile families are promoted
The approved contract SHALL govern chat history/thread and runtime profile
list/create/update/delete/set-path/unset-path operations. Runtime profile create
SHALL expose the reviewed `runtime-type` and compatible legacy
`protocol-family` rules. Prior `separate_extension_candidate`, `defer`, and
public-family `not_sdk_surface` dispositions SHALL be invalid for these public
families.

#### Scenario: Former deferrals fail strict validation
- **WHEN** the pinned target contract still classifies a public chat, wakeup, or runtime-profile operation as deferred or outside the SDK
- **THEN** strict validation fails before generated or handwritten public behavior is accepted

### Requirement: Complete target inventory governs the SDK
The approved contract SHALL reconcile the complete pinned public CLI tree, not
only the 164 currently approved operations and 167 currently reviewed response
entrypoints. Every public leaf, effective input, emitted response variant, and
nested field SHALL link to pinned source/help evidence, disposition, public
symbol or transport equivalent, compatibility policy, and test references.

#### Scenario: Approved-subset counts cannot certify parity
- **WHEN** the current approved operation and response counts match their historical baselines but source/help inventory contains additional public items
- **THEN** the parity gate fails until every additional item is reviewed and dispositioned

#### Scenario: Unreviewed source patterns fail closed
- **WHEN** extraction reports an unresolved helper, dynamic enum, imperative constraint, presence-sensitive branch, or unknown output mapping relevant to the public CLI
- **THEN** the item remains a blocking review record and changes no generated behavior

### Requirement: Complete response review follows actual CLI output
The approved contract SHALL review every public response-producing entrypoint
against the concrete CLI output path and preserve every emitted envelope,
variant, nested field, type, nullability, omission rule, redaction rule,
pagination signal, ordering rule, timestamp/numeric encoding, mutation
acknowledgement, and error behavior. Compatibility claims based only on an
unchanged upstream version delta or fixtures synthesized from SDK models SHALL
NOT certify the response.

#### Scenario: Advertised decoder matches a native payload
- **WHEN** a public operation claims a structured return model
- **THEN** a source-linked native-shape fixture passes through the public operation decoder and preserves all reviewed data

#### Scenario: Unchanged version delta does not hide an old mismatch
- **WHEN** the same upstream response exists in consecutive CLI versions but the SDK decoder has never matched it
- **THEN** the entrypoint is classified as incompatible until the public model and decoder are corrected

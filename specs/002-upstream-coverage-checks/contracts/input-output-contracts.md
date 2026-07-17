# Contract: Input, Output, and Runtime Compatibility

## Typed Input Contracts

Typed coverage requires an input contract for every public SDK operation.

Required details:

- Python parameter to positional argument or CLI flag mapping.
- Required/optional rules.
- Boolean encoding.
- Repeated/list encoding.
- Enum mapping and strict/open policy.
- Mutually exclusive and required-together groups.
- Environment/config/profile/workspace dependencies.
- Expected process exit behavior.

Validation contract:

- Every typed method has at least one offline argv contract test.
- Argv tests intercept process invocation and compare exact `list[str]`.
- Constraints have positive and negative tests.
- Raw matching between Python parameter names and CLI/API names is not accepted as proof.

## Typed Output Contracts

Typed structured output requires output provenance.

Required details:

- Output mode: JSON, text, binary, streaming, process, or none.
- Decoder/model identity.
- Checked-in fixture or schema reference.
- Schema hash for every structured JSON output; text, binary, streaming,
  process, and none outputs must record `schema_ref: null` and an explicit
  non-structured-output policy.
- Decoder policy for unknown fields.
- Confidence level when output cannot be collected without a server.

Validation contract:

- Every JSON decoder has a valid fixture.
- Strict decoders have negative fixtures for removed or type-changed fields.
- Optional output field additions are tested separately from removed/type-changed fields.
- Curated fixtures with source provenance are allowed when live server output is unavailable.
- Decoder behavior for `strict`, `permissive-extra-fields`, `text-only`, and
  `custom` is defined in `implementation-oracles.md`; implementations must not
  invent additional decoder-policy semantics.

## Runtime Compatibility Policy

The SDK compatibility matrix describes tested Multica CLI contracts.

Required details:

- SDK version.
- Minimum supported CLI version.
- Maximum tested CLI version.
- Contract hashes for tested versions.
- Runtime policy for older, newer-untested, and unknown-commit executables.
- Explicit advanced-user override behavior.

Validation contract:

- CLI version/build metadata is read once per client instance and cached.
- Runtime diagnostic contains detected CLI version and supported range.
- Warnings are not repeated on every method call.
- README/docs compatibility section is generated from the matrix.

## Why

The merged public-SDK simplification still rejects several natural Python values promised by its canonical examples, allows known interactive or process-oriented commands through the raw CLI escape hatch, and returns detached issues from the direct children API. Completing these contracts now prevents the README from advertising workflows that either fail locally or produce entities that cannot continue the workflow.

## What Changes

- Accept a path-like `description_file` in project creation and ordinary inline text or path-like description inputs in issue creation, while retaining semantic description variants for explicit stdin/file/inline behavior.
- Accept appropriate bound entities anywhere the affected issue/project workflows unambiguously require an identifier, and normalize supported status strings to the governed enum value before command construction.
- Keep eager and `*_command()` signatures in parity, preserve `OperationOptions` plus `Unset`/`None` semantics, and reject invalid or conflicting natural inputs with `TypeError` or `ValueError` before I/O.
- Classify known process-oriented command forms before transport: reject interactive, TTY-dependent, and managed-process forms with an actionable typed-API/`ManagedProcess` hint, while allowing the governed bounded forms `auth login --token <token>` and `workspace watch` and continuing to accept unknown bounded non-interactive argv.
- Bind every issue in both `children` and `unstaged` returned by `client.issues.children(...)` to the originating client without implicit hydration or additional CLI calls.
- Reorder the README introduction around `MulticaClient()` → `issues.get(...)` → direct entity action, then listing and command inspection, using only the final natural input forms and no removed request DTOs.
- Extend table-driven contract, unit, component, documentation, typing, and offline-suite coverage for normalization, signature parity, zero-I/O failures, raw CLI classification, and no-N+1 child binding.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdk-surface`: Common project/issue inputs gain explicit natural-value normalization and consistent eager/command signatures, without restoring one-operation request DTOs.
- `raw-cli-escape-hatch`: The escape hatch classifies overloaded command forms, rejecting interactive `auth login` without a token and other known process-oriented paths while allowing bounded token login, `workspace watch`, and unknown bounded non-interactive commands.
- `bound-resource-relations`: Direct issue-children pages bind all returned issues to the originating client with no hydration calls.
- `verification-and-release`: Offline gates cover the final natural inputs, local validation, README order, raw CLI boundary, and actionable child collections.

## Impact

- Public signatures and normalizers in project, issue, and raw CLI resources change; approved operation metadata and generated signature projections may need corresponding updates without changing upstream argv or response contracts.
- Direct issue-children decoding changes only client binding/finalization; wire models, pagination shape, lazy relation behavior, and transport call counts remain unchanged.
- README examples and focused contract/unit/component tests are updated. No new runtime dependency, upstream CLI change, request DTO, automatic issue hydration, or subprocess architecture redesign is introduced.

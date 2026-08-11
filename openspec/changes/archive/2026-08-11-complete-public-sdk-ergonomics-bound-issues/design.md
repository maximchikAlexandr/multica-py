## Context

The merged simplification already provides direct keyword APIs, bound issue entities across most collection origins, explicit domain actions, a raw argv escape hatch, and the offline inventory gates. Four seams remain inconsistent with that design:

- `ProjectResource.create[_command]` accepts only inline `description`, while upstream already has a governed `--description-file` mapping.
- `IssueResource.create[_command]` requires an `IssueDescriptionInput` wrapper and a raw `project_id`; status command builders assume callers passed enums and access `.value` directly.
- `CliResource._validate_argv` validates only argv shape, so known `ManagedProcess`/interactive paths—including the no-token overload of `auth login`—can be built as bounded `CliResult` plans, while token login is already a bounded action.
- `_issue_children_result_from_wire` creates detached `Issue` objects for both `children` and `unstaged`; unlike list/search finalizers, `IssueResource.children_command` does not apply the resource client.

The change must preserve the approved upstream argv, passive command inspection, `OperationOptions`, immutable entity snapshots, lazy-loading behavior, and the decision from GitHub issue #42 to remove one-operation request DTOs. It spans public resources, models/type aliases, the approved contract/generated projection, docs, and several offline test layers, so a design artifact is warranted.

## Goals / Non-Goals

**Goals:**

- Make the documented common project/issue flows accept ordinary Python values with deterministic pre-I/O validation.
- Make exact string enum values behave identically to enum members on the affected public status surfaces.
- Prevent the raw CLI escape hatch from misrepresenting already-known interactive, TTY-dependent, or managed execution modes.
- Make both direct child collections immediately actionable without hydration or N+1 calls.
- Give the implementer an exact compatibility, documentation, and verification path.

**Non-Goals:**

- Restoring request DTOs, generic request/kwargs resolution, or dual request-object APIs.
- Adding `status` to issue update, inventing an `"open"` alias, or widening unrelated enum-like fields.
- Changing upstream flags, response envelopes, transport execution, `ManagedProcess`, or the general lazy-relation architecture.
- Automatically hydrating partial issues, reading description files during preview, or validating file existence in the SDK.
- Blocking unknown raw commands by broad command-family or keyword heuristics.

## Decisions

### 1. Normalize natural values at the resource boundary

Add explicit keyword parameters rather than a generic object adapter. Project create gains `description_file`. Issue create gains `description`, `description_file`, and canonical `project: str | Project | None`, while retaining `description_input` for semantic variants and allowing the existing `project_id` compatibility spelling. Project-scoped create mirrors the description parameters but continues to derive the project identifier from its bound relation.

One small description normalizer selects exactly one source:

- omitted/`NoDescription` → no description flag;
- `str`/`InlineDescription` → `--description`;
- `str | os.PathLike[str]` through `description_file`, or `FileDescription` → `--description-file` with a lexical absolute path;
- `StdinDescription` → `--description-stdin`.

More than one source is a local `TypeError`. Blank or bytes-backed file paths are rejected; path normalization uses the command-construction cwd and lexical absolute-path operations only, with no `open`, `stat`, existence check, or content read. The existing `project_id` compatibility spelling conflicts with `project`; a local `_normalize_project_reference` follows the established assignment/issue-reference pattern and accepts only a nonblank string or `Project`, returning its ID without I/O.

Alternatives considered: converting ordinary inputs into public wrapper instances would keep the current internal shape but continue leaking wrappers into signatures; removing semantic variants would lose distinct stdin behavior; accepting arbitrary `_BoundEntity` values would defer an incompatible reference to the CLI. Explicit source selection and type-specific reference normalization keep the contract inspectable.

### 2. Normalize only exact closed status values

Introduce narrow helpers for `IssueStatus | str` and `ProjectStatus | str`. Existing enum instances pass through; strings are converted by the corresponding `StrEnum` constructor; other types raise `TypeError`. This applies after resolving an `IssueListFilter` and before any `.value` access, to issue resource and bound-issue status actions, and to `ProjectResource.set_status[_command]`. The current public method set has no `Project.set_status[_command]`; this change does not add a bound-project status action. The model decoder remains unchanged.

The conversion is case-sensitive and defines no semantic aliases. Therefore `"done"` works and `"open"` raises `ValueError`; README listing uses a real value such as `"todo"`. This resolves the accidental `AttributeError` without inventing a status mapping that upstream does not govern.

Alternative considered: documenting enum-only inputs would be internally consistent but would leave the canonical string examples from the public ergonomics contract unsupported. An open string pass-through was rejected because it would defer known closed-enum errors to transport.

### 3. Use an explicit raw-command execution-mode registry

After structural argv validation and before `_raw_command`, classify the leading argv path with a module-level immutable registry plus an explicit overload classifier. The initial reviewed entries are:

- `auth login` → inspect the execution form: `auth login --token <token>` is a bounded raw form and remains allowed, including trailing arguments/options after the token operand; `auth login` without that token form, including trailing arguments/options or a missing/option-like token operand, is interactive and rejects with a `client.auth.login(...)` / `ManagedProcess` hint;
- `setup cloud`, `setup self-host` → `client.setup` managed flows;
- `daemon start`, `daemon logs` → `client.daemon` managed flows;
- top-level `update` → `client.maintenance.update()` managed flow;

Prefix matching intentionally rejects trailing flags for the other registry entries, so `daemon logs --follow` cannot bypass classification. The `auth login` classifier is the exception: once the exact `--token <token>` operand form is established, trailing arguments/options remain in the bounded raw plan; without it, any trailing arguments/options remain rejected as interactive. Each rejected entry stores a reason and public replacement used in the `ValueError`. Neither the classifier nor its errors include the token operand. Allowed token-login plans use the existing redaction pipeline so previews, representations, execution diagnostics, exceptions, and returned stdout/stderr do not expose the token. The registry matches command paths, not generic words: an unknown `plugin watch` remains eligible for the forward-compatible bounded escape hatch. `workspace watch` is deliberately absent from the registry because `WorkspaceResource.watch[_command]` is the approved bounded `Command[ActionResult[None]]` surface; raw `workspace watch` therefore follows the ordinary bounded escape-hatch path. Both `command` and `command_command` share the same validation path.

Alternatives considered: rejecting every known typed command would destroy the escape hatch's intended convenience; treating `auth login` as one undifferentiated prefix would reject the governed token action; blocking whole top-level families would prevent future bounded commands; inferring from names such as `watch` or `start` would be brittle. An explicit reviewed registry with a narrow auth overload classifier is small, testable, and updated when typed execution-mode contracts change.

### 4. Bind the complete children envelope in one finalizer

Keep `_issue_children_result_from_wire` as a client-agnostic wire decoder. Add `IssueResource._bind_issue_children_result` that reconstructs `IssueChildrenResult`, applies `_with_client(self._client)` to every `items`/`children` and `unstaged` entry, and copies `total`, `child_stages`, `limit`, `offset`, `has_more`, and `next_cursor` unchanged. `children_command` maps decode then bind, following list/search finalizers. Tighten the runtime `unstaged` annotation to `tuple[Issue, ...]` if needed for mypy parity.

This performs no transport call and preserves the inspected plan. The bound `Issue.children` lazy relation may continue adapting the direct envelope, but tests must prove direct and relation paths retain the same originating scope without extra `issue get` calls.

Alternative considered: calling `issues.get` for each row would populate more fields but violates partial-snapshot honesty and introduces N+1 I/O. Moving client references into wire models would couple transport decoding to a client and conflict with existing resource finalizer conventions.

### 5. Keep contracts, generated projections, docs, and tests synchronized

Update approved signatures/mappings and deterministic generated descriptors for the natural keywords and status unions while leaving CLI bindings and response types unchanged. Keep the public status surface limited to the existing root resources and bound issue actions; do not add a `Project.set_status[_command]` pair. Extend existing frozen operation/invalid-input tables and shared transport fixtures rather than adding parallel test frameworks. Raw execution cases form one frozen matrix covering allowed token-login, rejected no-token/malformed auth forms, the other denied prefixes, bounded `workspace watch`, and expected hints/redaction; children envelope cases cover empty, children-only, unstaged-only, and mixed payloads with exact call counts.

README starts with default client construction, `issues.get`, and `issue.set_status("done")`; listing with `status="todo"` follows, then `get_command` inspection. API/migration/service docs explain semantic description variants and the raw-command deny boundary without describing request DTO compatibility.

## Risks / Trade-offs

- **[Risk] Multiple description spellings create ambiguous calls** → Enforce exactly one source before path normalization or plan construction and cover the full conflict matrix.
- **[Risk] Keeping `project_id` during compatibility leaves two spellings temporarily** → Make `project` canonical in docs, reject simultaneous use, and keep both signatures synchronized until a separately specified removal.
- **[Risk] Lexical paths differ from symlink-resolved paths** → Preserve passivity and let the CLI resolve/open the path at execution; assert exact normalization from a controlled cwd.
- **[Risk] A new upstream managed command is initially absent from the registry** → Tie registry review and tests to public operations returning `ManagedProcess` and update it during upstream contract reconciliation; keep bounded operations such as `WorkspaceResource.watch[_command]` out of the registry and do not compensate with overbroad heuristics.
- **[Risk] Auth overload classification either rejects token login or admits an interactive form** → Recognize only the governed `--token <token>` operand form, reject missing/option-like operands before transport, and never include the token in classifier errors or diagnostics.
- **[Risk] Binding only `children` repeats the original defect for `unstaged`** → Reconstruct the complete envelope in one helper and parameterize all envelope shapes.
- **[Risk] Contract projection drifts from hand-written signatures** → Update the approved contract first, render deterministically, and run exact signature/canonical-vector gates before the full suite.

## Migration Plan

1. Add failing table-driven signature, natural-input, status, raw-boundary, and child-binding tests plus documentation-order assertions.
2. Update the approved contract and generated projection for the new public parameters/unions without changing upstream command/response evidence.
3. Implement resource-boundary normalizers, wire them identically into eager/command pairs and project-scoped create, and preserve existing argv and option snapshots.
4. Add raw execution-mode classification and the children-result binding finalizer.
5. Rewrite README and affected API/service/migration examples around the final natural forms and explicit raw-command boundary.
6. Run OpenSpec validation, deterministic contract validation/render/check, Ruff, mypy for source and tests, package validation, and the complete offline test suite.

The change requires no stored-data or server migration. Before release it can be rolled back by reverting the implementation/docs/contract commit set; no runtime dual-mode fallback is required.

## Open Questions

None. The affected issue, merged baseline, current resource conventions, and pinned command inventory resolve the public spellings, status policy, root-only project status surface, bounded raw `workspace watch` behavior, rejected raw paths, binding point, and verification scope.

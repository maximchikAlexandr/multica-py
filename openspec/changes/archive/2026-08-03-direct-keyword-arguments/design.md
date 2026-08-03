## Context

The public SDK exposes request-bearing resource methods that take a single
positional `*Request` msgspec.Struct. Today every caller must import the
request class and construct it inline even for trivial two-field operations.
Issue #22 asks for a direct keyword form alongside the request-object form,
with the direct form as the documentation default and the request-object form
kept for reuse/validation/cross-layer assembly.

Current state of the in-surface request objects (all `msgspec.Struct,
frozen=True, kw_only=True`):

| Method | Request class | Fields (defaults) | Notes |
|---|---|---|---|
| `projects.create` | `ProjectCreateRequest` | `name: str`, `description: str \| None = None` | `validate_nonblank(name)` at call site |
| `projects.update` | `ProjectUpdateRequest` | `name: str \| UnsetType = Unset`, `description: str \| None \| UnsetType = Unset` | `Unset` = omit; `None` for description is rejected by CLI; `ValidationError` |
| `agents.create` | `AgentCreateRequest` | `name`, `description`, `runtime_id`, `model` (all `str \| None = None` except `name`) | `validate_nonblank(name)` |
| `agents.update` | `AgentUpdateRequest` | `name: str \| None`, `description: str \| None` | `validate_nonblank(agent_id)` is positional id, not request |
| `skills.create` | `SkillCreateRequest` | `name`, `description` | `validate_nonblank(name)` |
| `skills.update` | `SkillUpdateRequest` | `name`, `description` | `validate_nonblank(skill_id)` positional |
| `issues.create` | `IssueCreateRequest` | `title`, `description_input: IssueDescriptionInput = NoDescription()`, `priority`, `assignee_id`, `label_ids: tuple[str,...] = ()`, `project_id`, `parent_id` | `__post_init__` validates description_input type, blank project_id/parent_id |
| `issues.update` | `IssueUpdateRequest` | `title`, `description`, `priority`, `assignee_id`, `project_id`, `parent_id` (all optional) | `__post_init__` validates blank project_id/parent_id |
| `issues.assign` | `IssueAssignmentRequest` | `issue_id: str`, `member_id`, `agent_id`, `squad_id`, `unassign: bool = False` | `__post_init__` exactly-one-target |
| `issues.reorder` | `IssueReorderRequest` | `issue_id: str`, `before_id`, `after_id`, `top: bool`, `bottom: bool` | `__post_init__` exactly-one-target |
| `runtimes.update` | `RuntimeUpdate` | `target_version: str`, `wait: bool = False` | nonblank check at call site |
| `project_resources.add_local_directory` | `ProjectResourceAddLocalDirectoryRequest` | `local_path: str \| Path`, `daemon_id: str`, `label: str \| None` | `__post_init__` nonblank `daemon_id` only (absolute-path check is in `LocalDirectoryResourceRef.__post_init__`, a separate out-of-scope class; call site normalizes `local_path` via `os.path.abspath`) |
| `project_resources.update_local_directory` | `ProjectResourceUpdateLocalDirectoryRequest` | `local_path: str \| Path` | `__post_init__` non-empty |
| `users.profile_update` | `UserProfileUpdate` | `description: str \| msgspec.UnsetType = msgspec.UNSET` | `Unset` rejected at call site |

Constraints: no public method may be renamed, split, or removed. No transport,
argv, wire, or dependency change. The request classes stay as the source of
truth for field names, types, defaults, and `__post_init__` validation. Tests
reuse the existing canonical table-driven pattern (`OperationCase` in
`tests/cases/operations.py`, consumed by
`tests/unit/resources/test_operations.py::test_operation`) and the shared
fake-CLI client fixture; no new test framework or third-party dep. `uv run mypy
src` and `uv run mypy tests` must pass; no `Any` leaks.

## Goals / Non-Goals

**Goals:**

- Add a dual-input calling convention (request-object OR keyword-only direct
  fields) to the 14 in-scope methods listed in the proposal, with
  `@overload`-typed signatures.
- Reject mixed input with a precise `TypeError` before any CLI invocation.
- Make the direct keyword form produce argv/transport/stdin/timeout identical
  to the equivalent request-object call, including update-style
  omit/`None`/`Unset` presence semantics.
- Keep all request classes, request-object signatures, transport behavior, and
  public method names unchanged.
- Document the direct form as the default and the request-object form as the
  advanced/reusable alternative.

**Non-Goals:**

- No new generic request-builder abstraction, dispatcher framework, or
  "dual-input mixin" beyond a tiny shared helper.
- No change to out-of-scope request-bearing methods
  (`issue_comments` list overloads, `issue_metadata.query`,
  `issue_metadata.set_typed`).
- No removal or rename of any request class.
- No wire, transport, subprocess, or generated-contract change.
- No change to entity models, lazy relations, or pagination.
- No public method-name additions (no `create_from_request`, etc.).

## Decisions

### Decision 1: Single positional request slot + `**kwargs` dispatch

Each in-scope method gets a signature shaped (for the `projects.create` example)
as:

```python
@overload
def create(self, request: ProjectCreateRequest, /) -> Project: ...
@overload
def create(self, *, name: str, description: str | None = None) -> Project: ...

def create(self, request: ProjectCreateRequest | None = None, /, **kwargs: object) -> Project:
    req = _resolve_request(request, kwargs, ProjectCreateRequest)
    validate_nonblank(req.name)
    args = ["project", "create", "--title", req.name]
    if req.description is not None:
        args.extend(["--description", req.description])
    return self._bind_project(project_from_wire(self._run_json_decode(tuple(args), ProjectWire)))
```

The positional request object uses `/` (positional-only) so the name `request`
cannot collide with a request-model field named `request`. Direct fields arrive
via `**kwargs` and are routed through a single shared helper.

**Why this shape:**

- One implementation body per method, not two. The body always works on a
  `req` instance, so the existing argv-building logic is untouched.
- `@overload` gives precise types for both forms; the runtime body uses a
  broad-but-honest annotation (`ProjectCreateRequest | None` + `**kwargs`).
- `/` on the request slot prevents a field literally named `request` from
  shadowing the request object in any future request model.

**Alternatives considered:**

- *Two real methods (`_create_from_request` + `_create_from_kwargs`)* —
  rejected: duplicates argv logic, drift risk, and the public name is one.
- *A per-method `@singledispatchmethod`* — rejected: `singledispatch` keys on
  the first positional type only, has no hook for "no positional arg, use
  kwargs", and adds a decorator per method for no gain.
- *Generic `TRequest` dispatcher with `TypeAdapter`* — rejected: msgspec
  structs do not expose a typed `from_kwargs` constructor without runtime
  introspection; a generic path would hide per-field validation and
  presence semantics. A small per-method overload + one shared helper is
  shorter and explicit.

### Decision 2: One shared `_resolve_request` helper in `resources/_base.py`

Add one module-private function in `src/multica_py/resources/_base.py`:

```python
def _resolve_request(
    request: R | None, kwargs: dict[str, object], cls: type[R]
) -> R:
    if request is not None and kwargs:
        raise TypeError(
            "Pass either a request object or keyword arguments, not both."
        )
    if request is not None:
        return request
    if not kwargs:
        raise TypeError(
            f"Pass a {cls.__name__} or its keyword arguments; got neither."
        )
    try:
        return cls(**kwargs)  # type: ignore[arg-type]
    except TypeError as e:
        raise TypeError(str(e)) from None
```

where `R = TypeVar("R", bound=msgspec.Struct)`.

**Why one helper:** the dispatch rule (reject mixed, reject neither, construct
otherwise) is identical for all 14 methods. msgspec structs accept
`Struct(**kwargs)` with `kw_only=True`, so `cls(**kwargs)` reuses the request
model's own `__post_init__` validation for free — no per-method re-validation.
A bad field name produces a `TypeError` from msgspec, which we re-raise as
`TypeError` (preserving the "this field doesn't exist" signal).

**`Unset`/`None` presence:** for update-style requests, callers pass
`description=Unset` or `description=None` explicitly as kwargs. `cls(**kwargs)`
forwards them verbatim, so `ProjectUpdateRequest(description=None)` and the
direct `description=None` call construct identical structs. The existing
argv-building branches (`if request.description is Unset: ... elif ...
is None: raise ValidationError ...`) then run unchanged. Omitting
`description` in the direct form maps to the field's default (`Unset`), again
identical to the request-object form.

**Why not `inspect.signature` introspection to build a "correct" TypeError
message:** msgspec already raises a useful `TypeError` naming the unexpected
field. Re-raise it. No introspection, no fragile signature mirroring.

### Decision 3: Overload ordering and the runtime signature

For every in-scope method, emit two `@overload`s in this order:

1. `def method(self, request: <Req>, /) -> <Return>: ...`  (request-object
   form)
2. `def method(self, *, field1, field2, ...) -> <Return>: ...`  (direct form,
   keyword-only, mirroring the request model fields, defaults, and
   optionals exactly)

then the runtime body:

```python
def method(self, request: <Req> | None = None, /, **kwargs: object) -> <Return>: ...
```

The runtime annotation is deliberately broad. mypy resolves calls to one of the
two `@overload`s; the body's annotation only needs to be internally consistent
and `Any`-free. `**kwargs: object` (not `Any`) keeps the no-`Any` rule.

For methods that already take a required positional identifier before the
request (e.g. `projects.update(self, project_id: str, request: ...)`,
`agents.update(self, agent_id: str, request: ...)`), the overloads are:

1. `def update(self, project_id: str, request: ProjectUpdateRequest, /) -> Project: ...`
2. `def update(self, project_id: str, *, name=..., description=...) -> Project: ...`
3. runtime: `def update(self, project_id: str, request: ProjectUpdateRequest | None = None, /, **kwargs: object) -> Project: ...`

The pre-existing positional identifiers — `project_id` (on `projects.update`),
`agent_id` (on `agents.update`), `skill_id` (on `skills.update`), `runtime_id`
(on `runtimes.update`), and `project_id`/`resource_id` (on the
`project_resources` methods) — stay positional and are not part of the
dual-input dispatch.

**Exception — `issues.assign` and `issues.reorder`:** these two methods do
NOT take a separate positional `issue_id`. Their signatures today are
`IssueResource.assign(self, request: IssueAssignmentRequest)` and
`IssueResource.reorder(self, request: IssueReorderRequest)`, and `issue_id`
lives INSIDE the request class (`IssueAssignmentRequest.issue_id: str`,
`IssueReorderRequest.issue_id: str`). For these two methods the entire
request — including `issue_id` — is the subject of the dual-input dispatch,
so `issue_id` is a required keyword in the direct-form `@overload`
(`def assign(self, *, issue_id: str, member_id=..., agent_id=...,
squad_id=..., unassign: bool = False) -> IssueEntity: ...`). The `issues.update`
method is different: it already takes `issue_id` as a separate positional
identifier, which stays positional; `issues.update`'s direct form mirrors
only the `IssueUpdateRequest` fields (title, description, priority,
assignee_id, project_id, parent_id) as keywords.

### Decision 4: Field surface mirrors the request model exactly

The direct-form `@overload` keyword parameters mirror the request model's
fields one-to-one: same names, same types (including `str | None`, `bool`,
`tuple[str, ...]`, `IssueDescriptionInput`, `str | Path`, `str | UnsetType`),
same defaults, same optional-ness. No renaming, no aliasing, no "ergonomic"
shortcuts. This makes the request model the single source of truth and keeps
`__post_init__` validation authoritative.

For `issues.create`, `description_input` keeps its structured
`IssueDescriptionInput` type in the direct form. A future doc example can show
`description_input=InlineDescription(text="...")` or
`description_input=FileDescription(path=...)`. We do not add a convenience
`description: str` shortcut in this change — it would diverge from the request
model and is out of scope for issue #22.

### Decision 5: Documentation default flips to direct keyword form

In `docs/` resource method examples, the primary snippet for each in-scope
method becomes the direct keyword form. A secondary snippet shows the
request-object form with a one-line note: "Use a request object when you need
to reuse, validate, store, or pass the request across layers." Out-of-scope
request-bearing methods keep their request-object-only example.

### Decision 6: Tests reuse the existing table pattern

Per the AGENTS.md test rules, coverage is added as new rows on the existing
canonical table-driven infrastructure, not new files or near-identical
functions. The canonical case type is `OperationCase`
(`@dataclass(frozen=True)`) in `tests/cases/operations.py`; the canonical
parametrized consumer is
`tests/unit/resources/test_operations.py::test_operation` (parametrized over
`OPERATION_CASES`). Per-domain case classes that exist today
(`AvatarArgvCase`, `SkillFileArgvCase`, `ProjectResourceDecodeCase`, etc.) are
not the canonical argv-parity surface and MUST NOT be referenced as the
target for new parity rows. For each in-scope method, add parity rows to
`OPERATION_CASES` via `tests/cases/operations.py` — the direct-form row and
the request-object row are two `OperationCase(...)` entries with the same
`expected_argv` (and matching `stdin`/`timeout`/`transport_method`):

- one `OperationCase` row for the direct keyword form (args empty, the
  request fields passed as `kwargs`, `expected_argv` asserting the exact
  argv, and `stdin`/`timeout` where relevant);
- one `OperationCase` row for the request-object form (the request passed
  positionally in `args`, `kwargs` empty) asserting the same `expected_argv`
  (parity). If an equivalent request-object row already exists in
  `OPERATION_CASES`, do NOT duplicate it — add only the direct-form row and
  reuse the existing row as the parity baseline.

The mixed-input and neither-input `TypeError` paths and the
`__post_init__`-validation `ValueError` paths do NOT fit the
`test_operation` argv-parity shape (they raise before transport) and go
into dedicated tests in `tests/unit/resources/` that reuse the shared
`mock_transport` fixture from `tests/unit/resources/conftest.py`:

- one `@pytest.mark.parametrize` test across all 14 in-scope methods
  asserting mixed-input `TypeError` (request + kwargs) and neither-input
  `TypeError`, asserting the transport is never called;
- where the request model has `__post_init__` validation, negative rows in
  the same parametrized test asserting the same `ValueError` from the
  direct form.

## Risks / Trade-offs

- **Risk:** `@overload` + broad runtime body hides a wrong field name at
  runtime that mypy would catch statically.
  → **Mitigation:** the `cls(**kwargs)` call re-raises msgspec's `TypeError`
  naming the unexpected field; static checkers catch it for typed callers; the
  parametrized negative test covers the runtime path.
- **Risk:** Field-surface drift between the `@overload` and the request model
  if someone adds a field to the request class but forgets the overload.
  → **Mitigation:** the tasks include a single test that introspects each
  in-scope request class's fields and asserts the direct-form `@overload`
  exposes the same keyword set. This is the one place introspection is
  warranted — it is a structural-parity guard, not a dispatch mechanism.
- **Risk:** `Unset`/`None` presence semantics on update methods silently
  diverge between the two forms.
  → **Mitigation:** the parity `OperationCase` rows assert bit-for-bit argv for
  omitted/`None`/`Unset` on `projects.update` and `users.profile_update`.
- **Risk:** The broad runtime `**kwargs: object` tempts callers to bypass the
  overloads with untyped dicts.
  → **Mitigation:** `cls(**kwargs)` still runs `__post_init__`; mypy warns on
  `dict` unpacking against an `@overload`; the no-`Any` rule holds.
- **Trade-off:** The runtime body's annotation (`<Req> | None = None` +
  `**kwargs: object`) is less precise than the overloads. This is the standard
  `@overload` trade-off and is acceptable because the overloads are the
  public type contract.

## Migration Plan

- Purely additive: every existing request-object call continues to work with
  no source change. No deprecation, no removal.
- Rollout is one commit per resource module (projects, agents, skills, issues,
  runtimes, project_resources, users) so each module's tests land green
  independently and review stays small.
- Documentation flip lands in the same commit as each module's code change so
  the docs never show a form the code does not yet support.
- Rollback: revert the branch; no wire, storage, or persisted-state impact.

## Open Questions

None. The scope, method list, presence semantics, and test approach are
settled by the proposal and the request models' current behavior.
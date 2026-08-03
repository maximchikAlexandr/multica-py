## 1. Shared dispatch helper

- [ ] 1.1 Add `_resolve_request(request, kwargs, cls)` to `src/multica_py/resources/_base.py` with `R = TypeVar("R", bound=msgspec.Struct)`: raise `TypeError("Pass either a request object or keyword arguments, not both.")` when `request is not None and kwargs`; raise `TypeError(f"Pass a {cls.__name__} or its keyword arguments; got neither.")` when both are empty; otherwise return `request` or `cls(**kwargs)` (re-raising msgspec's `TypeError` as `TypeError`). No `Any`. Keep it module-private.
- [ ] 1.2 Add a unit test for `_resolve_request` covering: request-only returns it, kwargs-only constructs, mixed raises the exact message, neither raises the "got neither" message, unknown kwarg re-raises `TypeError`.

## 2. `projects` module

- [ ] 2.1 Add two `@overload`s + runtime body to `ProjectResource.create`: `(self, request: ProjectCreateRequest, /) -> Project` and `(self, *, name: str, description: str | None = None) -> Project`; runtime `(self, request: ProjectCreateRequest | None = None, /, **kwargs: object) -> Project` calling `_resolve_request` then the existing argv logic unchanged.
- [ ] 2.2 Add two `@overload`s + runtime body to `ProjectResource.update`: `(self, project_id: str, request: ProjectUpdateRequest, /) -> Project` and `(self, project_id: str, *, name: str | UnsetType = Unset, description: str | None | UnsetType = Unset) -> Project`; runtime with `_resolve_request`. Preserve the existing `Unset`/`None`/`ValidationError` branches verbatim.
- [ ] 2.3 Add `ArgvCase` rows in `tests/unit/resources/` for `projects.create` direct form (`name=`, `description=`) asserting exact argv, plus a parity row asserting the request-object form emits the same argv.
- [ ] 2.4 Add `ArgvCase` rows for `projects.update` direct form covering omitted `description`, `description=None` (expect `ValidationError`), `description=Unset`, and a non-`None` value; plus request-object parity rows for each.
- [ ] 2.5 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 3. `agents` module

- [ ] 3.1 Add dual `@overload`s + runtime body to `AgentResource.create` mirroring `AgentCreateRequest` (`name`, `description`, `runtime_id`, `model`).
- [ ] 3.2 Add dual `@overload`s + runtime body to `AgentResource.update` mirroring `AgentUpdateRequest` (`name`, `description`), keeping `agent_id: str` positional.
- [ ] 3.3 Add `ArgvCase` rows for both methods: direct form (all fields, optional fields omitted), request-object parity, and mixed-input `TypeError`.
- [ ] 3.4 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 4. `skills` module

- [ ] 4.1 Add dual `@overload`s + runtime body to `SkillResource.create` and `SkillResource.update` mirroring `SkillCreateRequest` / `SkillUpdateRequest`.
- [ ] 4.2 Add `ArgvCase` rows for both methods: direct form, request-object parity, mixed-input `TypeError`.
- [ ] 4.3 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 5. `issues` module

- [ ] 5.1 Add dual `@overload`s + runtime body to `IssueResource.create` mirroring `IssueCreateRequest` exactly, including `description_input: IssueDescriptionInput = NoDescription()`, `label_ids: tuple[str, ...] = ()`. Preserve the existing argv-building and post-create label-attach loop unchanged.
- [ ] 5.2 Add dual `@overload`s + runtime body to `IssueResource.update` mirroring `IssueUpdateRequest` (`title`, `description`, `priority`, `assignee_id`, `project_id`, `parent_id`).
- [ ] 5.3 Add dual `@overload`s + runtime body to `IssueResource.assign` mirroring `IssueAssignmentRequest` (`issue_id`, `member_id`, `agent_id`, `squad_id`, `unassign`). Preserve the exactly-one-target `__post_init__` validation by routing through `_resolve_request`.
- [ ] 5.4 Add dual `@overload`s + runtime body to `IssueResource.reorder` mirroring `IssueReorderRequest` (`issue_id`, `before_id`, `after_id`, `top`, `bottom`). Preserve exactly-one-target validation.
- [ ] 5.5 Add `ArgvCase` rows for all four methods: direct form (representative field combinations), request-object parity, mixed-input `TypeError`, and `__post_init__` `ValueError` (blank `project_id` on create/update, no-target and multi-target on assign/reorder).
- [ ] 5.6 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 6. `runtimes` module

- [ ] 6.1 Add dual `@overload`s + runtime body to `RuntimeResource.update` mirroring `RuntimeUpdate` (`target_version: str`, `wait: bool = False`), keeping `runtime_id: str` positional.
- [ ] 6.2 Add `ArgvCase` rows: direct form (`target_version=`, `wait=True/False`), request-object parity, mixed-input `TypeError`.
- [ ] 6.3 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 7. `project_resources` module

- [ ] 7.1 Add dual `@overload`s + runtime body to `ProjectResourceCollection.add_local_directory` mirroring `ProjectResourceAddLocalDirectoryRequest` (`local_path: str | Path`, `daemon_id: str`, `label: str | None = None`), keeping `project_id: str` positional.
- [ ] 7.2 Add dual `@overload`s + runtime body to `ProjectResourceCollection.update_local_directory` mirroring `ProjectResourceUpdateLocalDirectoryRequest` (`local_path: str | Path`), keeping `project_id` and `resource_id` positional.
- [ ] 7.3 Add `ArgvCase` rows: direct form, request-object parity, mixed-input `TypeError`, and `__post_init__` `ValueError` (relative `local_path` on add, blank `daemon_id`, blank `local_path` on update).
- [ ] 7.4 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 8. `users` module

- [ ] 8.1 Add dual `@overload`s + runtime body to `UserResource.profile_update` mirroring `UserProfileUpdate` (`description: str | msgspec.UnsetType = msgspec.UNSET`). Preserve the existing `if request.description is Unset: raise ValueError` branch verbatim.
- [ ] 8.2 Add `ArgvCase` rows: direct form with `description=` (present), direct form omitting `description` (expect `ValueError`), `description=Unset` (expect `ValueError`), request-object parity, mixed-input `TypeError`.
- [ ] 8.3 Run `uv run pytest -m "not live" tests/unit/resources` and `uv run mypy src` and `uv run mypy tests`; fix until green.

## 9. Structural parity guard

- [ ] 9.1 Add one test in `tests/unit/resources/test_operations.py` that, for each in-scope `(method, request_class)` pair, introspects the request class's `msgspec.structs.fields(cls)` and asserts the direct-form `@overload` exposes exactly those field names as keyword-only parameters with matching defaults. This is the only introspection-based test; it guards against field-surface drift.

## 10. Mixed-input and neither-input parametrized guard

- [ ] 10.1 Add one `@pytest.mark.parametrize` test in `tests/unit/resources/` that iterates all 14 in-scope methods and asserts: (a) calling with a request object plus any one direct field raises `TypeError` with the exact message `Pass either a request object or keyword arguments, not both.`; (b) calling with no request object and no kwargs raises `TypeError`. Use the shared fake-CLI client fixture; no CLI invocation occurs (assert transport not called).

## 11. Discovered-public-methods invariant

- [ ] 11.1 Re-run `tests/unit/resources/test_operations.py::test_discovered_public_methods` and confirm the discovered set is unchanged (no new public method names, no renamed methods). Update the canonical case count in `tests/cases/operations.py` only if the dual-input overloads change discovery — they must not.

## 12. Documentation

- [ ] 12.1 In `docs/`, flip the primary example for each of the 14 in-scope methods to the direct keyword form; add a secondary snippet showing the request-object form with a one-line note "Use a request object when you need to reuse, validate, store, or pass the request across layers." Leave out-of-scope request-bearing methods unchanged.
- [ ] 12.2 Add a short "Direct keyword vs request object" section to the SDK usage guide explaining the two forms, the exactly-one-style rule, the mixed-input `TypeError`, and the list of methods where only the request-object form is supported.

## 13. Final verification

- [ ] 13.1 Run `uv run pytest -m "not live"` (full offline suite) end-to-end and confirm green, no `tests/live/*` node collected.
- [ ] 13.2 Run `uv run mypy src` and `uv run mypy tests` end-to-end; confirm no `Any` leaks and no new errors.
- [ ] 13.3 Run `uv run ruff check` and `uv run ruff format --check`; fix until green.
- [ ] 13.4 Run `openspec validate direct-keyword-arguments` and `openspec validate --specs`; fix any reported drift.
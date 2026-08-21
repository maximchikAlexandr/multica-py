from __future__ import annotations

import datetime
import shlex
from collections.abc import Callable, Mapping
from contextlib import ExitStack
from dataclasses import dataclass, replace
from typing import Generic, Literal, Protocol, TypeGuard, TypeVar, cast

from multica_py._internal.redaction import (
    collect_diagnostic_secret_values,
    redact_diagnostic_argv,
)
from multica_py._internal.transport import CliTransport, _effective_environment
from multica_py.config import ClientConfig
from multica_py.execution import OutputArtifact

__all__ = ["Command"]

T_co = TypeVar("T_co", covariant=True)
T_plan = TypeVar("T_plan")
T_mapped = TypeVar("T_mapped")
T_source = TypeVar("T_source")
T_result = TypeVar("T_result")

_StepMode = Literal["run_bytes", "run_text", "spawn"]


@dataclass(frozen=True, slots=True)
class _StepRef:
    kind: Literal["result", "temp", "output"]
    field: str | None = None
    alias: str | None = None


@dataclass(frozen=True, slots=True, repr=False)
class _Step:
    argv: tuple[str, ...]
    mode: _StepMode
    stdin: bytes | None = None
    timeout: datetime.timedelta | None = None
    refs: tuple[tuple[int, _StepRef], ...] = ()
    decode: Callable[[bytes, str], object] | None = None
    result_alias: str | None = None


class _TempProvider(Protocol):
    def __call__(self) -> str: ...

    def cleanup(self) -> None: ...


class _StageProvider(Protocol):
    def __call__(self) -> tuple[str, bytes]: ...


@dataclass(frozen=True, slots=True, repr=False)
class _CommandPlan(Generic[T_co]):
    config_snapshot: ClientConfig
    transport: CliTransport
    steps: tuple[_Step, ...]
    finalize: Callable[[tuple[object, ...]], T_co]
    _temp_provider: _TempProvider | None = None
    _stage_provider: _StageProvider | None = None
    _capture_output_label: str | None = None
    _run_override: Callable[[], T_co] | None = None
    _step_gate: Callable[[int, tuple[object, ...]], bool] | None = None
    _step_continuation: Callable[[int, tuple[object, ...]], _Step | None] | None = None

    def render(self) -> tuple[str, ...]:
        rendered: list[str] = []
        for step in self.steps:
            argv = list(step.argv)
            for position, ref in step.refs:
                argv[position] = _display_ref(ref)
            full_argv = self.transport.build_full_argv(tuple(argv))
            environment = _effective_environment(self.config_snapshot)
            secret_values = collect_diagnostic_secret_values(
                full_argv,
                environment,
                stdin=step.stdin,
                include_file_contents=False,
            )
            rendered.append(
                shlex.join(redact_diagnostic_argv(full_argv, secret_values=secret_values))
            )
        return tuple(rendered)

    def run(self) -> T_co:
        if self._run_override is not None:
            try:
                return self._run_override()
            finally:
                _cleanup_temp_provider(self._temp_provider)
        if not self.steps:
            return self.finalize(())

        with ExitStack() as staged_paths:
            results: list[object] = []
            steps = list(self.steps)
            staged_path: str | None = None
            output_artifact: OutputArtifact | None = None
            index = 0
            try:
                while index < len(steps):
                    if self._step_gate is not None and not self._step_gate(index, tuple(results)):
                        break
                    step = steps[index]
                    argv = list(step.argv)
                    for position, ref in step.refs:
                        resolved, staged_path, output_artifact = self._resolve_ref(
                            ref, results, steps, staged_paths, staged_path, output_artifact
                        )
                        argv[position] = resolved
                    results.append(self._run_step(step, tuple(argv)))
                    if self._step_continuation is not None:
                        next_step = self._step_continuation(index, tuple(results))
                        if next_step is not None:
                            steps.append(next_step)
                    index += 1
                if output_artifact is not None:
                    results.append(output_artifact)
                return self.finalize(tuple(results))
            finally:
                _cleanup_temp_provider(self._temp_provider)

    def _run_step(self, step: _Step, argv: tuple[str, ...]) -> object:
        if step.mode == "run_bytes":
            raw_result = self.transport.run_bytes(argv, stdin=step.stdin, timeout=step.timeout)
            if step.decode is None:
                return raw_result
            return step.decode(raw_result.stdout, " ".join(raw_result.argv))
        if step.mode == "run_text":
            if step.stdin is None and step.timeout is None:
                text_result = self.transport.run_text(argv)
            else:
                text_result = self.transport.run_text(argv, stdin=step.stdin, timeout=step.timeout)
            if step.decode is None:
                return text_result
            return step.decode(text_result.text.encode("utf-8"), " ".join(argv))
        return self.transport.spawn(argv)

    def _resolve_ref(
        self,
        ref: _StepRef,
        results: list[object],
        steps: list[_Step],
        staged_paths: ExitStack,
        staged_path: str | None,
        output_artifact: OutputArtifact | None,
    ) -> tuple[str, str | None, OutputArtifact | None]:
        if ref.kind == "output":
            if self._capture_output_label is not None:
                if output_artifact is None:
                    output_artifact = staged_paths.enter_context(
                        self.transport.executor.capture_output(self._capture_output_label)
                    )
                return output_artifact.path, staged_path, output_artifact
            raise RuntimeError("command plan has an output reference without a provider")
        if ref.kind == "temp":
            if self._stage_provider is not None:
                if staged_path is None:
                    label, content = self._stage_provider()
                    staged_path = staged_paths.enter_context(
                        self.transport.executor.stage(label, content)
                    )
                return staged_path, staged_path, output_artifact
            if self._temp_provider is None:
                raise RuntimeError("command plan has a temp reference without a provider")
            return self._temp_provider(), staged_path, output_artifact

        if ref.alias is None:
            raise RuntimeError("result reference has no result alias")
        for index in range(len(steps) - 1, -1, -1):
            if steps[index].result_alias == ref.alias:
                if index >= len(results):
                    continue
                return _result_field(results[index], ref.field), staged_path, output_artifact
        raise RuntimeError(f"unknown result reference {ref.alias!r}")


_KEEP_RUN_OVERRIDE = object()


def _replace_plan(
    plan: _CommandPlan[object],
    *,
    finalize: Callable[[tuple[object, ...]], T_plan],
    steps: tuple[_Step, ...] | None = None,
    run_override: Callable[[], T_plan] | None | object = _KEEP_RUN_OVERRIDE,
    step_gate: Callable[[int, tuple[object, ...]], bool] | None = None,
    step_continuation: Callable[[int, tuple[object, ...]], _Step | None] | None = None,
) -> _CommandPlan[T_plan]:
    next_run_override = (
        cast("Callable[[], T_plan] | None", plan._run_override)
        if run_override is _KEEP_RUN_OVERRIDE
        else cast("Callable[[], T_plan] | None", run_override)
    )
    return cast(
        "_CommandPlan[T_plan]",
        replace(
            plan,
            steps=plan.steps if steps is None else steps,
            finalize=finalize,
            _run_override=next_run_override,
            _step_gate=plan._step_gate if step_gate is None else step_gate,
            _step_continuation=(
                plan._step_continuation if step_continuation is None else step_continuation
            ),
        ),
    )


class Command(Generic[T_co]):
    __slots__ = ("_plan",)

    def __init__(self, plan: _CommandPlan[T_co]) -> None:
        self._plan = plan

    @property
    def commands(self) -> tuple[str, ...]:
        return self._plan.render()

    def run(self) -> T_co:
        return self._plan.run()

    def _map(self, mapper: Callable[[T_co], T_mapped]) -> Command[T_mapped]:
        plan = self._plan
        override = plan._run_override

        def run_override() -> T_mapped:
            if override is None:
                raise RuntimeError("command has no run override")
            return mapper(override())

        return Command(
            _replace_plan(
                plan,
                finalize=lambda results: mapper(plan.finalize(results)),
                run_override=run_override if override is not None else None,
            )
        )

    def __repr__(self) -> str:
        return f"Command(commands={self.commands!r})"


def _cached_value_command(value: Callable[[], T_result]) -> Command[T_result]:
    """Build a no-step command for a value known without a client."""
    config = ClientConfig()
    return Command(
        _CommandPlan(
            config_snapshot=config,
            transport=CliTransport(config),
            steps=(),
            finalize=lambda _results: value(),
        )
    )


def _cached_result_command(
    command: Command[T_source], result: Callable[[], T_result]
) -> Command[T_result]:
    """Return a no-step command retaining the source snapshot and diagnostics."""
    plan = command._plan
    return Command(
        _replace_plan(
            plan,
            steps=(),
            finalize=lambda _results: result(),
            run_override=None,
        )
    )


def _coalesced_command(
    command: Command[T_source],
    run: Callable[[], T_result],
    *,
    finalize: Callable[[T_source], T_result] | None = None,
) -> Command[T_result]:
    """Replace execution while retaining the source command's plan snapshot."""
    plan = command._plan
    map_result = finalize or cast("Callable[[T_source], T_result]", lambda value: value)
    return Command(
        _replace_plan(
            plan,
            finalize=lambda results: map_result(plan.finalize(results)),
            run_override=run,
        )
    )


def _require_single_step(plan: _CommandPlan[object]) -> _Step:
    if len(plan.steps) != 1:
        raise ValueError("command transformation requires exactly one step")
    return plan.steps[0]


def _result_field_argument(
    command: Command[T_co],
    *,
    flag: str,
    field: str,
    alias: str = "result",
    require_existing: bool = False,
) -> Command[T_co]:
    """Bind an existing or inserted flag to a single-step result field."""
    plan = command._plan
    step = _require_single_step(plan)
    argv = list(step.argv)
    if flag in argv:
        position = argv.index(flag) + 1
        if position >= len(argv):
            raise ValueError(f"flag {flag!r} has no value")
        argv[position] = f"${{{alias}.{field}}}"
    else:
        if require_existing:
            raise ValueError(f"command has no {flag} argument")
        try:
            output_position = argv.index("--output")
        except ValueError as error:
            raise ValueError(f"cannot insert result field {flag!r} without --output") from error
        position = output_position
        argv[position:position] = [flag, f"${{{alias}.{field}}}"]
    refs = tuple(
        (*step.refs, (position + 1, _StepRef("result", field=field, alias=alias)))
        if flag not in step.argv
        else (*step.refs, (position, _StepRef("result", field=field, alias=alias)))
    )
    return Command(
        _replace_plan(
            plan,
            steps=(replace(step, argv=tuple(argv), refs=refs, result_alias=alias),),
            finalize=plan.finalize,
        )
    )


def _sequential_command(
    command: Command[T_source],
    template: Command[object],
    *,
    gate: Callable[[int, tuple[object, ...]], bool] | None = None,
    continuation: Callable[[int, tuple[object, ...]], bool] | None = None,
    finalize: Callable[[tuple[object, ...]], T_result],
) -> Command[T_result]:
    """Build a two-step sequential command from an aliased single-step source."""
    plan = command._plan
    first = _require_single_step(plan)
    template_step = _require_single_step(template._plan)
    alias = template_step.result_alias or "result"

    def next_step(index: int, results: tuple[object, ...]) -> _Step | None:
        if continuation is None or not continuation(index, results):
            return None
        return template_step

    return Command(
        _replace_plan(
            plan,
            steps=(replace(first, result_alias=alias), template_step),
            finalize=finalize,
            step_gate=gate,
            step_continuation=next_step,
        )
    )


def _display_ref(ref: _StepRef) -> str:
    if ref.kind in {"temp", "output"}:
        return "${temp.path}"
    alias = ref.alias or "result"
    field = ref.field or "value"
    return f"${{{alias}.{field}}}"


def _cleanup_temp_provider(provider: _TempProvider | None) -> None:
    if provider is None:
        return
    provider.cleanup()


def _is_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


def _result_field(value: object, field: str | None) -> str:
    if field is None:
        raise RuntimeError("result reference has no field")
    resolved: object = value
    for part in field.split("."):
        resolved = (
            resolved.get(part) if _is_mapping(resolved) else cast("object", getattr(resolved, part))
        )
    if resolved is None:
        raise RuntimeError(f"result field {field!r} is missing")
    return str(resolved)

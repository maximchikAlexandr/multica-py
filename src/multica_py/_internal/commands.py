from __future__ import annotations

import datetime
import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Generic, Literal, Protocol, TypeGuard, TypeVar, cast

from multica_py._internal.redaction import redact_argv
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig

__all__ = ["Command"]

T_co = TypeVar("T_co", covariant=True)
T_plan = TypeVar("T_plan")
T_mapped = TypeVar("T_mapped")

_StepMode = Literal["run_bytes", "run_text", "spawn"]


@dataclass(frozen=True, slots=True)
class _StepRef:
    kind: Literal["result", "temp"]
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


@dataclass(frozen=True, slots=True, repr=False)
class _CommandPlan(Generic[T_co]):
    config_snapshot: ClientConfig
    transport: CliTransport
    steps: tuple[_Step, ...]
    finalize: Callable[[tuple[object, ...]], T_co]
    _temp_provider: _TempProvider | None = None
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
            rendered.append(shlex.join(redact_argv(full_argv)))
        return tuple(rendered)

    def run(self) -> T_co:
        if self._run_override is not None:
            return self._run_override()
        if not self.steps:
            return self.finalize(())

        results: list[object] = []
        steps = list(self.steps)
        try:
            index = 0
            while index < len(steps):
                if self._step_gate is not None and not self._step_gate(index, tuple(results)):
                    break
                step = steps[index]
                argv = list(step.argv)
                for position, ref in step.refs:
                    argv[position] = self._resolve_ref(ref, results, steps)
                results.append(self._run_step(step, tuple(argv)))
                if self._step_continuation is not None:
                    next_step = self._step_continuation(index, tuple(results))
                    if next_step is not None:
                        steps.append(next_step)
                index += 1
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
            return step.decode(
                text_result.text.encode(self.config_snapshot.encoding), " ".join(argv)
            )
        return self.transport.spawn(argv)

    def _resolve_ref(self, ref: _StepRef, results: list[object], steps: list[_Step]) -> str:
        if ref.kind == "temp":
            if self._temp_provider is None:
                raise RuntimeError("command plan has a temp reference without a provider")
            return self._temp_provider()

        if ref.alias is None:
            raise RuntimeError("result reference has no result alias")
        for index in range(len(steps) - 1, -1, -1):
            if steps[index].result_alias == ref.alias:
                if index >= len(results):
                    continue
                return _result_field(results[index], ref.field)
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


def _display_ref(ref: _StepRef) -> str:
    if ref.kind == "temp":
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

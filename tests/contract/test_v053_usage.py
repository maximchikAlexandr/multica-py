from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import _task_run_from_wire, _TaskRunWire
from multica_py.models.issue_activity import IssueUsage, TaskUsageData
from multica_py.models.system import RuntimeUsage

_FIXTURE = cast(
    "dict[str, object]",
    json.loads((Path(__file__).parents[1] / "fixtures/provenance/usage_v053.json").read_text()),
)


@dataclass(frozen=True)
class TaskUsageCase:
    case_id: str
    payload: dict[str, object]
    expected: tuple[TaskUsageData, ...]


def _task_usage_rows(value: object) -> tuple[TaskUsageData, ...]:
    rows = cast("list[object]", value)
    return tuple(
        TaskUsageData(
            provider=cast("str", row["provider"]),
            model=cast("str", row["model"]),
            input_tokens=cast("int", row["input_tokens"]),
            output_tokens=cast("int", row["output_tokens"]),
            cache_read_tokens=cast("int", row["cache_read_tokens"]),
            cache_write_tokens=cast("int", row["cache_write_tokens"]),
            cost_usd_ticks=cast("int | None", row.get("cost_usd_ticks")),
        )
        for row in (cast("dict[str, object]", item) for item in rows)
    )


def _case_id(case: TaskUsageCase) -> str:
    return case.case_id


TASK_USAGE_CASES = tuple(
    TaskUsageCase(
        case_id=cast("str", row["id"]),
        payload=cast("dict[str, object]", row["payload"]),
        expected=_task_usage_rows(row["expected"]),
    )
    for row in cast("list[dict[str, object]]", _FIXTURE["task_runs"])
)


@pytest.mark.parametrize("case", TASK_USAGE_CASES, ids=_case_id)
def test_target_task_usage_values_are_preserved_without_sdk_arithmetic(case: TaskUsageCase) -> None:
    wire = decode_json(json.dumps(case.payload).encode(), _TaskRunWire)
    run = _task_run_from_wire(wire, issue_id="issue-1")
    assert run.usage == case.expected


def test_target_issue_usage_aggregate_is_preserved() -> None:
    usage = decode_json(json.dumps(_FIXTURE["issue_usage"]).encode(), IssueUsage)
    assert (usage.total_runs, usage.task_count) == (7, 7)
    assert (
        usage.total_input_tokens,
        usage.total_output_tokens,
        usage.total_cache_read_tokens,
        usage.total_cache_write_tokens,
        usage.cost_usd_ticks,
    ) == (253, 93, 18, 4, 12345)


def test_target_runtime_usage_aggregate_is_preserved() -> None:
    usage = decode_json(json.dumps(_FIXTURE["runtime_usage"]).encode(), RuntimeUsage)
    assert (
        usage.provider,
        usage.model,
        usage.input_tokens,
        usage.output_tokens,
        usage.cache_read_tokens,
        usage.cache_write_tokens,
    ) == ("anthropic", "claude-opus", 120, 30, 8, 2)

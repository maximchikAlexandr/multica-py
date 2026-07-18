from __future__ import annotations

import pytest

from tests.live.resource_registry import ResourceAbsentError, ResourceRegistry


def test_cleanup_runs_in_reverse_registration_order() -> None:
    order: list[str] = []
    registry = ResourceRegistry()
    registry.defer(key="project", cleanup=lambda: order.append("project"))
    registry.defer(key="issue", cleanup=lambda: order.append("issue"))
    registry.cleanup_all()
    assert order == ["issue", "project"]


def test_already_absent_is_tolerated() -> None:
    registry = ResourceRegistry()
    registry.defer(
        key="label",
        cleanup=lambda: (_ for _ in ()).throw(ResourceAbsentError()),
    )
    assert registry.cleanup_all() == []


def test_partial_failure_is_recorded() -> None:
    registry = ResourceRegistry()
    registry.defer(
        key="a",
        cleanup=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    failures = registry.cleanup_all()
    assert len(failures) == 1
    assert failures[0]["key"] == "a"

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingCase:
    id: str
    operation_id: str


ROUTING_CASES: tuple[RoutingCase, ...] = (
    RoutingCase("top-level", "manual:agents.list:canonical"),
    RoutingCase("issue-comments", "generated:issues.comments.list:direct:canonical"),
    RoutingCase("project-resources", "generated:projects.resources.list:default:canonical"),
    RoutingCase("skill-files", "manual:skills.files.list:canonical"),
)

from __future__ import annotations

import datetime
from typing import TypeVar

import msgspec

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.entities._base import _BoundEntity
from multica_py.entities.issues import Issue
from multica_py.models.agents import AgentSkill, AgentTask
from multica_py.models.common import ActionResult, Page
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage

S = TypeVar("S", bound=msgspec.Struct)


def _page_items(value: Page[S] | tuple[S, ...]) -> tuple[S, ...]:
    return value.items if isinstance(value, Page) else value


class Agent(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    description: str | None = None
    skill_refs: tuple[AgentSkill, ...] = msgspec.field(default_factory=tuple, name="skills")
    archived_at: datetime.datetime | None = None

    _skills: LazyCollection[AgentSkill] | None = msgspec.field(default=None, name="_skills")
    _tasks: LazyCollection[AgentTask] | None = msgspec.field(default=None, name="_tasks")
    _issues: OffsetLazyCollection[Issue] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "description", "skill_refs", "archived_at")

    @property
    def skills(self) -> LazyCollection[AgentSkill]:
        if self._skills is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="skills"
            )
            aid = self.id
            skills = client.agents.skills
            self._set_runtime(
                "_skills",
                LazyCollection(
                    lambda: _page_items(skills.list(aid)),
                    command_loader=lambda: client.agents._skills_relation_command(aid),
                ),
            )
        return self._skills  # type: ignore[return-value]

    @property
    def tasks(self) -> LazyCollection[AgentTask]:
        if self._tasks is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="tasks"
            )
            aid = self.id
            agents = client.agents
            self._set_runtime(
                "_tasks",
                LazyCollection(
                    lambda: agents.tasks(aid),
                    command_loader=lambda: client.agents._tasks_relation_command(aid),
                ),
            )
        return self._tasks  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[Issue]:
        if self._issues is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="issues"
            )
            aid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:
                from multica_py.models.issues import IssueListFilter

                issue_filter = IssueListFilter(assignee_id=aid, limit=limit, offset=offset)
                return client.issues._offset_page(issue_filter)

            def page_command_loader(limit: int | None, offset: int) -> Command[OffsetPage[Issue]]:
                from multica_py.models.issues import IssueListFilter

                issue_filter = IssueListFilter(assignee_id=aid, limit=limit, offset=offset)
                return client.issues._offset_page_command(issue_filter)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=page_command_loader,
                ),
            )
        return self._issues  # type: ignore[return-value]

    def _invalidate_skills(self) -> None:
        if self._skills is not None:
            self._skills.invalidate()

    def set_skills(
        self, skill_ids: tuple[str, ...], *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        """Set the agent's assigned skills and invalidate cached skills cache."""
        return self.set_skills_command(skill_ids, options=options).run()

    def set_skills_command(
        self, skill_ids: tuple[str, ...], *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        """Build a lazy command to set skills and invalidate the cache on success."""
        client = self._require_client(
            entity_type="Agent", entity_id=self.id, relation_name="set_skills"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_skills()
            return result

        return client.agents._set_skills_command(
            self.id, skill_ids, invalidate=invalidate, options=options
        )

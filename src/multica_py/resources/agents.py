from __future__ import annotations

import datetime
import pathlib
from typing import TYPE_CHECKING, overload

import msgspec

from multica_py._generated.approved_sdk import AGENT_AVATAR_BINDING, validate_nonblank
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models._bound import _BoundEntity
from multica_py.models.agents import (
    AgentCreateRequest,
    AgentSkill,
    AgentTask,
    AgentUpdateRequest,
)
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.resources.issues import _issue_summary_offset_page

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _page_agent_issues(
    client: MulticaClient, agent_id: str, limit: int | None, offset: int
) -> OffsetPage[IssueSummary]:

    flt = IssueListFilter(
        assignee_id=agent_id,
        limit=limit,
        offset=offset,
    )
    return _issue_summary_offset_page(client.issues, flt)


class Agent(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    description: str | None = None
    skill_refs: tuple[AgentSkill, ...] = msgspec.field(default_factory=tuple, name="skills")
    archived_at: datetime.datetime | None = None

    _skills: LazyCollection[AgentSkill] | None = msgspec.field(default=None, name="_skills")
    _tasks: LazyCollection[AgentTask] | None = msgspec.field(default=None, name="_tasks")
    _issues: OffsetLazyCollection[IssueSummary] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "description", "skill_refs", "archived_at")

    @property
    def skills(self) -> LazyCollection[AgentSkill]:
        if self._skills is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="skills"
            )
            aid = self.id
            skills = client.agents.skills

            self._set_runtime("_skills", LazyCollection(lambda: skills.list(aid)))
        return self._skills  # type: ignore[return-value]

    @property
    def tasks(self) -> LazyCollection[AgentTask]:
        if self._tasks is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="tasks"
            )
            aid = self.id
            agents = client.agents

            self._set_runtime("_tasks", LazyCollection(lambda: agents.tasks(aid)))
        return self._tasks  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="issues"
            )
            aid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return _page_agent_issues(client, aid, limit, offset)

            self._set_runtime("_issues", OffsetLazyCollection(page_loader))
        return self._issues  # type: ignore[return-value]

    def _invalidate_skills(self) -> None:
        if self._skills is not None:
            self._skills.invalidate()

    def set_skills(self, skill_ids: tuple[str, ...]) -> None:
        """Set the agent's assigned skills and invalidate cached skills cache."""
        client = self._require_client(
            entity_type="Agent", entity_id=self.id, relation_name="set_skills"
        )
        agent_skills = client.agents.skills
        agent_skills.set(self.id, skill_ids)
        self._invalidate_skills()


class AgentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.skills = AgentSkillResource(transport, config)

    def list(self) -> tuple[Agent, ...]:
        items = self._run_json_decode_list(("agent", "list"), Agent)
        return tuple(a._with_client(self._client) for a in items)

    def get(self, agent_id: str) -> Agent:
        validate_nonblank(agent_id)
        a = self._run_json_decode(("agent", "get", agent_id), Agent)
        return a._with_client(self._client)

    @overload
    def create(self, request: AgentCreateRequest, /) -> Agent: ...
    @overload
    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        runtime_id: str | None = None,
        model: str | None = None,
    ) -> Agent: ...

    def create(self, request: AgentCreateRequest | None = None, /, **kwargs: object) -> Agent:  # type: ignore[misc]
        req = _resolve_request(request, kwargs, AgentCreateRequest)
        validate_nonblank(req.name)
        args = ["agent", "create", "--name", req.name]
        if req.description is not None:
            args.extend(["--description", req.description])
        if req.runtime_id is not None:
            args.extend(["--runtime-id", req.runtime_id])
        if req.model is not None:
            args.extend(["--model", req.model])
        a = self._run_json_decode(tuple(args), Agent)
        return a._with_client(self._client)

    @overload
    def update(self, agent_id: str, request: AgentUpdateRequest, /) -> Agent: ...
    @overload
    def update(
        self, agent_id: str, *, name: str | None = None, description: str | None = None
    ) -> Agent: ...

    def update(  # type: ignore[misc]
        self, agent_id: str, request: AgentUpdateRequest | None = None, /, **kwargs: object
    ) -> Agent:
        validate_nonblank(agent_id)
        req = _resolve_request(request, kwargs, AgentUpdateRequest)
        args = ["agent", "update", agent_id]
        if req.name is not None:
            args.extend(["--name", req.name])
        if req.description is not None:
            args.extend(["--description", req.description])
        a = self._run_json_decode(tuple(args), Agent)
        return a._with_client(self._client)

    def archive(self, agent_id: str) -> None:
        validate_nonblank(agent_id)
        self._transport.run_text(("agent", "archive", agent_id))

    def restore(self, agent_id: str) -> None:
        validate_nonblank(agent_id)
        self._transport.run_text(("agent", "restore", agent_id))

    def tasks(self, agent_id: str) -> tuple[AgentTask, ...]:
        validate_nonblank(agent_id)
        return self._run_json_decode_list(("agent", "tasks", agent_id), AgentTask)

    def avatar(self, agent_id: str, file: pathlib.Path) -> None:
        _ = AGENT_AVATAR_BINDING
        validate_nonblank(agent_id)
        path = file.resolve()
        if not path.is_file():
            raise ValueError(f"file must be an existing local file: {file}")
        self._transport.run_text(("agent", "avatar", agent_id, "--file", str(path)))

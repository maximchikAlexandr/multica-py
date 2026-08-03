from __future__ import annotations

import datetime
import pathlib
from typing import TYPE_CHECKING, overload

from multica_py._generated.approved_sdk import AGENT_AVATAR_BINDING, validate_nonblank
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models import ResourceEntity
from multica_py.models.agents import (
    Agent,
    AgentCreateRequest,
    AgentData,
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


class AgentEntity(ResourceEntity[AgentData]):
    def __init__(self, data: AgentData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._skills: LazyCollection[AgentSkill] | None = None
        self._tasks: LazyCollection[AgentTask] | None = None
        self._issues: OffsetLazyCollection[IssueSummary] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def description(self) -> str | None:
        return self._data.description

    @property
    def archived_at(self) -> datetime.datetime | None:
        return self._data.archived_at

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="AgentEntity", entity_id=self._data.id, relation_name=relation_name
        )

    @property
    def skills(self) -> LazyCollection[AgentSkill]:
        if self._skills is None:
            client = self._check_client("skills")
            aid = self._data.id
            skills = client.agents.skills

            self._skills = LazyCollection(lambda: skills.list(aid))
        return self._skills

    @property
    def tasks(self) -> LazyCollection[AgentTask]:
        if self._tasks is None:
            client = self._check_client("tasks")
            aid = self._data.id
            agents = client.agents

            self._tasks = LazyCollection(lambda: agents.tasks(aid))
        return self._tasks

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._check_client("issues")
            aid = self._data.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return _page_agent_issues(client, aid, limit, offset)

            self._issues = OffsetLazyCollection(page_loader)
        return self._issues

    def _invalidate_skills(self) -> None:
        if self._skills is not None:
            self._skills.invalidate()

    def set_skills(self, skill_ids: tuple[str, ...]) -> None:
        """Set the agent's assigned skills and invalidate cached skills cache."""
        client = self._check_client("set_skills")
        agent_skills = client.agents.skills
        agent_skills.set(self._data.id, skill_ids)
        self._invalidate_skills()


class AgentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.skills = AgentSkillResource(transport, config)

    def list(self) -> tuple[AgentEntity, ...]:
        items = self._run_json_decode_list(("agent", "list"), Agent)
        return tuple(self._bind_agent(a) for a in items)

    def get(self, agent_id: str) -> AgentEntity:
        validate_nonblank(agent_id)
        a = self._run_json_decode(("agent", "get", agent_id), Agent)
        return self._bind_agent(a)

    def _bind_agent(self, a: Agent) -> AgentEntity:
        data = AgentData(
            id=a.id,
            name=a.name,
            description=a.description,
            skill_refs=a.skills,
            archived_at=a.archived_at,
        )
        return AgentEntity(data, client=self._client)

    @overload
    def create(self, request: AgentCreateRequest, /) -> AgentEntity: ...
    @overload
    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        runtime_id: str | None = None,
        model: str | None = None,
    ) -> AgentEntity: ...

    def create(self, request: AgentCreateRequest | None = None, /, **kwargs: object) -> AgentEntity:  # type: ignore[misc]
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
        return self._bind_agent(a)

    @overload
    def update(self, agent_id: str, request: AgentUpdateRequest, /) -> AgentEntity: ...
    @overload
    def update(
        self, agent_id: str, *, name: str | None = None, description: str | None = None
    ) -> AgentEntity: ...

    def update(  # type: ignore[misc]
        self, agent_id: str, request: AgentUpdateRequest | None = None, /, **kwargs: object
    ) -> AgentEntity:
        validate_nonblank(agent_id)
        req = _resolve_request(request, kwargs, AgentUpdateRequest)
        args = ["agent", "update", agent_id]
        if req.name is not None:
            args.extend(["--name", req.name])
        if req.description is not None:
            args.extend(["--description", req.description])
        a = self._run_json_decode(tuple(args), Agent)
        return self._bind_agent(a)

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

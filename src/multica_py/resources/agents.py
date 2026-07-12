from __future__ import annotations

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.agents import Agent, AgentCreateRequest, AgentTask, AgentUpdateRequest
from multica_py.resources._base import BaseResource
from multica_py.resources.agent_skills import AgentSkillResource


class AgentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.skills = AgentSkillResource(transport, config)

    def list(self) -> tuple[Agent, ...]:
        return self._run_json_decode_list(("agent", "list"), Agent)

    def get(self, agent_id: str) -> Agent:
        return self._run_json_decode(("agent", "get", agent_id), Agent)

    def create(self, request: AgentCreateRequest) -> Agent:
        args = ["agent", "create", "--name", request.name]
        if request.description is not None:
            args.extend(["--description", request.description])
        return self._run_json_decode(tuple(args), Agent)

    def update(self, agent_id: str, request: AgentUpdateRequest) -> Agent:
        args = ["agent", "update", agent_id]
        if request.name is not None:
            args.extend(["--name", request.name])
        if request.description is not None:
            args.extend(["--description", request.description])
        return self._run_json_decode(tuple(args), Agent)

    def archive(self, agent_id: str) -> None:
        self._transport.run_text(("agent", "archive", agent_id))

    def restore(self, agent_id: str) -> None:
        self._transport.run_text(("agent", "restore", agent_id))

    def tasks(self, agent_id: str) -> tuple[AgentTask, ...]:
        return self._run_json_decode_list(("agent", "tasks", agent_id), AgentTask)

    def upload_avatar(self, agent_id: str, image_path: str) -> None:
        self._transport.run_text(("agent", "avatar", "upload", agent_id, "--image", image_path))

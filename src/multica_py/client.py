from __future__ import annotations

import datetime
import pathlib
from collections.abc import Mapping

import msgspec

from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.resources.agents import AgentResource
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.configuration import ConfigurationResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.maintenance import MaintenanceResource
from multica_py.resources.projects import ProjectResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.setup import SetupResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.users import UserResource
from multica_py.resources.workspaces import WorkspaceResource


class MulticaClient:
    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        self._semaphore = ProcessSemaphore(config.max_processes)
        self._transport = CliTransport(config, semaphore=self._semaphore)

        self.auth = AuthResource(self._transport, config)
        self.setup = SetupResource(self._transport, config)
        self.daemon = DaemonResource(self._transport, config)
        self.workspaces = WorkspaceResource(self._transport, config)
        self.issues = IssueResource(self._transport, config)
        self.projects = ProjectResource(self._transport, config)
        self.labels = LabelResource(self._transport, config)
        self.agents = AgentResource(self._transport, config)
        self.skills = SkillResource(self._transport, config)
        self.autopilots = AutopilotResource(self._transport, config)
        self.repositories = RepositoryResource(self._transport, config)
        self.runtimes = RuntimeResource(self._transport, config)
        self.attachments = AttachmentResource(self._transport, config)
        self.configuration = ConfigurationResource(self._transport, config)
        self.squads = SquadResource(self._transport, config)
        self.users = UserResource(self._transport, config)
        self.maintenance = MaintenanceResource(self._transport, config)

    @property
    def config(self) -> ClientConfig:
        return self._config

    def _replace_config(self, **changes: object) -> ClientConfig:
        return msgspec.structs.replace(self._config, **changes)

    def with_profile(self, profile: str | None) -> MulticaClient:
        return MulticaClient(self._replace_config(profile=profile))

    def with_workspace(self, workspace_id: str | None) -> MulticaClient:
        return MulticaClient(self._replace_config(workspace_id=workspace_id))

    def with_timeout(self, timeout: datetime.timedelta | None) -> MulticaClient:
        return MulticaClient(self._replace_config(timeout=timeout))

    def with_cwd(self, cwd: pathlib.Path | None) -> MulticaClient:
        return MulticaClient(self._replace_config(cwd=cwd))

    def with_environment(
        self,
        environment: Mapping[str, str] | tuple[tuple[str, str], ...],
    ) -> MulticaClient:
        normalized = (
            tuple(sorted(environment.items())) if isinstance(environment, Mapping) else environment
        )
        return MulticaClient(self._replace_config(environment=normalized))

    def __enter__(self) -> MulticaClient:
        return self

    def __exit__(self, *args: object) -> None:
        self._transport.close()

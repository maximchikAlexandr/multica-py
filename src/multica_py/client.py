from __future__ import annotations

import datetime
import os
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor, as_completed
from typing import TypeVar, cast

from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions, _apply_operation_options
from multica_py.entities._base import _BoundEntity
from multica_py.exceptions import DetachedEntityError
from multica_py.execution import CommandExecutor, LocalExecutor
from multica_py.models.relations import LazyCollection, LazyLoadable, LazyMapping, LazyRef
from multica_py.resources.agents import AgentResource
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.cli import CliResource
from multica_py.resources.configuration import ConfigurationResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.maintenance import MaintenanceResource
from multica_py.resources.plugins import PluginResource
from multica_py.resources.projects import ProjectResource
from multica_py.resources.properties import PropertyResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.setup import SetupResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.users import UserResource
from multica_py.resources.workspaces import WorkspaceResource
from multica_py.sentinels import Unset, UnsetType

TEntity = TypeVar("TEntity", bound=_BoundEntity)
TRelationValue_co = TypeVar("TRelationValue_co", covariant=True)


class MulticaClient:
    def __init__(
        self,
        config: ClientConfig | None = None,
        *,
        executor: CommandExecutor | None = None,
        _semaphore: ProcessSemaphore | None = None,
    ) -> None:
        if config is None:
            config = ClientConfig()
        self._config = config
        self._semaphore = _semaphore or ProcessSemaphore(config.max_processes)
        self._executor = LocalExecutor() if executor is None else executor
        self._owns_executor = executor is None
        self._closed = False
        self._transport = CliTransport(config, semaphore=self._semaphore, executor=self._executor)

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
        self.cli = CliResource(self._transport, config)
        self.configuration = ConfigurationResource(self._transport, config)
        self.squads = SquadResource(self._transport, config)
        self.users = UserResource(self._transport, config)
        self.maintenance = MaintenanceResource(self._transport, config)
        self.plugins = PluginResource(self._transport, config)
        self.properties = PropertyResource(self._transport, config)
        for r in (
            self.auth,
            self.setup,
            self.daemon,
            self.workspaces,
            self.issues,
            self.projects,
            self.labels,
            self.agents,
            self.skills,
            self.autopilots,
            self.repositories,
            self.runtimes,
            self.attachments,
            self.cli,
            self.configuration,
            self.squads,
            self.users,
            self.maintenance,
            self.plugins,
            self.properties,
        ):
            r._set_client(self)

    @property
    def config(self) -> ClientConfig:
        return self._config

    def with_options(
        self,
        *,
        profile: str | None | UnsetType = Unset,
        workspace_id: str | None | UnsetType = Unset,
        timeout: datetime.timedelta | float | None | UnsetType = Unset,
        cwd: str | os.PathLike[str] | None | UnsetType = Unset,
        environment: Mapping[str, str] | tuple[tuple[str, str], ...] | UnsetType = Unset,
    ) -> MulticaClient:
        options = OperationOptions(
            profile=profile,
            workspace_id=workspace_id,
            timeout=timeout,
            cwd=cwd,
            environment=environment,
        )
        return MulticaClient(
            _apply_operation_options(self._config, options),
            executor=self._executor,
            _semaphore=self._semaphore,
        )

    def with_profile(self, profile: str | None) -> MulticaClient:
        return self.with_options(profile=profile)

    def with_workspace(self, workspace_id: str | None) -> MulticaClient:
        return self.with_options(workspace_id=workspace_id)

    def with_timeout(
        self,
        timeout: datetime.timedelta | float | None,
    ) -> MulticaClient:
        return self.with_options(timeout=timeout)

    def with_cwd(self, cwd: str | os.PathLike[str] | None) -> MulticaClient:
        return self.with_options(cwd=cwd)

    def with_environment(
        self,
        environment: Mapping[str, str] | tuple[tuple[str, str], ...],
    ) -> MulticaClient:
        """Return a scoped client whose environment is **replaced**, not merged.

        Pass the full set of variables you want the scoped client to use;
        variables configured on the parent are dropped unless repeated here.
        Use an empty mapping/tuple to explicitly clear the environment.
        """
        return self.with_options(environment=environment)

    def _singular_scope_key(self, target_type: str, target_id: str) -> tuple[object, ...]:
        config = self._config
        cwd = None if config.cwd is None else os.fspath(config.cwd)
        return (
            os.fspath(config.executable),
            config.server_url,
            config.profile,
            config.workspace_id,
            cwd,
            tuple(config.environment),
            config.timeout,
            config.debug,
            config.compatibility,
            config.min_cli_version,
            config.max_cli_version,
            id(self._executor),
            id(self._semaphore),
            target_type,
            target_id,
        )

    def prefetch(
        self,
        entities: Iterable[TEntity],
        selector: Callable[[TEntity], LazyLoadable[TRelationValue_co] | LazyRef[object]],
        *,
        max_parallel: int = 4,
    ) -> None:
        """Load selected relations concurrently for the given entities.

        Detached entities raise ``DetachedEntityError``. Concurrent load
        failures raise only the lowest-index error; that single-exception
        surface is the supported public contract.
        """
        if max_parallel < 1:
            raise ValueError("max_parallel must be at least 1")

        entity_values = tuple(entities)
        jobs: list[tuple[int, Callable[[], object]]] = []
        job_specs: list[LazyLoadable[object] | list[LazyRef[object]]] = []
        collection_ids: set[int] = set()
        singular_jobs: dict[tuple[object, ...], list[LazyRef[object]]] = {}
        for entity in entity_values:
            origin = entity._client
            if origin is None:
                raise DetachedEntityError(
                    type(entity).__name__, cast("str", getattr(entity, "id")), "prefetch"
                )
            if cast("object | None", getattr(origin, "_semaphore", None)) is not self._semaphore:
                raise ValueError("entities must share an origin scope")
            selected: object = selector(entity)
            if not isinstance(selected, (LazyRef, LazyCollection, LazyMapping)):
                raise ValueError("selector must return LazyRef, LazyCollection, or LazyMapping")
            if selected.loaded:
                continue
            if isinstance(selected, LazyRef):
                singular = selected
                key = singular._prefetch_key()
                destinations = singular_jobs.get(key)
                if destinations is None:
                    destinations = [singular]
                    singular_jobs[key] = destinations
                    job_specs.append(destinations)
                elif not any(destination is singular for destination in destinations):
                    destinations.append(singular)
                continue
            relation = cast("LazyLoadable[object]", selected)
            relation_id = id(relation)
            if relation_id in collection_ids:
                continue
            collection_ids.add(relation_id)
            job_specs.append(relation)
        failures: dict[int, Exception] = {}
        futures: dict[Future[object], int] = {}
        reserved_targets: list[tuple[LazyRef[object], int | None]] = []

        try:
            for index, spec in enumerate(job_specs):
                if isinstance(spec, list):
                    target_list: list[tuple[LazyRef[object], int | None]] = []
                    for destination in spec:
                        target_list.append((destination, destination._prefetch_reserve()))
                    reserved_targets.extend(target_list)
                    targets = tuple(target_list)
                    primary, primary_generation = targets[0]

                    def load_singular(
                        primary: LazyRef[object] = primary,
                        primary_generation: int | None = primary_generation,
                        targets: tuple[tuple[LazyRef[object], int | None], ...] = targets,
                    ) -> None:
                        try:
                            value = primary._prefetch_load(primary_generation)
                            for target, generation in targets:
                                if generation is not None:
                                    target._prefetch_publish(generation, value)
                        except Exception as error:
                            for target, generation in targets:
                                if generation is not None:
                                    target._prefetch_fail(generation, error)
                            raise

                    jobs.append((index, load_singular))
                    continue

                jobs.append((index, spec.all))

            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                for index, load in jobs:
                    futures[executor.submit(load)] = index
                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        future.result()
                    except CancelledError:
                        continue
                    except Exception as error:
                        failures[index] = error
                        for pending in futures:
                            if not pending.done():
                                pending.cancel()
                for future, index in futures.items():
                    try:
                        future.result()
                    except CancelledError:
                        continue
                    except Exception as error:
                        failures.setdefault(index, error)
        finally:
            cancellation = RuntimeError("prefetch job did not execute")
            for target, generation in reserved_targets:
                if generation is not None:
                    target._prefetch_fail(generation, cancellation)
        if failures:
            raise failures[min(failures)]

    def __enter__(self) -> MulticaClient:
        return self

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._transport.close()
        if self._owns_executor:
            self._executor.close()

    def __exit__(self, *args: object) -> None:
        self.close()

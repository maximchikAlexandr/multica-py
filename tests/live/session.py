"""Live session and case context managers (spec §11).

Exports: LiveEnvironment, LiveCase, LiveSession, SandboxSession.
"""

from __future__ import annotations

import contextlib
import pathlib
from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from tests.live.api import LiveApiClient, bootstrap_api_client
from tools.live_support.environment import Environment


@dataclass(frozen=True)
class LiveEnvironment(Environment):
    """Full live test environment with bootstrap state and helper callbacks.

    Carries every field the old conftest fixtures exposed (server_url, identity,
    primary/secondary workspaces, diagnostics, registry, target, agent-sandbox
    helpers, canary settings) so tests can address them via one fixture.
    """

    base_url: str = "https://api.multica.ai"
    canary: bool = False
    server_url: str = "https://api.multica.ai"
    compose_project: str = ""
    compose_files: tuple[pathlib.Path, ...] = field(default_factory=tuple)
    home_dir: pathlib.Path = pathlib.Path()
    profile_name: str = ""
    cli_executable: pathlib.Path = pathlib.Path()
    readiness_endpoint: str = ""
    readiness_timeout_seconds: float = 120.0
    managed_compose: bool = False
    run_id: str = ""
    target: Any = None
    diagnostics: Any = None
    resource_registry: Any = None
    identity: Any = None
    primary_workspace: Any = None
    secondary_workspace: Any = None
    client: Any = None
    client_secondary: Any = None
    oracle: Any = None
    agent_sandbox_settings: Any = None
    agent_sandbox_run_context: Any = None
    agent_sandbox_target_report: dict[str, object] = field(default_factory=dict)
    canary_settings: Any = None


@dataclass(frozen=True)
class LiveCase:
    """Per-test data (spec §11). `defer_cleanup` is the cleanup channel that
    replaced the legacy ``LiveSession.register_resource(key=..., cleanup=...)`` wrapper."""

    unique_name: str
    profile: str
    extra: dict[str, str] = field(default_factory=dict)
    _stack: contextlib.ExitStack = field(default_factory=contextlib.ExitStack, repr=False)

    def __enter__(self) -> LiveCase:
        self._stack.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._stack.__exit__(exc_type, exc_val, exc_tb)

    def defer_cleanup(self, callback: Callable[..., None], /, *args: Any) -> None:
        """Register a cleanup callback. Runs LIFO when the case closes.

        Cleanup callbacks are best-effort: ``ResourceAbsentError`` and
        ``NotFoundError`` (raised when the resource was already deleted
        by the test or an earlier cleanup) are swallowed so they do not
        fail the test in teardown. Other exceptions still propagate.
        """
        self._stack.callback(_swallow_absent(_bind_args(callback, args)))


def _bind_args(callback: Callable[..., None], args: tuple[Any, ...]) -> Callable[[], None]:
    if not args:
        return callback

    def _bound() -> None:
        callback(*args)

    return _bound


def _swallow_absent(callback: Callable[[], None]) -> Callable[[], None]:
    from multica_py.exceptions import NotFoundError
    from tools.live_support.oracle import ResourceAbsentError

    def _cleanup() -> None:
        try:
            callback()
        except (ResourceAbsentError, NotFoundError):
            return

    return _cleanup


class LiveSession(contextlib.AbstractContextManager["LiveSession"]):
    """One HTTP client + one ExitStack."""

    def __init__(self, env: LiveEnvironment) -> None:
        self.env = env
        self._stack = contextlib.ExitStack()
        self.api: LiveApiClient | None = None

    @property
    def client(self) -> Any:
        return self.env.client

    @property
    def client_secondary(self) -> Any:
        return self.env.client_secondary

    @property
    def oracle(self) -> Any:
        return self.env.oracle

    @property
    def identity(self) -> Any:
        return self.env.identity

    @property
    def diagnostics(self) -> Any:
        return self.env.diagnostics

    @property
    def resource_registry(self) -> Any:
        return self.env.resource_registry

    @property
    def primary_workspace(self) -> Any:
        return self.env.primary_workspace

    @property
    def secondary_workspace(self) -> Any:
        return self.env.secondary_workspace

    @property
    def target(self) -> Any:
        return self.env.target

    def defer_cleanup(self, callback: Callable[..., None], /, *args: Any) -> None:
        """Register a cleanup callback. Runs LIFO when the session closes.

        See ``LiveCase.defer_cleanup`` for the absent-resource semantics.
        """
        self._stack.callback(_swallow_absent(_bind_args(callback, args)))

    def __enter__(self) -> LiveSession:
        self.api = bootstrap_api_client(self.env)
        self._stack.enter_context(self.api)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._stack.__exit__(exc_type, exc_val, exc_tb)


class SandboxSession(LiveSession):
    """Sandbox session: LiveSession + filesystem workspace for sandbox tests."""

    def __init__(self, env: LiveEnvironment, workspace: pathlib.Path) -> None:
        super().__init__(env)
        self.workspace = workspace

    def __enter__(self) -> SandboxSession:
        LiveSession.__enter__(self)
        return self

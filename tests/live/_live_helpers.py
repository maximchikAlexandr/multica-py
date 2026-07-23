from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import shutil
import tempfile
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass

from tools.live_support.environment import (
    RUN_ID_PATTERN,
    AgentSandboxSettings,
    CompatibilityTarget,
    LiveSettings,
    LiveSetupError,
    SecretString,
    SuiteProfile,
)

__all__ = [
    "MAX_LABEL_NAME_LEN",
    "LiveRunContext",
    "LiveTestEnvironment",
    "LiveTestRun",
    "TestIdentity",
    "WorkspaceContext",
    "bootstrap_email",
    "compose_project_name",
    "create_live_run_context",
    "create_live_test_run",
    "ensure_temp_home",
    "generate_run_id",
    "label_name",
    "live_run_prefix",
    "load_agent_sandbox_settings",
    "profile_config_path",
    "profile_name_for_run",
    "remove_live_run_context",
    "remove_temp_home",
    "resolve_secrets_base_dir",
    "resource_prefix",
    "skip_if_canary_environment_incomplete",
    "validate_not_real_home",
    "validate_run_id",
    "workspace_slug",
    "write_cli_profile",
]


@dataclass(frozen=True, slots=True)
class LiveTestRun:
    run_id: str
    suite_profile: SuiteProfile
    started_at: datetime.datetime
    target: CompatibilityTarget
    compose_project: str
    artifact_dir: pathlib.Path
    secrets_dir: pathlib.Path


@dataclass(frozen=True, slots=True)
class LiveTestEnvironment:
    server_url: str
    compose_project: str
    compose_files: tuple[pathlib.Path, ...]
    home_dir: pathlib.Path
    profile_name: str
    cli_executable: pathlib.Path
    readiness_endpoint: str
    readiness_timeout_seconds: float
    managed_compose: bool


def generate_run_id() -> str:
    return uuid.uuid4().hex


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.match(run_id):
        raise LiveSetupError("run_id", "run_id must be 32 lowercase hex characters")


def live_run_prefix(run_id: str) -> str:
    validate_run_id(run_id)
    return f"multica-py-live-{run_id}"


def compose_project_name(run_id: str) -> str:
    return live_run_prefix(run_id)


def profile_name_for_run(run_id: str) -> str:
    return f"live-{run_id}"


def bootstrap_email(run_id: str) -> str:
    return f"multica-py-live+{run_id}@localhost"


def workspace_slug(run_id: str, suffix: str) -> str:
    base = f"mpy-{run_id}-{suffix}"
    return _truncate_with_hash(base, max_len=48)


def resource_prefix(run_id: str, test_fragment: str) -> str:
    base = f"mpy-live-{run_id}-{test_fragment}"
    return _truncate_with_hash(base, max_len=64)


MAX_LABEL_NAME_LEN = 32


def label_name(prefix: str, suffix: str = "") -> str:
    tail = f"-{suffix}" if suffix else ""
    if len(tail) >= MAX_LABEL_NAME_LEN:
        return _truncate_with_hash(tail.lstrip("-"), max_len=MAX_LABEL_NAME_LEN)
    return f"{_truncate_with_hash(prefix, max_len=MAX_LABEL_NAME_LEN - len(tail))}{tail}"


def _truncate_with_hash(value: str, *, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    digest = hashlib.sha256(value.encode()).hexdigest()[:8]
    keep = max_len - 9
    return f"{value[:keep]}-{digest}"


def resolve_secrets_base_dir(artifact_root: pathlib.Path) -> pathlib.Path:
    raw = os.environ.get("MULTICA_LIVE_SECRETS_DIR")
    if raw:
        base = pathlib.Path(raw)
        if not base.is_absolute():
            raise LiveSetupError("target", "MULTICA_LIVE_SECRETS_DIR must be absolute")
    else:
        base = pathlib.Path(tempfile.gettempdir()) / "multica-py-live-secrets"
    resolved_base = base.resolve()
    resolved_artifacts = artifact_root.resolve()
    if resolved_base == resolved_artifacts or resolved_base.is_relative_to(resolved_artifacts):
        raise LiveSetupError(
            "target",
            "MULTICA_LIVE_SECRETS_DIR must be outside MULTICA_LIVE_ARTIFACT_DIR",
        )
    resolved_base.mkdir(parents=True, exist_ok=True)
    resolved_base.chmod(0o700)
    return resolved_base


def create_live_test_run(
    target: CompatibilityTarget,
    settings: LiveSettings,
    *,
    run_id: str | None = None,
) -> LiveTestRun:
    resolved_run_id = run_id or generate_run_id()
    validate_run_id(resolved_run_id)
    artifact_dir = settings.artifact_dir / resolved_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    secrets_dir = resolve_secrets_base_dir(settings.artifact_dir) / resolved_run_id
    secrets_dir.mkdir(parents=True, exist_ok=True)
    secrets_dir.chmod(0o700)
    return LiveTestRun(
        run_id=resolved_run_id,
        suite_profile=settings.suite_profile,
        started_at=datetime.datetime.now(tz=datetime.UTC),
        target=target,
        compose_project=compose_project_name(resolved_run_id),
        artifact_dir=artifact_dir,
        secrets_dir=secrets_dir,
    )


def write_cli_profile(
    home_dir: pathlib.Path,
    profile_name: str,
    *,
    server_url: str,
    app_url: str,
    workspace_id: str,
    token: str,
) -> pathlib.Path:
    validate_not_real_home(home_dir)
    profile_dir = home_dir.resolve() / ".multica" / "profiles" / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    config_path = profile_dir / "config.json"
    payload = {
        "server_url": server_url,
        "app_url": app_url,
        "workspace_id": workspace_id,
        "token": token,
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    config_path.chmod(0o600)
    return config_path


def profile_config_path(home_dir: pathlib.Path, profile_name: str) -> pathlib.Path:
    return home_dir / ".multica" / "profiles" / profile_name / "config.json"


def ensure_temp_home(base_dir: pathlib.Path, run_id: str) -> pathlib.Path:
    home_dir = base_dir / f"home-{run_id}"
    home_dir.mkdir(parents=True, exist_ok=False)
    validate_not_real_home(home_dir)
    return home_dir


def remove_temp_home(home_dir: pathlib.Path) -> None:
    if home_dir.exists():
        shutil.rmtree(home_dir, ignore_errors=True)


def validate_not_real_home(home_dir: pathlib.Path) -> None:
    if home_dir.resolve() == pathlib.Path.home().resolve():
        raise LiveSetupError("profile", "live session HOME must not equal real HOME")


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    id: str
    name: str
    slug: str
    profile_name: str


@dataclass(slots=True)
class TestIdentity:
    __test__ = False

    email: str
    user_id: str
    pat: SecretString


_ALLOWED_AGENT_MODES = frozenset({"success", "error", "timeout", "wrong-edit"})
_ALLOWED_CLEANUP_INJECTIONS = frozenset({"remove-resource"})


@dataclass(frozen=True, slots=True)
class LiveRunContext:
    run_id: str
    prefix: str
    temp_root: pathlib.Path
    home: pathlib.Path
    workspaces_root: pathlib.Path
    sandbox_dir: pathlib.Path
    profile_name: str
    daemon_id: str
    artifact_dir: pathlib.Path
    workspace_id: str | None = None
    project_id: str | None = None
    resource_id: str | None = None
    runtime_id: str | None = None
    agent_id: str | None = None
    issue_id: str | None = None
    run_execution_id: str | None = None

    def diagnostics_payload(self) -> dict[str, object]:
        return {
            key: str(value) if isinstance(value, pathlib.Path) else value
            for key, value in asdict(self).items()
        }


def load_agent_sandbox_settings(*, repo_root: pathlib.Path | None = None) -> AgentSandboxSettings:
    root = repo_root or pathlib.Path.cwd()
    raw_mode = os.environ.get("MULTICA_TEST_AGENT_MODE")
    agent_mode = "success" if raw_mode in {None, ""} else raw_mode.strip()
    if agent_mode not in _ALLOWED_AGENT_MODES:
        raise LiveSetupError(
            "sandbox",
            f"MULTICA_TEST_AGENT_MODE must be one of {sorted(_ALLOWED_AGENT_MODES)}",
        )
    inject_raw = os.environ.get("MULTICA_TEST_INJECT_CLEANUP_FAILURE")
    inject_cleanup_failure = None if not inject_raw else inject_raw.strip()
    if (
        inject_cleanup_failure is not None
        and inject_cleanup_failure not in _ALLOWED_CLEANUP_INJECTIONS
    ):
        raise LiveSetupError(
            "sandbox",
            f"MULTICA_TEST_INJECT_CLEANUP_FAILURE must be one of {sorted(_ALLOWED_CLEANUP_INJECTIONS)}",
        )
    opencode_raw = os.environ.get("MULTICA_TEST_OPENCODE_PATH")
    if opencode_raw:
        opencode_path = pathlib.Path(opencode_raw)
    else:
        opencode_path = root / "tests" / "fixtures" / "fake_opencode.py"
    if not opencode_path.is_absolute():
        raise LiveSetupError("sandbox", "MULTICA_TEST_OPENCODE_PATH must be absolute when set")
    if not opencode_path.is_file():
        raise LiveSetupError("sandbox", f"OpenCode executable not found: {opencode_path}")
    if not os.access(opencode_path, os.X_OK):
        raise LiveSetupError("sandbox", f"OpenCode executable is not executable: {opencode_path}")
    return AgentSandboxSettings(
        agent_mode=agent_mode,
        inject_cleanup_failure=inject_cleanup_failure,
        opencode_path=opencode_path,
        opencode_model="multica-test/fake",
    )


def create_live_run_context(
    *,
    run_id: str,
    artifact_root: pathlib.Path,
    temp_parent: pathlib.Path | None = None,
) -> LiveRunContext:
    validate_run_id(run_id)
    prefix = live_run_prefix(run_id)
    parent = temp_parent or pathlib.Path(tempfile.gettempdir())
    temp_root = parent / prefix
    if temp_root.exists():
        shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=False)
    home = temp_root / "home"
    workspaces_root = temp_root / "workspaces"
    sandbox_dir = temp_root / "sandbox" / "project"
    home.mkdir(parents=True, exist_ok=False)
    workspaces_root.mkdir(parents=True, exist_ok=False)
    sandbox_dir.mkdir(parents=True, exist_ok=False)
    validate_not_real_home(home)
    artifact_dir = artifact_root / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return LiveRunContext(
        run_id=run_id,
        prefix=prefix,
        temp_root=temp_root,
        home=home,
        workspaces_root=workspaces_root,
        sandbox_dir=sandbox_dir.resolve(),
        profile_name=prefix,
        daemon_id=prefix,
        artifact_dir=artifact_dir,
    )


def remove_live_run_context(run_context: LiveRunContext) -> None:
    if run_context.temp_root.exists():
        shutil.rmtree(run_context.temp_root, ignore_errors=True)


def skip_if_canary_environment_incomplete(
    environ: Mapping[str, str] | None = None,
) -> None:
    import pytest

    from tools.live_support.environment import collect_missing_canary_variables

    missing = collect_missing_canary_variables(environ)
    if missing:
        pytest.skip(f"canary environment incomplete: missing {', '.join(missing)}")

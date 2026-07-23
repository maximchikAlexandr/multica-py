from __future__ import annotations

from tests.cases.argv_data import _SPAWN_SDK_METHODS, ARGV_CASES, ArgvSpec
from tests.cases.models import (
    BehaviorDimension,
    ExpectedTransportCall,
    FakeCliResponse,
    LivePolicy,
    OperationCase,
)

# fmt: off
_DECODE_METHODS = frozenset({
    "agents.get", "agents.list", "agents.tasks", "attachments.list", "attachments.upload",
    "autopilots.get_run", "autopilots.list", "maintenance.version",
    "projects.resources.add_local_directory", "projects.resources.list",
    "repositories.checkout", "repositories.list", "runtimes.list", "skills.list",
    "squads.list", "users.list",
})

# Live policy catalog (mode / owner). ``str`` value -> unrunnable with that
# reason; ``tuple(mode, owner)`` -> live policy with that mode/owner.
_LIVE_POLICY_RAW: dict[str, str | tuple[str, str]] = {
    'agents.archive': 'destructive-irrecoverable',
    'agents.create': ('sandbox', 'sandbox'),
    'agents.get': 'requires-external-infra',
    'agents.list': ('extended', 'direct:agents.list'),
    'agents.restore': 'destructive-irrecoverable',
    'agents.skills.list': 'requires-external-infra',
    'agents.skills.set': 'requires-external-infra',
    'agents.tasks': 'requires-external-infra',
    'agents.update': 'requires-external-infra',
    'agents.upload_avatar': 'requires-external-infra',
    'attachments.download': 'requires-external-infra',
    'attachments.list': 'requires-external-infra',
    'attachments.upload': 'requires-external-infra',
    'auth.login': 'interactive-or-foreground',
    'auth.logout': 'interactive-or-foreground',
    'auth.status': 'interactive-or-foreground',
    'autopilots.create': 'requires-external-infra',
    'autopilots.delete': 'requires-external-infra',
    'autopilots.get': 'requires-external-infra',
    'autopilots.get_run': 'requires-external-infra',
    'autopilots.history': 'requires-external-infra',
    'autopilots.list': 'requires-external-infra',
    'autopilots.run': 'requires-external-infra',
    'autopilots.triggers.create': 'requires-external-infra',
    'autopilots.triggers.delete': 'requires-external-infra',
    'autopilots.triggers.list': 'requires-external-infra',
    'autopilots.update': 'requires-external-infra',
    'configuration.get': 'requires-external-infra',
    'configuration.set': 'requires-external-infra',
    'configuration.show': 'requires-external-infra',
    'daemon.disk_usage': 'process-or-daemon-control',
    'daemon.logs': 'interactive-or-foreground',
    'daemon.restart': 'process-or-daemon-control',
    'daemon.start': 'process-or-daemon-control',
    'daemon.status': 'process-or-daemon-control',
    'daemon.stop': 'process-or-daemon-control',
    'issues.assign': ('extended', 'direct:issues.assign'),
    'issues.cancel_task': ('sandbox', 'sandbox'),
    'issues.children': 'requires-external-infra',
    'issues.comments.add': ('extended', 'direct:issues.comments.add'),
    'issues.comments.delete': ('extended', 'direct:issues.comments.delete'),
    'issues.comments.list': ('extended', 'direct:issues.comments.list'),
    'issues.comments.reply': 'requires-external-infra',
    'issues.comments.resolve': 'requires-external-infra',
    'issues.comments.unresolve': 'requires-external-infra',
    'issues.create': ('extended', 'direct:issues.create'),
    'issues.deprioritize': ('extended', 'direct:issues.deprioritize'),
    'issues.get': ('extended', 'direct:issues.get'),
    'issues.labels.add': ('extended', 'direct:issues.labels.add'),
    'issues.labels.list': ('extended', 'direct:issues.labels.list'),
    'issues.labels.remove': ('extended', 'direct:issues.labels.remove'),
    'issues.list': ('extended', 'direct:issues.list'),
    'issues.metadata.delete': 'requires-external-infra',
    'issues.metadata.get': 'requires-external-infra',
    'issues.metadata.list': 'requires-external-infra',
    'issues.metadata.set': 'requires-external-infra',
    'issues.pull_requests': 'requires-external-infra',
    'issues.reorder': 'requires-external-infra',
    'issues.rerun': 'requires-external-infra',
    'issues.run_messages': 'requires-external-infra',
    'issues.runs': ('sandbox', 'sandbox'),
    'issues.search': 'requires-external-infra',
    'issues.set_status': ('extended', 'direct:issues.set_status'),
    'issues.subscribers.add': ('extended', 'direct:issues.subscribers.add'),
    'issues.subscribers.list': ('extended', 'direct:issues.subscribers.list'),
    'issues.subscribers.remove': ('extended', 'direct:issues.subscribers.remove'),
    'issues.update': ('extended', 'direct:issues.update'),
    'issues.usage': 'requires-external-infra',
    'labels.create': ('extended', 'crud:labels'),
    'labels.delete': ('extended', 'crud:labels'),
    'labels.get': ('extended', 'crud:labels'),
    'labels.list': ('extended', 'direct:labels.list'),
    'labels.update': ('extended', 'crud:labels'),
    'maintenance.update': 'destructive-irrecoverable',
    'maintenance.version': 'requires-external-infra',
    'projects.create': ('extended', 'crud:projects'),
    'projects.delete': ('extended', 'crud:projects'),
    'projects.get': ('extended', 'crud:projects'),
    'projects.list': ('extended', 'direct:projects.list'),
    'projects.resources.add_local_directory': 'requires-external-infra',
    'projects.resources.list': 'requires-external-infra',
    'projects.resources.remove': 'requires-external-infra',
    'projects.resources.update_local_directory': 'requires-external-infra',
    'projects.set_status': ('extended', 'direct:projects.set_status'),
    'projects.update': ('extended', 'crud:projects'),
    'repositories.checkout': 'requires-external-infra',
    'repositories.get': 'requires-external-infra',
    'repositories.list': ('extended', 'direct:repositories.list'),
    'runtimes.get': 'requires-external-infra',
    'runtimes.list': ('extended', 'direct:runtimes.list'),
    'setup.cloud': 'interactive-or-foreground',
    'setup.self_host': 'interactive-or-foreground',
    'skills.create': 'requires-external-infra',
    'skills.delete': 'requires-external-infra',
    'skills.files.delete': 'requires-external-infra',
    'skills.files.list': 'requires-external-infra',
    'skills.files.upsert': 'requires-external-infra',
    'skills.get': 'requires-external-infra',
    'skills.import_from_url': 'requires-external-infra',
    'skills.list': ('extended', 'direct:skills.list'),
    'skills.update': 'requires-external-infra',
    'squads.get': 'requires-external-infra',
    'squads.list': ('extended', 'direct:squads.list'),
    'users.get': 'requires-external-infra',
    'users.list': 'requires-external-infra',
    'workspaces.get': ('extended', 'direct:workspaces.get'),
    'workspaces.list': ('extended', 'direct:workspaces.list'),
    'workspaces.members': ('extended', 'direct:workspaces.members'),
    'workspaces.switch': 'interactive-or-foreground',
    'workspaces.unwatch': 'requires-external-infra',
    'workspaces.watch': 'requires-external-infra',
}


def _to_policy(raw: str | tuple[str, str]) -> LivePolicy:
    if isinstance(raw, tuple):
        return LivePolicy(mode=raw[0], owner=raw[1])
    return LivePolicy(reason=raw)


_LIVE_POLICY: dict[str, LivePolicy] = {k: _to_policy(v) for k, v in _LIVE_POLICY_RAW.items()}


def _transport(case: ArgvSpec) -> ExpectedTransportCall:
    return ExpectedTransportCall(
        method=case.transport_method, args=list(case.expected_argv),
        stdin=case.stdin.decode("utf-8") if case.stdin is not None else None,
        timeout=int(case.timeout) if case.timeout is not None else None,
    )


def _argv_ref(sdk_method: str) -> ArgvSpec | None:
    for case in ARGV_CASES:
        if case.sdk_method == sdk_method and not case.id:
            return case
    for case in ARGV_CASES:
        if case.sdk_method == sdk_method:
            return case
    return None


def _make_case(sdk_method: str) -> OperationCase:
    argv = _argv_ref(sdk_method)
    expected_call = _transport(argv) if argv is not None else None
    case_args = tuple(argv.args) if argv is not None else ()
    case_kwargs = tuple(sorted(argv.kwargs.items())) if argv is not None else ()
    response = FakeCliResponse(stdout=argv.stdout) if argv is not None and argv.stdout else None
    live = _LIVE_POLICY[sdk_method]
    dimensions: set[BehaviorDimension] = {BehaviorDimension.ARGV}
    if sdk_method in _DECODE_METHODS:
        dimensions.add(BehaviorDimension.DECODE)
    if live.mode != "unrunnable" and sdk_method not in _SPAWN_SDK_METHODS:
        dimensions.add(BehaviorDimension.COMPONENT_ROUNDTRIP)
    if live.mode == "extended":
        dimensions.add(BehaviorDimension.LIVE_EXTENDED)
    elif live.mode == "sandbox":
        dimensions.add(BehaviorDimension.LIVE_SANDBOX)
    elif live.mode == "smoke":
        dimensions.add(BehaviorDimension.LIVE_SMOKE)
    return OperationCase(
        sdk_method=sdk_method, operation_id=sdk_method,
        args=case_args, kwargs=case_kwargs,
        expected_call=expected_call, response=response,
        live=live, tags={d.value for d in dimensions}, dimensions=frozenset(dimensions),
    )


OPERATION_CASES: tuple[OperationCase, ...] = tuple(_make_case(m) for m in _LIVE_POLICY)
# fmt: on

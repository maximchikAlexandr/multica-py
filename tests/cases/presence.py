from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PresenceCase:
    """One approved update presence vector and its exact command plan."""

    id: str
    model_id: str
    field: str
    state: str
    value: object
    expected_argv: tuple[tuple[str, ...], ...] | None = None
    error_match: str | None = None


@dataclass(frozen=True)
class NoOpCase:
    """An all-optional update's read-only execution contract."""

    id: str
    model_id: str
    target_id: str
    expected_argv: tuple[str, ...]
    stdout: bytes
    expected_entity_id: str


def _argv(*parts: str) -> tuple[tuple[str, ...], ...]:
    return (parts,)


def _omitted(model_id: str, field: str, target: str, command: str) -> PresenceCase:
    return PresenceCase(
        f"{model_id}:{field}:omitted",
        model_id,
        field,
        "omitted",
        (),
        _argv(command, "get", target, "--output", "json"),
    )


def _empty(model_id: str, field: str, target: str, *parts: str) -> PresenceCase:
    return PresenceCase(
        f"{model_id}:{field}:empty",
        model_id,
        field,
        "empty",
        "",
        _argv(*parts, "--output", "json"),
    )


def _null(
    model_id: str,
    field: str,
    target: str,
    expected_argv: tuple[tuple[str, ...], ...] | None = None,
    *,
    error_match: str | None = None,
) -> PresenceCase:
    return PresenceCase(
        f"{model_id}:{field}:null",
        model_id,
        field,
        "null",
        None,
        expected_argv,
        error_match,
    )


_OPTIONAL_UPDATE_PRESENCE_CASES: tuple[PresenceCase, ...] = (
    _omitted("ProjectUpdateRequest", "name", "p1", "project"),
    _omitted("ProjectUpdateRequest", "description", "p1", "project"),
    _empty("ProjectUpdateRequest", "name", "p1", "project", "update", "p1", "--title", ""),
    _empty(
        "ProjectUpdateRequest", "description", "p1", "project", "update", "p1", "--description", ""
    ),
    _null(
        "ProjectUpdateRequest",
        "name",
        "p1",
        error_match="name must be non-null",
    ),
    _null(
        "ProjectUpdateRequest",
        "description",
        "p1",
        _argv("project", "update", "p1", "--description", "", "--output", "json"),
    ),
    _omitted("AgentUpdateRequest", "name", "a1", "agent"),
    _omitted("AgentUpdateRequest", "description", "a1", "agent"),
    _empty("AgentUpdateRequest", "name", "a1", "agent", "update", "a1", "--name", ""),
    _empty("AgentUpdateRequest", "description", "a1", "agent", "update", "a1", "--description", ""),
    _null("AgentUpdateRequest", "name", "a1", error_match="name must be non-null"),
    _null(
        "AgentUpdateRequest",
        "description",
        "a1",
        _argv("agent", "update", "a1", "--description", "", "--output", "json"),
    ),
    _omitted("SkillUpdateRequest", "name", "s1", "skill"),
    _omitted("SkillUpdateRequest", "description", "s1", "skill"),
    _empty("SkillUpdateRequest", "name", "s1", "skill", "update", "s1", "--name", ""),
    _empty("SkillUpdateRequest", "description", "s1", "skill", "update", "s1", "--description", ""),
    _null("SkillUpdateRequest", "name", "s1", error_match="name must be non-null"),
    _null(
        "SkillUpdateRequest",
        "description",
        "s1",
        _argv("skill", "update", "s1", "--description", "", "--output", "json"),
    ),
    _omitted("IssueUpdateRequest", "title", "i1", "issue"),
    _omitted("IssueUpdateRequest", "description", "i1", "issue"),
    _omitted("IssueUpdateRequest", "priority", "i1", "issue"),
    _omitted("IssueUpdateRequest", "assignee_id", "i1", "issue"),
    _omitted("IssueUpdateRequest", "project_id", "i1", "issue"),
    _omitted("IssueUpdateRequest", "parent_id", "i1", "issue"),
    _empty("IssueUpdateRequest", "title", "i1", "issue", "update", "i1", "--title", ""),
    _empty("IssueUpdateRequest", "priority", "i1", "issue", "update", "i1", "--priority", ""),
    _empty("IssueUpdateRequest", "description", "i1", "issue", "update", "i1", "--description", ""),
    _empty("IssueUpdateRequest", "assignee_id", "i1", "issue", "update", "i1", "--assignee-id", ""),
    PresenceCase(
        "IssueUpdateRequest:project_id:empty",
        "IssueUpdateRequest",
        "project_id",
        "empty",
        "",
        error_match="project_id must be non-empty",
    ),
    PresenceCase(
        "IssueUpdateRequest:parent_id:empty",
        "IssueUpdateRequest",
        "parent_id",
        "empty",
        "",
        error_match="parent_id must be non-empty",
    ),
    _null("IssueUpdateRequest", "title", "i1", error_match="title must be non-null"),
    _null(
        "IssueUpdateRequest",
        "priority",
        "i1",
        error_match="priority must be non-null",
    ),
    _null(
        "IssueUpdateRequest",
        "description",
        "i1",
        _argv("issue", "update", "i1", "--description", "", "--output", "json"),
    ),
    _null(
        "IssueUpdateRequest",
        "assignee_id",
        "i1",
        (
            _argv("issue", "assign", "i1", "--unassign", "--output", "json")[0],
            _argv("issue", "get", "i1", "--output", "json")[0],
        ),
    ),
    _null(
        "IssueUpdateRequest",
        "project_id",
        "i1",
        _argv("issue", "update", "i1", "--project", "", "--output", "json"),
    ),
    _null(
        "IssueUpdateRequest",
        "parent_id",
        "i1",
        _argv("issue", "update", "i1", "--parent", "", "--output", "json"),
    ),
    _omitted("AutopilotUpdateRequest", "title", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "agent", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "priority", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "status", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "execution_mode", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "description", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "project_id", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "issue_title_template", "ap1", "autopilot"),
    _omitted("AutopilotUpdateRequest", "subscribers", "ap1", "autopilot"),
    _empty("AutopilotUpdateRequest", "title", "ap1", "autopilot", "update", "ap1", "--title", ""),
    _empty("AutopilotUpdateRequest", "agent", "ap1", "autopilot", "update", "ap1", "--agent", ""),
    _empty(
        "AutopilotUpdateRequest", "priority", "ap1", "autopilot", "update", "ap1", "--priority", ""
    ),
    _empty("AutopilotUpdateRequest", "status", "ap1", "autopilot", "update", "ap1", "--status", ""),
    _empty(
        "AutopilotUpdateRequest",
        "description",
        "ap1",
        "autopilot",
        "update",
        "ap1",
        "--description",
        "",
    ),
    _empty(
        "AutopilotUpdateRequest", "project_id", "ap1", "autopilot", "update", "ap1", "--project", ""
    ),
    _empty(
        "AutopilotUpdateRequest",
        "issue_title_template",
        "ap1",
        "autopilot",
        "update",
        "ap1",
        "--issue-title-template",
        "",
    ),
    _null("AutopilotUpdateRequest", "title", "ap1", error_match="title must be non-null"),
    _null("AutopilotUpdateRequest", "agent", "ap1", error_match="agent must be non-null"),
    _null(
        "AutopilotUpdateRequest",
        "priority",
        "ap1",
        error_match="priority must be non-null",
    ),
    _null("AutopilotUpdateRequest", "status", "ap1", error_match="status must be non-null"),
    _null(
        "AutopilotUpdateRequest",
        "execution_mode",
        "ap1",
        error_match="execution_mode must be non-null",
    ),
    _null(
        "AutopilotUpdateRequest",
        "description",
        "ap1",
        _argv("autopilot", "update", "ap1", "--description", "", "--output", "json"),
    ),
    _null(
        "AutopilotUpdateRequest",
        "project_id",
        "ap1",
        _argv("autopilot", "update", "ap1", "--project", "", "--output", "json"),
    ),
    _null(
        "AutopilotUpdateRequest",
        "issue_title_template",
        "ap1",
        _argv("autopilot", "update", "ap1", "--issue-title-template", "", "--output", "json"),
    ),
    PresenceCase(
        "AutopilotUpdateRequest:subscribers:empty",
        "AutopilotUpdateRequest",
        "subscribers",
        "empty",
        (),
        _argv("autopilot", "update", "ap1", "--clear-subscribers", "--output", "json"),
    ),
    _null(
        "AutopilotUpdateRequest",
        "subscribers",
        "ap1",
        error_match="subscribers must be non-null",
    ),
    _omitted("LabelUpdateRequest", "name", "l1", "label"),
    _omitted("LabelUpdateRequest", "color", "l1", "label"),
    _empty("LabelUpdateRequest", "name", "l1", "label", "update", "l1", "--name", ""),
    _empty("LabelUpdateRequest", "color", "l1", "label", "update", "l1", "--color", ""),
    _null("LabelUpdateRequest", "name", "l1", error_match="name must be non-null"),
    _null("LabelUpdateRequest", "color", "l1", error_match="color must be non-null"),
    PresenceCase(
        "AutopilotTriggerUpdate:title:omitted",
        "AutopilotTriggerUpdate",
        "title",
        "omitted",
        (),
        _argv("autopilot", "get", "ap1", "--output", "json"),
    ),
    PresenceCase(
        "AutopilotTriggerUpdate:kind:omitted",
        "AutopilotTriggerUpdate",
        "kind",
        "omitted",
        (),
        _argv("autopilot", "get", "ap1", "--output", "json"),
    ),
    _empty(
        "AutopilotTriggerUpdate",
        "title",
        "tr1",
        "autopilot",
        "trigger-update",
        "ap1",
        "tr1",
        "--title",
        "",
    ),
    _empty(
        "AutopilotTriggerUpdate",
        "kind",
        "tr1",
        "autopilot",
        "trigger-update",
        "ap1",
        "tr1",
        "--kind",
        "",
    ),
    _null("AutopilotTriggerUpdate", "title", "tr1", error_match="title must be non-null"),
    _null("AutopilotTriggerUpdate", "kind", "tr1", error_match="kind must be non-null"),
    PresenceCase(
        "UserProfileUpdate:description:omitted",
        "UserProfileUpdate",
        "description",
        "omitted",
        (),
        _argv("user", "profile", "get", "--output", "json"),
    ),
    _empty(
        "UserProfileUpdate",
        "description",
        "profile",
        "user",
        "profile",
        "update",
        "--description",
        "",
    ),
    _null(
        "UserProfileUpdate",
        "description",
        "profile",
        _argv("user", "profile", "update", "--clear", "--output", "json"),
    ),
)


REQUIRED_UPDATE_BOUNDARY_CASES: tuple[PresenceCase, ...] = (
    PresenceCase(
        "ProjectResourceUpdateLocalDirectoryRequest:local_path:omitted",
        "ProjectResourceUpdateLocalDirectoryRequest",
        "local_path",
        "omitted",
        (),
        error_match="Missing required argument 'local_path'",
    ),
    PresenceCase(
        "ProjectResourceUpdateLocalDirectoryRequest:local_path:null",
        "ProjectResourceUpdateLocalDirectoryRequest",
        "local_path",
        "null",
        None,
        error_match="local_path must be non-null",
    ),
    PresenceCase(
        "RuntimeUpdate:target_version:omitted",
        "RuntimeUpdate",
        "target_version",
        "omitted",
        (),
        error_match="Missing required argument 'target_version'",
    ),
    PresenceCase(
        "RuntimeUpdate:target_version:null",
        "RuntimeUpdate",
        "target_version",
        "null",
        None,
        error_match="target_version must be non-null",
    ),
    PresenceCase(
        "RuntimeUpdate:wait:false",
        "RuntimeUpdate",
        "wait",
        "false",
        False,
        _argv("runtime", "update", "r1", "--target-version", "v1", "--output", "json"),
    ),
    PresenceCase(
        "RuntimeUpdate:wait:zero",
        "RuntimeUpdate",
        "wait",
        "zero",
        0,
        _argv("runtime", "update", "r1", "--target-version", "v1", "--output", "json"),
    ),
)


NO_OP_CASES: tuple[NoOpCase, ...] = (
    NoOpCase(
        "ProjectUpdateRequest",
        "ProjectUpdateRequest",
        "p1",
        ("project", "get", "p1"),
        b'{"id":"p1","title":"Project","status":"planned"}',
        "p1",
    ),
    NoOpCase(
        "AgentUpdateRequest",
        "AgentUpdateRequest",
        "a1",
        ("agent", "get", "a1"),
        b'{"id":"a1","name":"Agent"}',
        "a1",
    ),
    NoOpCase(
        "SkillUpdateRequest",
        "SkillUpdateRequest",
        "s1",
        ("skill", "get", "s1"),
        b'{"id":"s1","name":"Skill"}',
        "s1",
    ),
    NoOpCase(
        "IssueUpdateRequest",
        "IssueUpdateRequest",
        "i1",
        ("issue", "get", "i1"),
        b'{"id":"i1","title":"Issue","status":"todo"}',
        "i1",
    ),
    NoOpCase(
        "AutopilotUpdateRequest",
        "AutopilotUpdateRequest",
        "ap1",
        ("autopilot", "get", "ap1"),
        b'{"autopilot":{"id":"ap1","workspace_id":"w1","title":"AP",'
        b'"assignee_type":"member","assignee_id":"u1","status":"active",'
        b'"execution_mode":"create_issue","created_by_type":"member",'
        b'"created_by_id":"u1"},"triggers":[]}',
        "ap1",
    ),
    NoOpCase(
        "LabelUpdateRequest",
        "LabelUpdateRequest",
        "l1",
        ("label", "get", "l1"),
        b'{"id":"l1","name":"Label"}',
        "l1",
    ),
    NoOpCase(
        "AutopilotTriggerUpdate",
        "AutopilotTriggerUpdate",
        "ap1",
        ("autopilot", "get", "ap1"),
        b'{"autopilot":{"id":"ap1","workspace_id":"w1","title":"AP",'
        b'"assignee_type":"member","assignee_id":"u1","status":"active",'
        b'"execution_mode":"create_issue","created_by_type":"member",'
        b'"created_by_id":"u1"},"triggers":[{"id":"tr1","type":"webhook",'
        b'"config":{}}]}',
        "tr1",
    ),
    NoOpCase(
        "UserProfileUpdate",
        "UserProfileUpdate",
        "profile",
        ("user", "profile", "get"),
        b'{"id":"u1","name":"User"}',
        "u1",
    ),
)


OPTIONAL_UPDATE_PRESENCE_CASES = _OPTIONAL_UPDATE_PRESENCE_CASES
PRESENCE_CASES = _OPTIONAL_UPDATE_PRESENCE_CASES + REQUIRED_UPDATE_BOUNDARY_CASES

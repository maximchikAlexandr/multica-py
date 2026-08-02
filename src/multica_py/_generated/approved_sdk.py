from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

TARGET_VERSION = '0.4.9'
MIN_CLI_VERSION = TARGET_VERSION
MAX_CLI_VERSION = '0.4.10'

class AutopilotExecutionMode(StrEnum):
    create_issue = 'create_issue'
    run_only = 'run_only'

class IssueSort(StrEnum):
    position = 'position'
    title = 'title'
    created_at = 'created_at'
    start_date = 'start_date'
    due_date = 'due_date'
    priority = 'priority'

class SortDirection(StrEnum):
    asc = 'asc'
    desc = 'desc'

@dataclass(frozen=True)
class GeneratedMapping:
    python_path: str
    cli_binding: str
    destination: str

@dataclass(frozen=True)
class GeneratedBinding:
    operation_id: str
    entrypoint_id: str
    command: tuple[str, ...]
    mappings: tuple[GeneratedMapping, ...]
    validator_ids: tuple[str, ...]

AGENT_AVATAR_BINDING = GeneratedBinding(
    'agents.avatar', 'default', ('agent', 'avatar'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('file', '--file', 'local_control:absolute_path'),), ('nonblank:agent_id',),
)

AGENT_GET_BINDING = GeneratedBinding(
    'agents.get', 'default', ('agent', 'get'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), ('nonblank:agent_id',),
)

AGENT_LIST_BINDING = GeneratedBinding(
    'agents.list', 'default', ('agent', 'list'),
    (), (),
)

AGENT_SKILLS_LIST_BINDING = GeneratedBinding(
    'agents.skills.list', 'default', ('agent', 'skills', 'list'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), ('nonblank:agent_id',),
)

AGENT_SKILLS_SET_BINDING = GeneratedBinding(
    'agents.skills.set', 'default', ('agent', 'skills', 'set'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('skill_ids', 'repeat:pos:1', 'path:skill_ids'),), ('nonblank:agent_id',),
)

AGENT_TASKS_BINDING = GeneratedBinding(
    'agents.tasks', 'default', ('agent', 'tasks'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), ('nonblank:agent_id',),
)

ATTACHMENT_DOWNLOAD_BINDING = GeneratedBinding(
    'attachments.download', 'default', ('attachment', 'download'),
    (GeneratedMapping('attachment_id', 'pos:0', 'path:attachment_id'), GeneratedMapping('output_dir', '--output-dir', 'local_control:absolute_path'),), ('nonblank:attachment_id',),
)

ATTACHMENT_UPLOAD_BINDING = GeneratedBinding(
    'attachments.upload', 'default', ('attachment', 'upload'),
    (GeneratedMapping('path', 'pos:0', 'local_control:absolute_path'), GeneratedMapping('task_id', '--task', 'path:task_id'),), (),
)

AUTOPILOT_CREATE_BINDING = GeneratedBinding(
    'autopilots.create', 'default', ('autopilot', 'create'),
    (GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('agent', '--agent', 'json_body:assignee_id'), GeneratedMapping('execution_mode', '--mode', 'json_body:execution_mode'), GeneratedMapping('priority', '--priority', 'json_body:priority'), GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('issue_title_template', '--issue-title-template', 'json_body:issue_title_template'), GeneratedMapping('subscribers', 'repeat:--subscriber', 'json_body:subscribers'),), ('nonblank:title', 'nonblank:agent'),
)

AUTOPILOT_DELETE_BINDING = GeneratedBinding(
    'autopilots.delete', 'default', ('autopilot', 'delete'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'),), ('nonblank:autopilot_id',),
)

AUTOPILOT_GET_BINDING = GeneratedBinding(
    'autopilots.get', 'default', ('autopilot', 'get'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'),), ('nonblank:autopilot_id',),
)

AUTOPILOT_HISTORY_BINDING = GeneratedBinding(
    'autopilots.history', 'default', ('autopilot', 'runs'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('limit', '--limit', 'query:limit'), GeneratedMapping('offset', '--offset', 'query:offset'),), ('nonblank:autopilot_id',),
)

AUTOPILOT_LIST_BINDING = GeneratedBinding(
    'autopilots.list', 'default', ('autopilot', 'list'),
    (), (),
)

AUTOPILOT_TRIGGER_BINDING = GeneratedBinding(
    'autopilots.trigger', 'default', ('autopilot', 'trigger'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'),), ('nonblank:autopilot_id',),
)

AUTOPILOT_TRIGGER_ADD_BINDING = GeneratedBinding(
    'autopilots.trigger_add', 'default', ('autopilot', 'trigger-add'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('request.title', '--title', 'json_body:title'), GeneratedMapping('request.kind', '--kind', 'json_body:trigger_kind'),), ('nonblank:autopilot_id', 'nonblank:request.title'),
)

AUTOPILOT_TRIGGER_DELETE_BINDING = GeneratedBinding(
    'autopilots.trigger_delete', 'default', ('autopilot', 'trigger-delete'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('trigger_id', 'pos:1', 'path:trigger_id'),), ('nonblank:autopilot_id', 'nonblank:trigger_id'),
)

AUTOPILOT_TRIGGER_UPDATE_BINDING = GeneratedBinding(
    'autopilots.trigger_update', 'default', ('autopilot', 'trigger-update'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('trigger_id', 'pos:1', 'path:trigger_id'), GeneratedMapping('request.title', '--title', 'json_body:title'), GeneratedMapping('request.kind', '--kind', 'json_body:trigger_kind'),), ('nonblank:autopilot_id', 'nonblank:trigger_id'),
)

AUTOPILOT_UPDATE_BINDING = GeneratedBinding(
    'autopilots.update', 'default', ('autopilot', 'update'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('agent', '--agent', 'json_body:assignee_id'), GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('priority', '--priority', 'json_body:priority'), GeneratedMapping('status', '--status', 'json_body:status'), GeneratedMapping('execution_mode', '--mode', 'json_body:execution_mode'), GeneratedMapping('issue_title_template', '--issue-title-template', 'json_body:issue_title_template'), GeneratedMapping('subscribers', 'repeat:--subscriber', 'json_body:subscribers'), GeneratedMapping('clear_subscribers', '--clear-subscribers', 'json_body:clear_subscribers'),), ('nonblank:autopilot_id',),
)

ISSUE_CANCEL_TASK_BINDING = GeneratedBinding(
    'issues.cancel_task', 'default', ('issue', 'cancel-task'),
    (GeneratedMapping('task_id', 'pos:0', 'path:task_id'), GeneratedMapping('issue_id', '--issue', 'query:issue_id'),), ('nonblank:task_id',),
)

ISSUE_CHILDREN_BINDING = GeneratedBinding(
    'issues.children', 'default', ('issue', 'children'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

COMMENT_ADD_BINDING = GeneratedBinding(
    'issues.comments.add', 'default', ('issue', 'comment', 'add'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('body', '--content', 'json_body:content'),), ('nonblank:body',),
)

COMMENT_DELETE_BINDING = GeneratedBinding(
    'issues.comments.delete', 'default', ('issue', 'comment', 'delete'),
    (GeneratedMapping('comment_id', 'pos:0', 'path:comment_id'),), ('nonblank:comment_id',),
)

COMMENT_LIST_BINDING = GeneratedBinding(
    'issues.comments.list', 'direct', ('issue', 'comment', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

COMMENT_LIST_FLAT_BINDING = GeneratedBinding(
    'issues.comments.list', 'flat', ('issue', 'comment', 'list'),
    (GeneratedMapping('request.issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('request.since', '--since', 'query:since'),), (),
)

COMMENT_LIST_RECENT_BINDING = GeneratedBinding(
    'issues.comments.list', 'recent', ('issue', 'comment', 'list'),
    (GeneratedMapping('request.issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('request.limit', '--recent', 'query:recent'), GeneratedMapping('request.cursor.before', '--before', 'query:before'), GeneratedMapping('request.cursor.before_id', '--before-id', 'query:before_id'),), ('cursor_pair', 'limit_positive'),
)

COMMENT_LIST_THREAD_BINDING = GeneratedBinding(
    'issues.comments.list', 'thread', ('issue', 'comment', 'list'),
    (GeneratedMapping('request.issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('request.thread_id', '--thread', 'query:thread'), GeneratedMapping('request.limit', '--tail', 'query:tail'), GeneratedMapping('request.cursor.before', '--before', 'query:before'), GeneratedMapping('request.cursor.before_id', '--before-id', 'query:before_id'),), ('cursor_pair', 'cursor_requires_limit', 'limit_nonnegative'),
)

ISSUE_CREATE_BINDING = GeneratedBinding(
    'issues.create', 'default', ('issue', 'create'),
    (GeneratedMapping('request.title', '--title', 'json_body:title'), GeneratedMapping('request.description_input', 'description-selector', 'local_control:description'), GeneratedMapping('request.priority', '--priority', 'json_body:priority'), GeneratedMapping('request.assignee_id', '--assignee-id', 'json_body:assignee_id'), GeneratedMapping('request.project_id', '--project', 'json_body:project_id'), GeneratedMapping('request.parent_id', '--parent', 'json_body:parent_issue_id'), GeneratedMapping('request.label_ids', 'repeat:issue label add', 'json_body:label_id'),), ('nonblank:request.title', 'description_exactly_one'),
)

ISSUE_GET_BINDING = GeneratedBinding(
    'issues.get', 'default', ('issue', 'get'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_LABELS_ADD_BINDING = GeneratedBinding(
    'issues.labels.add', 'default', ('issue', 'label', 'add'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('label_id', 'pos:1', 'json_body:label_id'),), ('nonblank:issue_id', 'nonblank:label_id'),
)

ISSUE_LABELS_LIST_BINDING = GeneratedBinding(
    'issues.labels.list', 'default', ('issue', 'label', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_LABELS_REMOVE_BINDING = GeneratedBinding(
    'issues.labels.remove', 'default', ('issue', 'label', 'remove'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('label_id', 'pos:1', 'path:label_id'),), ('nonblank:issue_id', 'nonblank:label_id'),
)

ISSUE_LIST_BINDING = GeneratedBinding(
    'issues.list', 'default', ('issue', 'list'),
    (GeneratedMapping('filter.status', '--status', 'query:status'), GeneratedMapping('filter.priority', '--priority', 'query:priority'), GeneratedMapping('filter.assignee_id', '--assignee-id', 'query:assignee_id'), GeneratedMapping('filter.limit', '--limit', 'query:limit'), GeneratedMapping('filter.offset', '--offset', 'query:offset'), GeneratedMapping('filter.project_id', '--project', 'query:project_id'), GeneratedMapping('filter.sort', '--sort', 'query:sort'), GeneratedMapping('filter.direction', '--direction', 'query:direction'),), ('direction_requires_sort', 'offset_nonnegative', 'position_forbids_direction'),
)

ISSUE_METADATA_DELETE_BINDING = GeneratedBinding(
    'issues.metadata.delete', 'default', ('issue', 'metadata', 'delete'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('key', 'pos:1', 'path:key'),), ('nonblank:issue_id', 'nonblank:key'),
)

ISSUE_METADATA_GET_BINDING = GeneratedBinding(
    'issues.metadata.get', 'default', ('issue', 'metadata', 'get'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('key', 'pos:1', 'path:key'),), ('nonblank:issue_id', 'nonblank:key'),
)

ISSUE_METADATA_LIST_BINDING = GeneratedBinding(
    'issues.metadata.list', 'default', ('issue', 'metadata', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_METADATA_SET_BINDING = GeneratedBinding(
    'issues.metadata.set', 'default', ('issue', 'metadata', 'set'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('key', 'pos:1', 'path:key'), GeneratedMapping('value', 'pos:2', 'json_body:value'),), ('nonblank:issue_id', 'nonblank:key'),
)

ISSUE_PULL_REQUESTS_BINDING = GeneratedBinding(
    'issues.pull_requests', 'default', ('issue', 'pull-requests'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_RERUN_BINDING = GeneratedBinding(
    'issues.rerun', 'default', ('issue', 'rerun'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_RUN_MESSAGES_BINDING = GeneratedBinding(
    'issues.run_messages', 'default', ('issue', 'run-messages'),
    (GeneratedMapping('task_run_id', 'pos:0', 'path:task_run_id'), GeneratedMapping('issue_id', '--issue', 'query:issue_id'),), ('nonblank:task_run_id',),
)

ISSUE_RUNS_BINDING = GeneratedBinding(
    'issues.runs', 'default', ('issue', 'runs'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_STATUS_BINDING = GeneratedBinding(
    'issues.set_status', 'default', ('issue', 'status'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('status', 'pos:1', 'json_body:status'),), ('strict:IssueStatus',),
)

ISSUE_SUBSCRIBERS_ADD_BINDING = GeneratedBinding(
    'issues.subscribers.add', 'default', ('issue', 'subscriber', 'add'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('user_id', 'pos:1', 'path:user_id'),), ('nonblank:issue_id', 'nonblank:user_id'),
)

ISSUE_SUBSCRIBERS_LIST_BINDING = GeneratedBinding(
    'issues.subscribers.list', 'default', ('issue', 'subscriber', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_SUBSCRIBERS_REMOVE_BINDING = GeneratedBinding(
    'issues.subscribers.remove', 'default', ('issue', 'subscriber', 'remove'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('user_id', 'pos:1', 'path:user_id'),), ('nonblank:issue_id', 'nonblank:user_id'),
)

LABEL_GET_BINDING = GeneratedBinding(
    'labels.get', 'default', ('label', 'get'),
    (GeneratedMapping('label_id', 'pos:0', 'path:label_id'),), ('nonblank:label_id',),
)

LABEL_LIST_BINDING = GeneratedBinding(
    'labels.list', 'default', ('label', 'list'),
    (), (),
)

PROJECT_CREATE_BINDING = GeneratedBinding(
    'projects.create', 'default', ('project', 'create'),
    (GeneratedMapping('request.name', '--title', 'json_body:title'), GeneratedMapping('request.description', '--description', 'json_body:description'),), ('nonblank:request.name',),
)

PROJECT_GET_BINDING = GeneratedBinding(
    'projects.get', 'default', ('project', 'get'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'),), ('nonblank:project_id',),
)

PROJECT_LIST_BINDING = GeneratedBinding(
    'projects.list', 'default', ('project', 'list'),
    (), (),
)

PROJECT_RESOURCE_ADD_BINDING = GeneratedBinding(
    'projects.resources.add_local_directory', 'default', ('project', 'resource', 'add'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('request.local_path', '--local-path', 'local_control:absolute_path'), GeneratedMapping('request.daemon_id', '--daemon-id', 'json_body:daemon_id'), GeneratedMapping('request.label', '--ref-label', 'json_body:label'), GeneratedMapping('literal.local_directory', '--type', 'json_body:type'),), ('nonblank:project_id', 'nonblank:request.local_path', 'nonblank:request.daemon_id', 'blank_label_omitted'),
)

PROJECT_RESOURCE_LIST_BINDING = GeneratedBinding(
    'projects.resources.list', 'default', ('project', 'resource', 'list'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'),), ('nonblank:project_id',),
)

PROJECT_RESOURCE_REMOVE_BINDING = GeneratedBinding(
    'projects.resources.remove', 'default', ('project', 'resource', 'remove'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('resource_id', 'pos:1', 'path:resource_id'),), ('nonblank:project_id', 'nonblank:resource_id'),
)

PROJECT_RESOURCE_UPDATE_BINDING = GeneratedBinding(
    'projects.resources.update_local_directory', 'default', ('project', 'resource', 'update'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('resource_id', 'pos:1', 'path:resource_id'), GeneratedMapping('request.local_path', '--local-path', 'local_control:absolute_path'),), ('nonblank:project_id', 'nonblank:resource_id', 'nonblank:request.local_path', 'preserve_daemon_and_label'),
)

PROJECT_STATUS_BINDING = GeneratedBinding(
    'projects.set_status', 'default', ('project', 'status'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('status', 'pos:1', 'json_body:status'),), ('strict:ProjectStatus',),
)

PROJECT_UPDATE_BINDING = GeneratedBinding(
    'projects.update', 'default', ('project', 'update'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('request.name', '--title', 'json_body:title'), GeneratedMapping('request.description', '--description', 'json_body:description'),), ('at_least_one:name_description', 'description_none_rejected', 'unset_omits', 'empty_emits'),
)

REPOSITORIES_ADD_BINDING = GeneratedBinding(
    'repositories.add', 'default', ('repo', 'add'),
    (GeneratedMapping('urls', 'repeat:pos:0', 'json_body:repos'), GeneratedMapping('description', '--description', 'json_body:description'),), (),
)

REPOSITORIES_LIST_BINDING = GeneratedBinding(
    'repositories.list', 'default', ('repo', 'list'),
    (), (),
)

REPOSITORIES_REMOVE_BINDING = GeneratedBinding(
    'repositories.remove', 'default', ('repo', 'remove'),
    (GeneratedMapping('urls', 'repeat:pos:0', 'json_body:repos'),), (),
)

RUNTIME_ACTIVITY_BINDING = GeneratedBinding(
    'runtimes.activity', 'default', ('runtime', 'activity'),
    (GeneratedMapping('runtime_id', 'pos:0', 'path:runtime_id'),), ('nonblank:runtime',),
)

RUNTIME_DELETE_BINDING = GeneratedBinding(
    'runtimes.delete', 'default', ('runtime', 'delete'),
    (GeneratedMapping('runtime_id', 'pos:0', 'path:runtime_id'), GeneratedMapping('cascade', '--cascade', 'local_control:cascade'),), ('nonblank:runtime',),
)

RUNTIME_LIST_BINDING = GeneratedBinding(
    'runtimes.list', 'default', ('runtime', 'list'),
    (), (),
)

RUNTIME_RENAME_BINDING = GeneratedBinding(
    'runtimes.rename', 'default', ('runtime', 'rename'),
    (GeneratedMapping('runtime_id', 'pos:0', 'path:runtime_id'), GeneratedMapping('name', 'pos:1', 'path:name'), GeneratedMapping('machine', '--machine', 'local_control:machine'),), ('nonblank:runtime', 'nonblank:name'),
)

RUNTIME_UPDATE_BINDING = GeneratedBinding(
    'runtimes.update', 'default', ('runtime', 'update'),
    (GeneratedMapping('runtime_id', 'pos:0', 'path:runtime_id'), GeneratedMapping('request.target_version', '--target-version', 'json_body:target_version'), GeneratedMapping('request.wait', '--wait', 'local_control:wait'),), ('nonblank:runtime',),
)

RUNTIME_USAGE_BINDING = GeneratedBinding(
    'runtimes.usage', 'default', ('runtime', 'usage'),
    (GeneratedMapping('runtime_id', 'pos:0', 'path:runtime_id'), GeneratedMapping('days', '--days', 'query:days'),), ('nonblank:runtime',),
)

SKILL_FILES_DELETE_BINDING = GeneratedBinding(
    'skills.files.delete', 'default', ('skill', 'files', 'delete'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'), GeneratedMapping('file_id', 'pos:1', 'path:file_id'),), ('nonblank:skill_id', 'nonblank:file_id'),
)

SKILL_FILES_LIST_BINDING = GeneratedBinding(
    'skills.files.list', 'default', ('skill', 'files', 'list'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'),), ('nonblank:skill_id',),
)

SKILL_FILES_UPSERT_BINDING = GeneratedBinding(
    'skills.files.upsert', 'default', ('skill', 'files', 'upsert'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'), GeneratedMapping('path', '--path', 'json_body:path'), GeneratedMapping('content', '--content', 'json_body:content'),), ('nonblank:skill_id', 'nonblank:path'),
)

SKILL_GET_BINDING = GeneratedBinding(
    'skills.get', 'default', ('skill', 'get'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'),), ('nonblank:skill_id',),
)

SKILL_LIST_BINDING = GeneratedBinding(
    'skills.list', 'default', ('skill', 'list'),
    (), (),
)

SQUAD_GET_BINDING = GeneratedBinding(
    'squads.get', 'default', ('squad', 'get'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'),), ('nonblank:squad_id',),
)

SQUAD_LIST_BINDING = GeneratedBinding(
    'squads.list', 'default', ('squad', 'list'),
    (), (),
)

SQUAD_MEMBERS_ADD_BINDING = GeneratedBinding(
    'squads.members.add', 'default', ('squad', 'member', 'add'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'), GeneratedMapping('member_id', 'pos:1', 'path:member_id'),), ('nonblank:squad_id', 'nonblank:member_id'),
)

SQUAD_MEMBERS_LIST_BINDING = GeneratedBinding(
    'squads.members.list', 'default', ('squad', 'member', 'list'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'),), ('nonblank:squad_id',),
)

SQUAD_MEMBERS_REMOVE_BINDING = GeneratedBinding(
    'squads.members.remove', 'default', ('squad', 'member', 'remove'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'), GeneratedMapping('member_id', 'pos:1', 'path:member_id'),), ('nonblank:squad_id', 'nonblank:member_id'),
)

USER_PROFILE_GET_BINDING = GeneratedBinding(
    'users.profile_get', 'default', ('user', 'profile', 'get'),
    (), (),
)

USER_PROFILE_UPDATE_BINDING = GeneratedBinding(
    'users.profile_update', 'default', ('user', 'profile', 'update'),
    (GeneratedMapping('request.description', '--description', 'json_body:profile_description'),), (),
)

WORKSPACE_GET_BINDING = GeneratedBinding(
    'workspaces.get', 'default', ('workspace', 'get'),
    (GeneratedMapping('workspace_id', 'pos:0', 'path:workspace_id'),), ('nonblank:workspace_id',),
)

WORKSPACE_LIST_BINDING = GeneratedBinding(
    'workspaces.list', 'default', ('workspace', 'list'),
    (), (),
)

WORKSPACE_MEMBERS_LIST_BINDING = GeneratedBinding(
    'workspaces.members.list', 'default', ('workspace', 'member', 'list'),
    (GeneratedMapping('workspace_id', 'pos:0', 'path:workspace_id'),), ('nonblank:workspace_id',),
)

OPERATION_BINDINGS: tuple[GeneratedBinding, ...] = (
    AGENT_AVATAR_BINDING,
    AGENT_GET_BINDING,
    AGENT_LIST_BINDING,
    AGENT_SKILLS_LIST_BINDING,
    AGENT_SKILLS_SET_BINDING,
    AGENT_TASKS_BINDING,
    ATTACHMENT_DOWNLOAD_BINDING,
    ATTACHMENT_UPLOAD_BINDING,
    AUTOPILOT_CREATE_BINDING,
    AUTOPILOT_DELETE_BINDING,
    AUTOPILOT_GET_BINDING,
    AUTOPILOT_HISTORY_BINDING,
    AUTOPILOT_LIST_BINDING,
    AUTOPILOT_TRIGGER_BINDING,
    AUTOPILOT_TRIGGER_ADD_BINDING,
    AUTOPILOT_TRIGGER_DELETE_BINDING,
    AUTOPILOT_TRIGGER_UPDATE_BINDING,
    AUTOPILOT_UPDATE_BINDING,
    ISSUE_CANCEL_TASK_BINDING,
    ISSUE_CHILDREN_BINDING,
    COMMENT_ADD_BINDING,
    COMMENT_DELETE_BINDING,
    COMMENT_LIST_BINDING,
    COMMENT_LIST_FLAT_BINDING,
    COMMENT_LIST_RECENT_BINDING,
    COMMENT_LIST_THREAD_BINDING,
    ISSUE_CREATE_BINDING,
    ISSUE_GET_BINDING,
    ISSUE_LABELS_ADD_BINDING,
    ISSUE_LABELS_LIST_BINDING,
    ISSUE_LABELS_REMOVE_BINDING,
    ISSUE_LIST_BINDING,
    ISSUE_METADATA_DELETE_BINDING,
    ISSUE_METADATA_GET_BINDING,
    ISSUE_METADATA_LIST_BINDING,
    ISSUE_METADATA_SET_BINDING,
    ISSUE_PULL_REQUESTS_BINDING,
    ISSUE_RERUN_BINDING,
    ISSUE_RUN_MESSAGES_BINDING,
    ISSUE_RUNS_BINDING,
    ISSUE_STATUS_BINDING,
    ISSUE_SUBSCRIBERS_ADD_BINDING,
    ISSUE_SUBSCRIBERS_LIST_BINDING,
    ISSUE_SUBSCRIBERS_REMOVE_BINDING,
    LABEL_GET_BINDING,
    LABEL_LIST_BINDING,
    PROJECT_CREATE_BINDING,
    PROJECT_GET_BINDING,
    PROJECT_LIST_BINDING,
    PROJECT_RESOURCE_ADD_BINDING,
    PROJECT_RESOURCE_LIST_BINDING,
    PROJECT_RESOURCE_REMOVE_BINDING,
    PROJECT_RESOURCE_UPDATE_BINDING,
    PROJECT_STATUS_BINDING,
    PROJECT_UPDATE_BINDING,
    REPOSITORIES_ADD_BINDING,
    REPOSITORIES_LIST_BINDING,
    REPOSITORIES_REMOVE_BINDING,
    RUNTIME_ACTIVITY_BINDING,
    RUNTIME_DELETE_BINDING,
    RUNTIME_LIST_BINDING,
    RUNTIME_RENAME_BINDING,
    RUNTIME_UPDATE_BINDING,
    RUNTIME_USAGE_BINDING,
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    SKILL_GET_BINDING,
    SKILL_LIST_BINDING,
    SQUAD_GET_BINDING,
    SQUAD_LIST_BINDING,
    SQUAD_MEMBERS_ADD_BINDING,
    SQUAD_MEMBERS_LIST_BINDING,
    SQUAD_MEMBERS_REMOVE_BINDING,
    USER_PROFILE_GET_BINDING,
    USER_PROFILE_UPDATE_BINDING,
    WORKSPACE_GET_BINDING,
    WORKSPACE_LIST_BINDING,
    WORKSPACE_MEMBERS_LIST_BINDING,
)

def normalize_optional_label(value: object) -> None:
    if value is None:
        raise ValueError('project update value cannot be None')

def validate_comment_cursor(value: object) -> None:
    if value is None:
        raise ValueError('project update value cannot be None')

def validate_description_input(value: object) -> None:
    if value is None:
        raise ValueError('project update value cannot be None')

def validate_issue_sort(value: object) -> None:
    if value is None:
        raise ValueError('project update value cannot be None')

def validate_issue_status(value: object) -> None:
    if not isinstance(value, str) or value not in ('backlog', 'blocked', 'cancelled', 'done', 'in_progress', 'in_review', 'todo'):
        raise ValueError('value is not a supported enum member')

def validate_nonblank(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('value must be nonblank')

def validate_nonnegative_limit(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('value must be a nonnegative integer')

def validate_positive_limit(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError('value must be a positive integer')

def validate_project_description(value: object) -> None:
    if value is None:
        raise ValueError('project update value cannot be None')

def validate_project_status(value: object) -> None:
    if not isinstance(value, str) or value not in ('cancelled', 'completed', 'in_progress', 'paused', 'planned'):
        raise ValueError('value is not a supported enum member')

def validate_project_update(value: object) -> None:
    if value is None:
        raise ValueError('project update value cannot be None')

def validate_resource_update(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('resource update path must be nonblank')

def validate_thread_cursor_limit(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError('value must be a positive integer')

__all__ = ('TARGET_VERSION', 'MIN_CLI_VERSION', 'MAX_CLI_VERSION', 'AutopilotExecutionMode', 'IssueSort', 'SortDirection', 'GeneratedMapping', 'GeneratedBinding', 'AGENT_AVATAR_BINDING', 'AGENT_GET_BINDING', 'AGENT_LIST_BINDING', 'AGENT_SKILLS_LIST_BINDING', 'AGENT_SKILLS_SET_BINDING', 'AGENT_TASKS_BINDING', 'ATTACHMENT_DOWNLOAD_BINDING', 'ATTACHMENT_UPLOAD_BINDING', 'AUTOPILOT_CREATE_BINDING', 'AUTOPILOT_DELETE_BINDING', 'AUTOPILOT_GET_BINDING', 'AUTOPILOT_HISTORY_BINDING', 'AUTOPILOT_LIST_BINDING', 'AUTOPILOT_TRIGGER_BINDING', 'AUTOPILOT_TRIGGER_ADD_BINDING', 'AUTOPILOT_TRIGGER_DELETE_BINDING', 'AUTOPILOT_TRIGGER_UPDATE_BINDING', 'AUTOPILOT_UPDATE_BINDING', 'COMMENT_ADD_BINDING', 'COMMENT_DELETE_BINDING', 'COMMENT_LIST_BINDING', 'COMMENT_LIST_FLAT_BINDING', 'COMMENT_LIST_RECENT_BINDING', 'COMMENT_LIST_THREAD_BINDING', 'ISSUE_CANCEL_TASK_BINDING', 'ISSUE_CHILDREN_BINDING', 'ISSUE_CREATE_BINDING', 'ISSUE_GET_BINDING', 'ISSUE_LABELS_ADD_BINDING', 'ISSUE_LABELS_LIST_BINDING', 'ISSUE_LABELS_REMOVE_BINDING', 'ISSUE_LIST_BINDING', 'ISSUE_METADATA_DELETE_BINDING', 'ISSUE_METADATA_GET_BINDING', 'ISSUE_METADATA_LIST_BINDING', 'ISSUE_METADATA_SET_BINDING', 'ISSUE_PULL_REQUESTS_BINDING', 'ISSUE_RERUN_BINDING', 'ISSUE_RUN_MESSAGES_BINDING', 'ISSUE_RUNS_BINDING', 'ISSUE_STATUS_BINDING', 'ISSUE_SUBSCRIBERS_ADD_BINDING', 'ISSUE_SUBSCRIBERS_LIST_BINDING', 'ISSUE_SUBSCRIBERS_REMOVE_BINDING', 'LABEL_GET_BINDING', 'LABEL_LIST_BINDING', 'PROJECT_CREATE_BINDING', 'PROJECT_GET_BINDING', 'PROJECT_LIST_BINDING', 'PROJECT_RESOURCE_ADD_BINDING', 'PROJECT_RESOURCE_LIST_BINDING', 'PROJECT_RESOURCE_REMOVE_BINDING', 'PROJECT_RESOURCE_UPDATE_BINDING', 'PROJECT_STATUS_BINDING', 'PROJECT_UPDATE_BINDING', 'REPOSITORIES_ADD_BINDING', 'REPOSITORIES_LIST_BINDING', 'REPOSITORIES_REMOVE_BINDING', 'RUNTIME_ACTIVITY_BINDING', 'RUNTIME_DELETE_BINDING', 'RUNTIME_LIST_BINDING', 'RUNTIME_RENAME_BINDING', 'RUNTIME_UPDATE_BINDING', 'RUNTIME_USAGE_BINDING', 'SKILL_FILES_DELETE_BINDING', 'SKILL_FILES_LIST_BINDING', 'SKILL_FILES_UPSERT_BINDING', 'SKILL_GET_BINDING', 'SKILL_LIST_BINDING', 'SQUAD_GET_BINDING', 'SQUAD_LIST_BINDING', 'SQUAD_MEMBERS_ADD_BINDING', 'SQUAD_MEMBERS_LIST_BINDING', 'SQUAD_MEMBERS_REMOVE_BINDING', 'USER_PROFILE_GET_BINDING', 'USER_PROFILE_UPDATE_BINDING', 'WORKSPACE_GET_BINDING', 'WORKSPACE_LIST_BINDING', 'WORKSPACE_MEMBERS_LIST_BINDING', 'OPERATION_BINDINGS', 'normalize_optional_label', 'validate_comment_cursor', 'validate_description_input', 'validate_issue_sort', 'validate_issue_status', 'validate_nonblank', 'validate_nonnegative_limit', 'validate_positive_limit', 'validate_project_description', 'validate_project_status', 'validate_project_update', 'validate_resource_update', 'validate_thread_cursor_limit')

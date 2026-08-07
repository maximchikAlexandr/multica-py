from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

TARGET_VERSION = '0.4.20'
MIN_CLI_VERSION = TARGET_VERSION
MAX_CLI_VERSION = '0.4.21'

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

@dataclass(frozen=True)
class GeneratedConvention:
    operation_id: str
    entrypoint_id: str
    category: str
    response_id: str
    typed_input_id: str | None
    input_mode: str
    presence_policy_ids: tuple[str, ...]
    command_symbol: str

AGENTS_ARCHIVE_MANUAL_BINDING = GeneratedBinding(
    'agents.archive', 'default', ('agent', 'archive'),
    (), (),
)

AGENT_AVATAR_BINDING = GeneratedBinding(
    'agents.avatar', 'default', ('agent', 'avatar'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('file', '--file', 'local_control:absolute_path'),), ('nonblank:agent_id',),
)

AGENT_COPY_BINDING = GeneratedBinding(
    'agents.copy', 'default', ('agent', 'copy'),
    (GeneratedMapping('source_agent_id', 'pos:0', 'path:source_agent_id'), GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('runtime_id', '--runtime-id', 'json_body:runtime_id'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('instructions', '--instructions', 'json_body:instructions'), GeneratedMapping('model', '--model', 'json_body:model'), GeneratedMapping('thinking_level', '--thinking-level', 'json_body:thinking_level'), GeneratedMapping('service_tier', '--service-tier', 'json_body:service_tier'), GeneratedMapping('custom_args', '--custom-args', 'json_body:custom_args'), GeneratedMapping('max_concurrent_tasks', '--max-concurrent-tasks', 'json_body:max_concurrent_tasks'), GeneratedMapping('permission_mode', '--permission-mode', 'json_body:permission_mode'), GeneratedMapping('public_to_workspace', '--public-to-workspace', 'json_body:public_to_workspace'), GeneratedMapping('public_to_member_ids', 'repeat:--public-to-member', 'json_body:public_to_member_ids'), GeneratedMapping('copy_skills', '--no-skills', 'local_control:copy_skills'),), ('nonblank:source_agent_id', 'positive_int:max_concurrent_tasks'),
)

AGENTS_CREATE_MANUAL_BINDING = GeneratedBinding(
    'agents.create', 'default', ('agent', 'create'),
    (), (),
)

AGENT_GET_BINDING = GeneratedBinding(
    'agents.get', 'default', ('agent', 'get'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), ('nonblank:agent_id',),
)

AGENT_LIST_BINDING = GeneratedBinding(
    'agents.list', 'default', ('agent', 'list'),
    (), (),
)

AGENTS_RESTORE_MANUAL_BINDING = GeneratedBinding(
    'agents.restore', 'default', ('agent', 'restore'),
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

AGENTS_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'agents.update', 'default', ('agent', 'update'),
    (), (),
)

ATTACHMENT_DOWNLOAD_BINDING = GeneratedBinding(
    'attachments.download', 'default', ('attachment', 'download'),
    (GeneratedMapping('attachment_id', 'pos:0', 'path:attachment_id'), GeneratedMapping('output_dir', '--output-dir', 'local_control:absolute_path'),), ('nonblank:attachment_id',),
)

ATTACHMENTS_DOWNLOAD_BYTES_MANUAL_BINDING = GeneratedBinding(
    'attachments.download_bytes', 'default', ('attachment', 'download'),
    (), (),
)

ATTACHMENT_UPLOAD_BINDING = GeneratedBinding(
    'attachments.upload', 'default', ('attachment', 'upload'),
    (GeneratedMapping('path', 'pos:0', 'local_control:absolute_path'), GeneratedMapping('task_id', '--task', 'path:task_id'),), (),
)

ATTACHMENTS_UPLOAD_BYTES_MANUAL_BINDING = GeneratedBinding(
    'attachments.upload_bytes', 'default', ('attachment', 'upload'),
    (), (),
)

AUTH_LOGIN_MANUAL_BINDING = GeneratedBinding(
    'auth.login', 'default', ('auth', 'login'),
    (), (),
)

AUTH_LOGOUT_MANUAL_BINDING = GeneratedBinding(
    'auth.logout', 'default', ('auth', 'logout'),
    (), (),
)

AUTH_STATUS_MANUAL_BINDING = GeneratedBinding(
    'auth.status', 'default', ('auth', 'status'),
    (), (),
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

CONFIGURATION_GET_MANUAL_BINDING = GeneratedBinding(
    'configuration.get', 'default', ('config', 'get'),
    (), (),
)

CONFIGURATION_SET_MANUAL_BINDING = GeneratedBinding(
    'configuration.set', 'default', ('config', 'set'),
    (), (),
)

CONFIGURATION_SHOW_MANUAL_BINDING = GeneratedBinding(
    'configuration.show', 'default', ('config', 'show'),
    (), (),
)

DAEMON_DISK_USAGE_MANUAL_BINDING = GeneratedBinding(
    'daemon.disk_usage', 'default', ('daemon', 'disk-usage'),
    (), (),
)

DAEMON_LOGS_MANUAL_BINDING = GeneratedBinding(
    'daemon.logs', 'default', ('daemon', 'logs'),
    (), (),
)

DAEMON_RESTART_MANUAL_BINDING = GeneratedBinding(
    'daemon.restart', 'default', ('daemon', 'restart'),
    (), (),
)

DAEMON_START_MANUAL_BINDING = GeneratedBinding(
    'daemon.start', 'default', ('daemon', 'start'),
    (), (),
)

DAEMON_STATUS_MANUAL_BINDING = GeneratedBinding(
    'daemon.status', 'default', ('daemon', 'status'),
    (), (),
)

DAEMON_STOP_MANUAL_BINDING = GeneratedBinding(
    'daemon.stop', 'default', ('daemon', 'stop'),
    (), (),
)

ISSUES_ASSIGN_MANUAL_BINDING = GeneratedBinding(
    'issues.assign', 'default', ('issue', 'assign'),
    (), (),
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

ISSUES_COMMENTS_REPLY_MANUAL_BINDING = GeneratedBinding(
    'issues.comments.reply', 'default', ('issue', 'comment', 'add'),
    (), (),
)

ISSUES_COMMENTS_RESOLVE_MANUAL_BINDING = GeneratedBinding(
    'issues.comments.resolve', 'default', ('issue', 'comment', 'resolve'),
    (), (),
)

ISSUES_COMMENTS_UNRESOLVE_MANUAL_BINDING = GeneratedBinding(
    'issues.comments.unresolve', 'default', ('issue', 'comment', 'unresolve'),
    (), (),
)

ISSUE_CREATE_BINDING = GeneratedBinding(
    'issues.create', 'default', ('issue', 'create'),
    (GeneratedMapping('request.title', '--title', 'json_body:title'), GeneratedMapping('request.description_input', 'description-selector', 'local_control:description'), GeneratedMapping('request.priority', '--priority', 'json_body:priority'), GeneratedMapping('request.assignee_id', '--assignee-id', 'json_body:assignee_id'), GeneratedMapping('request.project_id', '--project', 'json_body:project_id'), GeneratedMapping('request.parent_id', '--parent', 'json_body:parent_issue_id'), GeneratedMapping('request.label_ids', 'repeat:issue label add', 'json_body:label_id'),), ('nonblank:request.title', 'description_exactly_one'),
)

ISSUES_DEPRIORITIZE_MANUAL_BINDING = GeneratedBinding(
    'issues.deprioritize', 'default', ('issue', 'deprioritize'),
    (), (),
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
    (GeneratedMapping('filter.status', '--status', 'query:status'), GeneratedMapping('filter.priority', '--priority', 'query:priority'), GeneratedMapping('filter.assignee_id', '--assignee-id', 'query:assignee_id'), GeneratedMapping('filter.limit', '--limit', 'query:limit'), GeneratedMapping('filter.offset', '--offset', 'query:offset'), GeneratedMapping('filter.project_id', '--project', 'query:project_id'), GeneratedMapping('filter.metadata', 'repeat:--metadata', 'query:metadata'), GeneratedMapping('filter.sort', '--sort', 'query:sort'), GeneratedMapping('filter.direction', '--direction', 'query:direction'),), ('direction_requires_sort', 'offset_nonnegative', 'position_forbids_direction'),
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

ISSUES_METADATA_QUERY_MANUAL_BINDING = GeneratedBinding(
    'issues.metadata.query', 'default', ('issue', 'metadata', 'list'),
    (), (),
)

ISSUE_METADATA_SET_BINDING = GeneratedBinding(
    'issues.metadata.set', 'default', ('issue', 'metadata', 'set'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('key', 'pos:1', 'path:key'), GeneratedMapping('value', 'pos:2', 'json_body:value'),), ('nonblank:issue_id', 'nonblank:key'),
)

ISSUES_METADATA_SET_TYPED_MANUAL_BINDING = GeneratedBinding(
    'issues.metadata.set_typed', 'default', ('issue', 'metadata', 'set'),
    (), (),
)

ISSUE_PULL_REQUESTS_BINDING = GeneratedBinding(
    'issues.pull_requests', 'default', ('issue', 'pull-requests'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUES_REORDER_MANUAL_BINDING = GeneratedBinding(
    'issues.reorder', 'default', ('issue', 'reorder'),
    (), (),
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

ISSUE_SEARCH_BINDING = GeneratedBinding(
    'issues.search', 'default', ('issue', 'search'),
    (GeneratedMapping('query', 'pos:0', 'query:q'),), ('nonblank:query',),
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

ISSUES_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'issues.update', 'default', ('issue', 'update'),
    (), (),
)

ISSUES_USAGE_MANUAL_BINDING = GeneratedBinding(
    'issues.usage', 'default', ('issue', 'usage'),
    (), (),
)

LABELS_CREATE_MANUAL_BINDING = GeneratedBinding(
    'labels.create', 'default', ('label', 'create'),
    (), (),
)

LABELS_DELETE_MANUAL_BINDING = GeneratedBinding(
    'labels.delete', 'default', ('label', 'delete'),
    (), (),
)

LABEL_GET_BINDING = GeneratedBinding(
    'labels.get', 'default', ('label', 'get'),
    (GeneratedMapping('label_id', 'pos:0', 'path:label_id'),), ('nonblank:label_id',),
)

LABEL_LIST_BINDING = GeneratedBinding(
    'labels.list', 'default', ('label', 'list'),
    (), (),
)

LABELS_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'labels.update', 'default', ('label', 'update'),
    (), (),
)

MAINTENANCE_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'maintenance.update', 'default', ('update',),
    (), (),
)

MAINTENANCE_VERSION_MANUAL_BINDING = GeneratedBinding(
    'maintenance.version', 'default', ('version',),
    (), (),
)

PROJECT_CREATE_BINDING = GeneratedBinding(
    'projects.create', 'default', ('project', 'create'),
    (GeneratedMapping('request.name', '--title', 'json_body:title'), GeneratedMapping('request.description', '--description', 'json_body:description'),), ('nonblank:request.name',),
)

PROJECTS_DELETE_MANUAL_BINDING = GeneratedBinding(
    'projects.delete', 'default', ('project', 'delete'),
    (), (),
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

SETUP_CLOUD_MANUAL_BINDING = GeneratedBinding(
    'setup.cloud', 'default', ('setup', 'cloud'),
    (), (),
)

SETUP_SELF_HOST_MANUAL_BINDING = GeneratedBinding(
    'setup.self_host', 'default', ('setup', 'self-host'),
    (), (),
)

SKILLS_CREATE_MANUAL_BINDING = GeneratedBinding(
    'skills.create', 'default', ('skill', 'create'),
    (), (),
)

SKILLS_DELETE_MANUAL_BINDING = GeneratedBinding(
    'skills.delete', 'default', ('skill', 'delete'),
    (), (),
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

SKILLS_IMPORT_FROM_URL_MANUAL_BINDING = GeneratedBinding(
    'skills.import_from_url', 'default', ('skill', 'import'),
    (), (),
)

SKILL_LIST_BINDING = GeneratedBinding(
    'skills.list', 'default', ('skill', 'list'),
    (), (),
)

SKILLS_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'skills.update', 'default', ('skill', 'update'),
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

WORKSPACES_SWITCH_MANUAL_BINDING = GeneratedBinding(
    'workspaces.switch', 'default', ('workspace', 'switch'),
    (), (),
)

WORKSPACES_UNWATCH_MANUAL_BINDING = GeneratedBinding(
    'workspaces.unwatch', 'default', ('workspace', 'unwatch'),
    (), (),
)

WORKSPACES_WATCH_MANUAL_BINDING = GeneratedBinding(
    'workspaces.watch', 'default', ('workspace', 'watch'),
    (), (),
)

OPERATION_BINDINGS: tuple[GeneratedBinding, ...] = (
    AGENTS_ARCHIVE_MANUAL_BINDING,
    AGENT_AVATAR_BINDING,
    AGENT_COPY_BINDING,
    AGENTS_CREATE_MANUAL_BINDING,
    AGENT_GET_BINDING,
    AGENT_LIST_BINDING,
    AGENTS_RESTORE_MANUAL_BINDING,
    AGENT_SKILLS_LIST_BINDING,
    AGENT_SKILLS_SET_BINDING,
    AGENT_TASKS_BINDING,
    AGENTS_UPDATE_MANUAL_BINDING,
    ATTACHMENT_DOWNLOAD_BINDING,
    ATTACHMENTS_DOWNLOAD_BYTES_MANUAL_BINDING,
    ATTACHMENT_UPLOAD_BINDING,
    ATTACHMENTS_UPLOAD_BYTES_MANUAL_BINDING,
    AUTH_LOGIN_MANUAL_BINDING,
    AUTH_LOGOUT_MANUAL_BINDING,
    AUTH_STATUS_MANUAL_BINDING,
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
    CONFIGURATION_GET_MANUAL_BINDING,
    CONFIGURATION_SET_MANUAL_BINDING,
    CONFIGURATION_SHOW_MANUAL_BINDING,
    DAEMON_DISK_USAGE_MANUAL_BINDING,
    DAEMON_LOGS_MANUAL_BINDING,
    DAEMON_RESTART_MANUAL_BINDING,
    DAEMON_START_MANUAL_BINDING,
    DAEMON_STATUS_MANUAL_BINDING,
    DAEMON_STOP_MANUAL_BINDING,
    ISSUES_ASSIGN_MANUAL_BINDING,
    ISSUE_CANCEL_TASK_BINDING,
    ISSUE_CHILDREN_BINDING,
    COMMENT_ADD_BINDING,
    COMMENT_DELETE_BINDING,
    COMMENT_LIST_BINDING,
    COMMENT_LIST_FLAT_BINDING,
    COMMENT_LIST_RECENT_BINDING,
    COMMENT_LIST_THREAD_BINDING,
    ISSUES_COMMENTS_REPLY_MANUAL_BINDING,
    ISSUES_COMMENTS_RESOLVE_MANUAL_BINDING,
    ISSUES_COMMENTS_UNRESOLVE_MANUAL_BINDING,
    ISSUE_CREATE_BINDING,
    ISSUES_DEPRIORITIZE_MANUAL_BINDING,
    ISSUE_GET_BINDING,
    ISSUE_LABELS_ADD_BINDING,
    ISSUE_LABELS_LIST_BINDING,
    ISSUE_LABELS_REMOVE_BINDING,
    ISSUE_LIST_BINDING,
    ISSUE_METADATA_DELETE_BINDING,
    ISSUE_METADATA_GET_BINDING,
    ISSUE_METADATA_LIST_BINDING,
    ISSUES_METADATA_QUERY_MANUAL_BINDING,
    ISSUE_METADATA_SET_BINDING,
    ISSUES_METADATA_SET_TYPED_MANUAL_BINDING,
    ISSUE_PULL_REQUESTS_BINDING,
    ISSUES_REORDER_MANUAL_BINDING,
    ISSUE_RERUN_BINDING,
    ISSUE_RUN_MESSAGES_BINDING,
    ISSUE_RUNS_BINDING,
    ISSUE_SEARCH_BINDING,
    ISSUE_STATUS_BINDING,
    ISSUE_SUBSCRIBERS_ADD_BINDING,
    ISSUE_SUBSCRIBERS_LIST_BINDING,
    ISSUE_SUBSCRIBERS_REMOVE_BINDING,
    ISSUES_UPDATE_MANUAL_BINDING,
    ISSUES_USAGE_MANUAL_BINDING,
    LABELS_CREATE_MANUAL_BINDING,
    LABELS_DELETE_MANUAL_BINDING,
    LABEL_GET_BINDING,
    LABEL_LIST_BINDING,
    LABELS_UPDATE_MANUAL_BINDING,
    MAINTENANCE_UPDATE_MANUAL_BINDING,
    MAINTENANCE_VERSION_MANUAL_BINDING,
    PROJECT_CREATE_BINDING,
    PROJECTS_DELETE_MANUAL_BINDING,
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
    SETUP_CLOUD_MANUAL_BINDING,
    SETUP_SELF_HOST_MANUAL_BINDING,
    SKILLS_CREATE_MANUAL_BINDING,
    SKILLS_DELETE_MANUAL_BINDING,
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    SKILL_GET_BINDING,
    SKILLS_IMPORT_FROM_URL_MANUAL_BINDING,
    SKILL_LIST_BINDING,
    SKILLS_UPDATE_MANUAL_BINDING,
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
    WORKSPACES_SWITCH_MANUAL_BINDING,
    WORKSPACES_UNWATCH_MANUAL_BINDING,
    WORKSPACES_WATCH_MANUAL_BINDING,
)

OPERATION_CONVENTIONS: tuple[GeneratedConvention, ...] = (
    GeneratedConvention(
        'agents.archive', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.archive_command',
    ),
    GeneratedConvention(
        'agents.avatar', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.avatar_command',
    ),
    GeneratedConvention(
        'agents.copy', 'default',
        'create', 'agent',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.copy_command',
    ),
    GeneratedConvention(
        'agents.create', 'default',
        'create', 'agent',
        'AgentCreateRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.agents.AgentResource.create_command',
    ),
    GeneratedConvention(
        'agents.get', 'default',
        'retrieve', 'agent',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.get_command',
    ),
    GeneratedConvention(
        'agents.list', 'default',
        'collection', 'page_agent',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.list_command',
    ),
    GeneratedConvention(
        'agents.restore', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.restore_command',
    ),
    GeneratedConvention(
        'agents.skills.list', 'default',
        'collection', 'page_agent_skills',
        None, 'direct',
        (), 'multica_py.resources.agent_skills.AgentSkillResource.list_command',
    ),
    GeneratedConvention(
        'agents.skills.set', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.agent_skills.AgentSkillResource.set_command',
    ),
    GeneratedConvention(
        'agents.tasks', 'default',
        'collection', 'page_task_runs',
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.tasks_command',
    ),
    GeneratedConvention(
        'agents.update', 'default',
        'update', 'agent',
        'AgentUpdateRequest', 'dual_optional',
        ('omit',), 'multica_py.resources.agents.AgentResource.update_command',
    ),
    GeneratedConvention(
        'attachments.download', 'default',
        'scalar', 'path',
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.download_command',
    ),
    GeneratedConvention(
        'attachments.download_bytes', 'default',
        'retrieve', 'bytes',
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.download_bytes_command',
    ),
    GeneratedConvention(
        'attachments.upload', 'default',
        'retrieve', 'attachment_result',
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.upload_command',
    ),
    GeneratedConvention(
        'attachments.upload_bytes', 'default',
        'action', 'attachment_result',
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.upload_bytes_command',
    ),
    GeneratedConvention(
        'auth.login', 'default',
        'action', 'action_result_str',
        None, 'direct',
        (), 'multica_py.resources.auth.AuthResource.login_command',
    ),
    GeneratedConvention(
        'auth.logout', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.auth.AuthResource.logout_command',
    ),
    GeneratedConvention(
        'auth.status', 'default',
        'scalar', 'scalar_str',
        None, 'direct',
        (), 'multica_py.resources.auth.AuthResource.status_command',
    ),
    GeneratedConvention(
        'autopilots.create', 'default',
        'create', 'autopilot',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.create_command',
    ),
    GeneratedConvention(
        'autopilots.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.delete_command',
    ),
    GeneratedConvention(
        'autopilots.get', 'default',
        'retrieve', 'autopilot',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.get_command',
    ),
    GeneratedConvention(
        'autopilots.history', 'default',
        'collection', 'autopilot_run_list_page',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.history_command',
    ),
    GeneratedConvention(
        'autopilots.list', 'default',
        'collection', 'autopilot_list_page',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.list_command',
    ),
    GeneratedConvention(
        'autopilots.trigger', 'default',
        'retrieve', 'autopilot_run',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_add', 'default',
        'retrieve', 'autopilot_trigger',
        'AutopilotTriggerCreate', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.autopilots.AutopilotResource.trigger_add_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_delete_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_update', 'default',
        'retrieve', 'autopilot_trigger',
        'AutopilotTriggerUpdate', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.autopilots.AutopilotResource.trigger_update_command',
    ),
    GeneratedConvention(
        'autopilots.update', 'default',
        'update', 'autopilot',
        'AutopilotUpdateRequest', 'dual_optional',
        ('omit',), 'multica_py.resources.autopilots.AutopilotResource.update_command',
    ),
    GeneratedConvention(
        'configuration.get', 'default',
        'scalar', 'scalar_str',
        None, 'direct',
        (), 'multica_py.resources.configuration.ConfigurationResource.get_command',
    ),
    GeneratedConvention(
        'configuration.set', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.configuration.ConfigurationResource.set_command',
    ),
    GeneratedConvention(
        'configuration.show', 'default',
        'mapping', 'mapping_config',
        None, 'direct',
        (), 'multica_py.resources.configuration.ConfigurationResource.show_command',
    ),
    GeneratedConvention(
        'daemon.disk_usage', 'default',
        'collection', 'page_daemon_disk_usage',
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.disk_usage_command',
    ),
    GeneratedConvention(
        'daemon.logs', 'default',
        'process', 'process',
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.logs_command',
    ),
    GeneratedConvention(
        'daemon.restart', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.restart_command',
    ),
    GeneratedConvention(
        'daemon.start', 'default',
        'process', 'process',
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.start_command',
    ),
    GeneratedConvention(
        'daemon.status', 'default',
        'retrieve', 'runtime_definition',
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.status_command',
    ),
    GeneratedConvention(
        'daemon.stop', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.stop_command',
    ),
    GeneratedConvention(
        'issues.assign', 'default',
        'action', 'action_result_none',
        'IssueAssignmentRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issues.IssueResource.assign_command',
    ),
    GeneratedConvention(
        'issues.cancel_task', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.cancel_task_command',
    ),
    GeneratedConvention(
        'issues.children', 'default',
        'collection', 'issue_children_result',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.children_command',
    ),
    GeneratedConvention(
        'issues.comments.add', 'default',
        'retrieve', 'comment',
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.add_command',
    ),
    GeneratedConvention(
        'issues.comments.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.delete_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'direct',
        'collection', 'page_comments',
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.list_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'flat',
        'collection', 'comment_page',
        'CommentListFlatRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issue_comments.IssueCommentResource.list_flat_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'recent',
        'collection', 'comment_thread_page',
        'CommentListRecentRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issue_comments.IssueCommentResource.list_recent_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'thread',
        'collection', 'comment_page',
        'CommentListThreadRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issue_comments.IssueCommentResource.list_thread_command',
    ),
    GeneratedConvention(
        'issues.comments.reply', 'default',
        'create', 'comment',
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.reply_command',
    ),
    GeneratedConvention(
        'issues.comments.resolve', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.resolve_command',
    ),
    GeneratedConvention(
        'issues.comments.unresolve', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.unresolve_command',
    ),
    GeneratedConvention(
        'issues.create', 'default',
        'create', 'issue',
        'IssueCreateRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issues.IssueResource.create_command',
    ),
    GeneratedConvention(
        'issues.deprioritize', 'default',
        'action', 'action_result_str',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.deprioritize_command',
    ),
    GeneratedConvention(
        'issues.get', 'default',
        'retrieve', 'issue',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.get_command',
    ),
    GeneratedConvention(
        'issues.labels.add', 'default',
        'collection', 'page_labels',
        None, 'direct',
        (), 'multica_py.resources.issue_labels.IssueLabelResource.add_command',
    ),
    GeneratedConvention(
        'issues.labels.list', 'default',
        'collection', 'page_labels',
        None, 'direct',
        (), 'multica_py.resources.issue_labels.IssueLabelResource.list_command',
    ),
    GeneratedConvention(
        'issues.labels.remove', 'default',
        'collection', 'page_labels',
        None, 'direct',
        (), 'multica_py.resources.issue_labels.IssueLabelResource.remove_command',
    ),
    GeneratedConvention(
        'issues.list', 'default',
        'collection', 'issue_list_page',
        'IssueListFilter', 'dual_optional',
        ('omit',), 'multica_py.resources.issues.IssueResource.list_command',
    ),
    GeneratedConvention(
        'issues.metadata.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.delete_command',
    ),
    GeneratedConvention(
        'issues.metadata.get', 'default',
        'retrieve', 'metadata_entries',
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.get_command',
    ),
    GeneratedConvention(
        'issues.metadata.list', 'default',
        'collection', 'metadata_entries',
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.list_command',
    ),
    GeneratedConvention(
        'issues.metadata.query', 'default',
        'mapping', 'metadata_entries',
        'MetadataListRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issue_metadata.IssueMetadataResource.query_command',
    ),
    GeneratedConvention(
        'issues.metadata.set', 'default',
        'update', 'metadata_entries',
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.set_command',
    ),
    GeneratedConvention(
        'issues.metadata.set_typed', 'default',
        'action', 'action_result_none',
        'MetadataSetRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issue_metadata.IssueMetadataResource.set_typed_command',
    ),
    GeneratedConvention(
        'issues.pull_requests', 'default',
        'collection', 'page_linked_pull_requests',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.pull_requests_command',
    ),
    GeneratedConvention(
        'issues.reorder', 'default',
        'action', 'action_result_none',
        'IssueReorderRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.issues.IssueResource.reorder_command',
    ),
    GeneratedConvention(
        'issues.rerun', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.rerun_command',
    ),
    GeneratedConvention(
        'issues.run_messages', 'default',
        'collection', 'page_run_messages',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.run_messages_command',
    ),
    GeneratedConvention(
        'issues.runs', 'default',
        'collection', 'page_task_runs',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.runs_command',
    ),
    GeneratedConvention(
        'issues.search', 'default',
        'collection', 'page_issue_summaries',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.search_command',
    ),
    GeneratedConvention(
        'issues.set_status', 'default',
        'update', 'issue',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.set_status_command',
    ),
    GeneratedConvention(
        'issues.subscribers.add', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issue_subscribers.IssueSubscriberResource.add_command',
    ),
    GeneratedConvention(
        'issues.subscribers.list', 'default',
        'collection', 'page_subscribers',
        None, 'direct',
        (), 'multica_py.resources.issue_subscribers.IssueSubscriberResource.list_command',
    ),
    GeneratedConvention(
        'issues.subscribers.remove', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.issue_subscribers.IssueSubscriberResource.remove_command',
    ),
    GeneratedConvention(
        'issues.update', 'default',
        'update', 'issue',
        'IssueUpdateRequest', 'dual_optional',
        ('omit',), 'multica_py.resources.issues.IssueResource.update_command',
    ),
    GeneratedConvention(
        'issues.usage', 'default',
        'collection', 'page_issue_usage',
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.usage_command',
    ),
    GeneratedConvention(
        'labels.create', 'default',
        'create', 'labels',
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.create_command',
    ),
    GeneratedConvention(
        'labels.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.delete_command',
    ),
    GeneratedConvention(
        'labels.get', 'default',
        'retrieve', 'labels',
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.get_command',
    ),
    GeneratedConvention(
        'labels.list', 'default',
        'collection', 'page_labels',
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.list_command',
    ),
    GeneratedConvention(
        'labels.update', 'default',
        'update', 'labels',
        'LabelUpdateRequest', 'dual_optional',
        ('omit',), 'multica_py.resources.labels.LabelResource.update_command',
    ),
    GeneratedConvention(
        'maintenance.update', 'default',
        'process', 'process',
        None, 'direct',
        (), 'multica_py.resources.maintenance.MaintenanceResource.update_command',
    ),
    GeneratedConvention(
        'maintenance.version', 'default',
        'scalar', 'scalar_str',
        None, 'direct',
        (), 'multica_py.resources.maintenance.MaintenanceResource.version_command',
    ),
    GeneratedConvention(
        'projects.create', 'default',
        'create', 'project',
        'ProjectCreateRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.projects.ProjectResource.create_command',
    ),
    GeneratedConvention(
        'projects.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.delete_command',
    ),
    GeneratedConvention(
        'projects.get', 'default',
        'retrieve', 'project',
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.get_command',
    ),
    GeneratedConvention(
        'projects.list', 'default',
        'collection', 'page_project',
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.list_command',
    ),
    GeneratedConvention(
        'projects.resources.add_local_directory', 'default',
        'retrieve', 'project_resource',
        'ProjectResourceAddLocalDirectoryRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.project_resources.ProjectResourceCollection.add_local_directory_command',
    ),
    GeneratedConvention(
        'projects.resources.list', 'default',
        'collection', 'page_project_resources',
        None, 'direct',
        (), 'multica_py.resources.project_resources.ProjectResourceCollection.list_command',
    ),
    GeneratedConvention(
        'projects.resources.remove', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.project_resources.ProjectResourceCollection.remove_command',
    ),
    GeneratedConvention(
        'projects.resources.update_local_directory', 'default',
        'retrieve', 'project_resource',
        'ProjectResourceUpdateLocalDirectoryRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.project_resources.ProjectResourceCollection.update_local_directory_command',
    ),
    GeneratedConvention(
        'projects.set_status', 'default',
        'update', 'project',
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.set_status_command',
    ),
    GeneratedConvention(
        'projects.update', 'default',
        'update', 'project',
        'ProjectUpdateRequest', 'dual_optional',
        ('omit',), 'multica_py.resources.projects.ProjectResource.update_command',
    ),
    GeneratedConvention(
        'repositories.add', 'default',
        'action', 'action_result_repository_mutation_result',
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.add_command',
    ),
    GeneratedConvention(
        'repositories.list', 'default',
        'collection', 'page_repository_records',
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.list_command',
    ),
    GeneratedConvention(
        'repositories.remove', 'default',
        'action', 'action_result_repository_mutation_result',
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.remove_command',
    ),
    GeneratedConvention(
        'runtimes.activity', 'default',
        'collection', 'page_runtime_activity',
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.activity_command',
    ),
    GeneratedConvention(
        'runtimes.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.delete_command',
    ),
    GeneratedConvention(
        'runtimes.list', 'default',
        'collection', 'page_runtime_definitions',
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.list_command',
    ),
    GeneratedConvention(
        'runtimes.rename', 'default',
        'update', 'runtime_definition',
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.rename_command',
    ),
    GeneratedConvention(
        'runtimes.update', 'default',
        'action', 'action_result_runtime_update_result',
        'RuntimeUpdate', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.runtimes.RuntimeResource.update_command',
    ),
    GeneratedConvention(
        'runtimes.usage', 'default',
        'collection', 'page_runtime_usage',
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.usage_command',
    ),
    GeneratedConvention(
        'setup.cloud', 'default',
        'process', 'process',
        None, 'direct',
        (), 'multica_py.resources.setup.SetupResource.cloud_command',
    ),
    GeneratedConvention(
        'setup.self_host', 'default',
        'process', 'process',
        None, 'direct',
        (), 'multica_py.resources.setup.SetupResource.self_host_command',
    ),
    GeneratedConvention(
        'skills.create', 'default',
        'create', 'skill',
        'SkillCreateRequest', 'dual_required',
        ('required_nonnull',), 'multica_py.resources.skills.SkillResource.create_command',
    ),
    GeneratedConvention(
        'skills.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.delete_command',
    ),
    GeneratedConvention(
        'skills.files.delete', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.skill_files.SkillFileResource.delete_command',
    ),
    GeneratedConvention(
        'skills.files.list', 'default',
        'collection', 'page_skill_files',
        None, 'direct',
        (), 'multica_py.resources.skill_files.SkillFileResource.list_command',
    ),
    GeneratedConvention(
        'skills.files.upsert', 'default',
        'retrieve', 'skill_file',
        None, 'direct',
        (), 'multica_py.resources.skill_files.SkillFileResource.upsert_command',
    ),
    GeneratedConvention(
        'skills.get', 'default',
        'retrieve', 'skill',
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.get_command',
    ),
    GeneratedConvention(
        'skills.import_from_url', 'default',
        'create', 'skill',
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.import_from_url_command',
    ),
    GeneratedConvention(
        'skills.list', 'default',
        'collection', 'page_skill',
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.list_command',
    ),
    GeneratedConvention(
        'skills.update', 'default',
        'update', 'skill',
        'SkillUpdateRequest', 'dual_optional',
        ('omit',), 'multica_py.resources.skills.SkillResource.update_command',
    ),
    GeneratedConvention(
        'squads.get', 'default',
        'retrieve', 'squad',
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.get_command',
    ),
    GeneratedConvention(
        'squads.list', 'default',
        'collection', 'page_squad',
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.list_command',
    ),
    GeneratedConvention(
        'squads.members.add', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.squad_members.SquadMemberResource.add_command',
    ),
    GeneratedConvention(
        'squads.members.list', 'default',
        'collection', 'page_squad_members',
        None, 'direct',
        (), 'multica_py.resources.squad_members.SquadMemberResource.list_command',
    ),
    GeneratedConvention(
        'squads.members.remove', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.squad_members.SquadMemberResource.remove_command',
    ),
    GeneratedConvention(
        'users.profile_get', 'default',
        'retrieve', 'user_profile',
        None, 'direct',
        (), 'multica_py.resources.users.UserResource.profile_get_command',
    ),
    GeneratedConvention(
        'users.profile_update', 'default',
        'update', 'user_profile',
        'UserProfileUpdate', 'dual_optional',
        ('omit',), 'multica_py.resources.users.UserResource.profile_update_command',
    ),
    GeneratedConvention(
        'workspaces.get', 'default',
        'retrieve', 'workspace',
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.get_command',
    ),
    GeneratedConvention(
        'workspaces.list', 'default',
        'collection', 'page_workspace',
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.list_command',
    ),
    GeneratedConvention(
        'workspaces.members.list', 'default',
        'collection', 'page_workspace_members',
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.members_command',
    ),
    GeneratedConvention(
        'workspaces.switch', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.switch_command',
    ),
    GeneratedConvention(
        'workspaces.unwatch', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.unwatch_command',
    ),
    GeneratedConvention(
        'workspaces.watch', 'default',
        'action', 'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.watch_command',
    ),
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

def validate_positive_max_concurrent_tasks(value: object) -> None:
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

__all__ = ('TARGET_VERSION', 'MIN_CLI_VERSION', 'MAX_CLI_VERSION', 'AutopilotExecutionMode', 'IssueSort', 'SortDirection', 'GeneratedMapping', 'GeneratedBinding', 'GeneratedConvention', 'AGENT_AVATAR_BINDING', 'AGENT_COPY_BINDING', 'AGENT_GET_BINDING', 'AGENT_LIST_BINDING', 'AGENT_SKILLS_LIST_BINDING', 'AGENT_SKILLS_SET_BINDING', 'AGENT_TASKS_BINDING', 'AGENTS_ARCHIVE_MANUAL_BINDING', 'AGENTS_CREATE_MANUAL_BINDING', 'AGENTS_RESTORE_MANUAL_BINDING', 'AGENTS_UPDATE_MANUAL_BINDING', 'ATTACHMENT_DOWNLOAD_BINDING', 'ATTACHMENT_UPLOAD_BINDING', 'ATTACHMENTS_DOWNLOAD_BYTES_MANUAL_BINDING', 'ATTACHMENTS_UPLOAD_BYTES_MANUAL_BINDING', 'AUTH_LOGIN_MANUAL_BINDING', 'AUTH_LOGOUT_MANUAL_BINDING', 'AUTH_STATUS_MANUAL_BINDING', 'AUTOPILOT_CREATE_BINDING', 'AUTOPILOT_DELETE_BINDING', 'AUTOPILOT_GET_BINDING', 'AUTOPILOT_HISTORY_BINDING', 'AUTOPILOT_LIST_BINDING', 'AUTOPILOT_TRIGGER_BINDING', 'AUTOPILOT_TRIGGER_ADD_BINDING', 'AUTOPILOT_TRIGGER_DELETE_BINDING', 'AUTOPILOT_TRIGGER_UPDATE_BINDING', 'AUTOPILOT_UPDATE_BINDING', 'COMMENT_ADD_BINDING', 'COMMENT_DELETE_BINDING', 'COMMENT_LIST_BINDING', 'COMMENT_LIST_FLAT_BINDING', 'COMMENT_LIST_RECENT_BINDING', 'COMMENT_LIST_THREAD_BINDING', 'CONFIGURATION_GET_MANUAL_BINDING', 'CONFIGURATION_SET_MANUAL_BINDING', 'CONFIGURATION_SHOW_MANUAL_BINDING', 'DAEMON_DISK_USAGE_MANUAL_BINDING', 'DAEMON_LOGS_MANUAL_BINDING', 'DAEMON_RESTART_MANUAL_BINDING', 'DAEMON_START_MANUAL_BINDING', 'DAEMON_STATUS_MANUAL_BINDING', 'DAEMON_STOP_MANUAL_BINDING', 'ISSUE_CANCEL_TASK_BINDING', 'ISSUE_CHILDREN_BINDING', 'ISSUE_CREATE_BINDING', 'ISSUE_GET_BINDING', 'ISSUE_LABELS_ADD_BINDING', 'ISSUE_LABELS_LIST_BINDING', 'ISSUE_LABELS_REMOVE_BINDING', 'ISSUE_LIST_BINDING', 'ISSUE_METADATA_DELETE_BINDING', 'ISSUE_METADATA_GET_BINDING', 'ISSUE_METADATA_LIST_BINDING', 'ISSUE_METADATA_SET_BINDING', 'ISSUE_PULL_REQUESTS_BINDING', 'ISSUE_RERUN_BINDING', 'ISSUE_RUN_MESSAGES_BINDING', 'ISSUE_RUNS_BINDING', 'ISSUE_SEARCH_BINDING', 'ISSUE_STATUS_BINDING', 'ISSUE_SUBSCRIBERS_ADD_BINDING', 'ISSUE_SUBSCRIBERS_LIST_BINDING', 'ISSUE_SUBSCRIBERS_REMOVE_BINDING', 'ISSUES_ASSIGN_MANUAL_BINDING', 'ISSUES_COMMENTS_REPLY_MANUAL_BINDING', 'ISSUES_COMMENTS_RESOLVE_MANUAL_BINDING', 'ISSUES_COMMENTS_UNRESOLVE_MANUAL_BINDING', 'ISSUES_DEPRIORITIZE_MANUAL_BINDING', 'ISSUES_METADATA_QUERY_MANUAL_BINDING', 'ISSUES_METADATA_SET_TYPED_MANUAL_BINDING', 'ISSUES_REORDER_MANUAL_BINDING', 'ISSUES_UPDATE_MANUAL_BINDING', 'ISSUES_USAGE_MANUAL_BINDING', 'LABEL_GET_BINDING', 'LABEL_LIST_BINDING', 'LABELS_CREATE_MANUAL_BINDING', 'LABELS_DELETE_MANUAL_BINDING', 'LABELS_UPDATE_MANUAL_BINDING', 'MAINTENANCE_UPDATE_MANUAL_BINDING', 'MAINTENANCE_VERSION_MANUAL_BINDING', 'PROJECT_CREATE_BINDING', 'PROJECT_GET_BINDING', 'PROJECT_LIST_BINDING', 'PROJECT_RESOURCE_ADD_BINDING', 'PROJECT_RESOURCE_LIST_BINDING', 'PROJECT_RESOURCE_REMOVE_BINDING', 'PROJECT_RESOURCE_UPDATE_BINDING', 'PROJECT_STATUS_BINDING', 'PROJECT_UPDATE_BINDING', 'PROJECTS_DELETE_MANUAL_BINDING', 'REPOSITORIES_ADD_BINDING', 'REPOSITORIES_LIST_BINDING', 'REPOSITORIES_REMOVE_BINDING', 'RUNTIME_ACTIVITY_BINDING', 'RUNTIME_DELETE_BINDING', 'RUNTIME_LIST_BINDING', 'RUNTIME_RENAME_BINDING', 'RUNTIME_UPDATE_BINDING', 'RUNTIME_USAGE_BINDING', 'SETUP_CLOUD_MANUAL_BINDING', 'SETUP_SELF_HOST_MANUAL_BINDING', 'SKILL_FILES_DELETE_BINDING', 'SKILL_FILES_LIST_BINDING', 'SKILL_FILES_UPSERT_BINDING', 'SKILL_GET_BINDING', 'SKILL_LIST_BINDING', 'SKILLS_CREATE_MANUAL_BINDING', 'SKILLS_DELETE_MANUAL_BINDING', 'SKILLS_IMPORT_FROM_URL_MANUAL_BINDING', 'SKILLS_UPDATE_MANUAL_BINDING', 'SQUAD_GET_BINDING', 'SQUAD_LIST_BINDING', 'SQUAD_MEMBERS_ADD_BINDING', 'SQUAD_MEMBERS_LIST_BINDING', 'SQUAD_MEMBERS_REMOVE_BINDING', 'USER_PROFILE_GET_BINDING', 'USER_PROFILE_UPDATE_BINDING', 'WORKSPACE_GET_BINDING', 'WORKSPACE_LIST_BINDING', 'WORKSPACE_MEMBERS_LIST_BINDING', 'WORKSPACES_SWITCH_MANUAL_BINDING', 'WORKSPACES_UNWATCH_MANUAL_BINDING', 'WORKSPACES_WATCH_MANUAL_BINDING', 'OPERATION_BINDINGS', 'OPERATION_CONVENTIONS', 'normalize_optional_label', 'validate_comment_cursor', 'validate_description_input', 'validate_issue_sort', 'validate_issue_status', 'validate_nonblank', 'validate_nonnegative_limit', 'validate_positive_limit', 'validate_positive_max_concurrent_tasks', 'validate_project_description', 'validate_project_status', 'validate_project_update', 'validate_resource_update', 'validate_thread_cursor_limit')

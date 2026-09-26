from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

TARGET_VERSION = '0.5.3'
MIN_CLI_VERSION = '0.4.42'
MAX_CLI_VERSION = '0.5.4'

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

class LabelResourceType(StrEnum):
    issue = 'issue'
    skill = 'skill'

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
    minimum_cli_version: str | None = None

@dataclass(frozen=True)
class GeneratedConvention:
    operation_id: str
    entrypoint_id: str
    category: str
    response_id: str
    fallback_response_id: str | None
    typed_input_id: str | None
    input_mode: str
    presence_policy_ids: tuple[str, ...]
    command_symbol: str

@dataclass(frozen=True)
class GeneratedInventoryItem:
    inventory_id: str
    kind: str
    identity: str
    disposition: str
    public_symbol: str | None
    transport: str | None
    compatibility: str

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
    (GeneratedMapping('model', '--model', 'json_body:model'), GeneratedMapping('thinking_level', '--thinking-level', 'json_body:thinking_level'), GeneratedMapping('conversation_starters', '--conversation-starters', 'json_body:conversation_starters'),), (),
)

AGENTS_ENV_GET_BINDING = GeneratedBinding(
    'agents.env.get', 'default', ('agent', 'env', 'get'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), (),
    minimum_cli_version='0.5.3',
)

AGENTS_ENV_SET_BINDING = GeneratedBinding(
    'agents.env.set', 'default', ('agent', 'env', 'set'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('custom_env', '--custom-env', 'json_body:custom_env'),), (),
    minimum_cli_version='0.5.3',
)

AGENT_GET_BINDING = GeneratedBinding(
    'agents.get', 'default', ('agent', 'get'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), ('nonblank:agent_id',),
)

AGENT_LIST_BINDING = GeneratedBinding(
    'agents.list', 'default', ('agent', 'list'),
    (), (),
)

AGENT_MCP_ADD_BINDING = GeneratedBinding(
    'agents.mcp.add', 'default', ('agent', 'mcp', 'add'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'json_body:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_ADD_BOUND_BINDING = GeneratedBinding(
    'agents.mcp.add_bound', 'default', ('agent', 'mcp', 'add'),
    (GeneratedMapping('self.id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'json_body:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_DISABLE_BINDING = GeneratedBinding(
    'agents.mcp.disable', 'default', ('agent', 'mcp', 'disable'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'path:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_DISABLE_BOUND_BINDING = GeneratedBinding(
    'agents.mcp.disable_bound', 'default', ('agent', 'mcp', 'disable'),
    (GeneratedMapping('self.id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'path:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_ENABLE_BINDING = GeneratedBinding(
    'agents.mcp.enable', 'default', ('agent', 'mcp', 'enable'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'path:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_ENABLE_BOUND_BINDING = GeneratedBinding(
    'agents.mcp.enable_bound', 'default', ('agent', 'mcp', 'enable'),
    (GeneratedMapping('self.id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'path:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_LIST_BINDING = GeneratedBinding(
    'agents.mcp.list', 'default', ('agent', 'mcp', 'list'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'),), ('nonblank:agent_id',),
)

AGENT_MCP_REMOVE_BINDING = GeneratedBinding(
    'agents.mcp.remove', 'default', ('agent', 'mcp', 'remove'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'path:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENT_MCP_REMOVE_BOUND_BINDING = GeneratedBinding(
    'agents.mcp.remove_bound', 'default', ('agent', 'mcp', 'remove'),
    (GeneratedMapping('self.id', 'pos:0', 'path:agent_id'), GeneratedMapping('server_id', 'pos:1', 'path:server_id'),), ('nonblank:agent_id', 'nonblank:server_id'),
)

AGENTS_RESTORE_MANUAL_BINDING = GeneratedBinding(
    'agents.restore', 'default', ('agent', 'restore'),
    (), (),
)

AGENTS_SKILLS_ADD_BINDING = GeneratedBinding(
    'agents.skills.add', 'default', ('agent', 'skills', 'add'),
    (GeneratedMapping('agent_id', 'pos:0', 'path:agent_id'), GeneratedMapping('skill_ids', '--skill-ids', 'json_body:skill_ids'),), (),
    minimum_cli_version='0.5.3',
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
    (GeneratedMapping('runtime_id', '--runtime-id', 'json_body:runtime_id'), GeneratedMapping('model', '--model', 'json_body:model'), GeneratedMapping('thinking_level', '--thinking-level', 'json_body:thinking_level'), GeneratedMapping('conversation_starters', '--conversation-starters', 'json_body:conversation_starters'),), (),
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
    'auth.login', 'default', ('login',),
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
    (GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('agent', '--agent', 'json_body:assignee_id'), GeneratedMapping('execution_mode', '--mode', 'json_body:execution_mode'), GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('issue_title_template', '--issue-title-template', 'json_body:issue_title_template'), GeneratedMapping('subscribers', 'repeat:--subscriber', 'json_body:subscribers'),), ('nonblank:title', 'nonblank:agent'),
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
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('kind', '--kind', 'json_body:kind'), GeneratedMapping('cron_expression', '--cron', 'json_body:cron_expression'), GeneratedMapping('timezone', '--timezone', 'json_body:timezone'), GeneratedMapping('label', '--label', 'json_body:label'),), ('nonblank:autopilot_id',),
)

AUTOPILOT_TRIGGER_DELETE_BINDING = GeneratedBinding(
    'autopilots.trigger_delete', 'default', ('autopilot', 'trigger-delete'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('trigger_id', 'pos:1', 'path:trigger_id'),), ('nonblank:autopilot_id', 'nonblank:trigger_id'),
)

AUTOPILOTS_TRIGGER_LIST_BINDING = GeneratedBinding(
    'autopilots.trigger_list', 'default', ('autopilot', 'trigger-list'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'),), (),
    minimum_cli_version='0.5.3',
)

AUTOPILOT_TRIGGER_ROTATE_URL_BINDING = GeneratedBinding(
    'autopilots.trigger_rotate_url', 'default', ('autopilot', 'trigger-rotate-url'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('trigger_id', 'pos:1', 'path:trigger_id'), GeneratedMapping('yes', '--yes', 'local_control:yes'),), (),
    minimum_cli_version='0.5.3',
)

AUTOPILOT_TRIGGER_UPDATE_BINDING = GeneratedBinding(
    'autopilots.trigger_update', 'default', ('autopilot', 'trigger-update'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('trigger_id', 'pos:1', 'path:trigger_id'), GeneratedMapping('cron_expression', '--cron', 'json_body:cron_expression'), GeneratedMapping('timezone', '--timezone', 'json_body:timezone'), GeneratedMapping('label', '--label', 'json_body:label'), GeneratedMapping('enabled', '--enabled', 'json_body:enabled'),), ('nonblank:autopilot_id', 'nonblank:trigger_id'),
)

AUTOPILOT_UPDATE_BINDING = GeneratedBinding(
    'autopilots.update', 'default', ('autopilot', 'update'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('agent', '--agent', 'json_body:assignee_id'), GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('status', '--status', 'json_body:status'), GeneratedMapping('execution_mode', '--mode', 'json_body:execution_mode'), GeneratedMapping('issue_title_template', '--issue-title-template', 'json_body:issue_title_template'), GeneratedMapping('subscribers', 'repeat:--subscriber', 'json_body:subscribers'), GeneratedMapping('subscribers', '--clear-subscribers', 'json_body:clear_subscribers'),), ('nonblank:autopilot_id',),
)

CHAT_HISTORY_BINDING = GeneratedBinding(
    'chats.history', 'default', ('chat', 'history'),
    (GeneratedMapping('limit', '--limit', 'query:limit'), GeneratedMapping('before', '--before', 'query:before'),), (),
    minimum_cli_version='0.5.3',
)

CHAT_THREAD_BINDING = GeneratedBinding(
    'chats.thread', 'default', ('chat', 'thread'),
    (GeneratedMapping('thread_id', 'pos:0', 'query:id'), GeneratedMapping('limit', '--limit', 'query:limit'), GeneratedMapping('before', '--before', 'query:before'),), (),
    minimum_cli_version='0.5.3',
)

CLI_COMMAND_BINDING = GeneratedBinding(
    'cli.command', 'default', (),
    (), (),
)

CONFIGURATION_GET_MANUAL_BINDING = GeneratedBinding(
    'configuration.get', 'default', ('config', 'show'),
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

ISSUES_ASSIGN_BOUND_BINDING = GeneratedBinding(
    'issues.assign_bound', 'default', (),
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
    minimum_cli_version='0.4.44',
)

COMMENT_LIST_BINDING = GeneratedBinding(
    'issues.comments.list', 'direct', ('issue', 'comment', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

COMMENT_LIST_FLAT_BINDING = GeneratedBinding(
    'issues.comments.list', 'flat', ('issue', 'comment', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('since', '--since', 'query:since'),), (),
)

COMMENT_LIST_RECENT_BINDING = GeneratedBinding(
    'issues.comments.list', 'recent', ('issue', 'comment', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('limit', '--recent', 'query:recent'), GeneratedMapping('cursor.before', '--before', 'query:before'), GeneratedMapping('cursor.before_id', '--before-id', 'query:before_id'),), ('cursor_pair', 'limit_positive'),
)

COMMENT_LIST_THREAD_BINDING = GeneratedBinding(
    'issues.comments.list', 'thread', ('issue', 'comment', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('thread_id', '--thread', 'query:thread'), GeneratedMapping('limit', '--tail', 'query:tail'), GeneratedMapping('cursor.before', '--before', 'query:before'), GeneratedMapping('cursor.before_id', '--before-id', 'query:before_id'),), ('cursor_pair', 'cursor_requires_limit', 'limit_nonnegative'),
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

COMMENT_UPDATE_BINDING = GeneratedBinding(
    'issues.comments.update', 'default', ('issue', 'comment', 'update'),
    (GeneratedMapping('comment_id', 'pos:0', 'path:comment_id'), GeneratedMapping('body', '--content', 'json_body:content'), GeneratedMapping('expected_revision', '--expected-revision', 'json_body:expected_revision'),), ('nonblank:comment_id', 'positive_int:expected_revision'),
    minimum_cli_version='0.5.0',
)

ISSUE_CREATE_BINDING = GeneratedBinding(
    'issues.create', 'default', ('issue', 'create'),
    (GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'local_control:description'), GeneratedMapping('description_file', '--description-file', 'local_control:description'), GeneratedMapping('description_input', 'description-selector', 'local_control:description'), GeneratedMapping('priority', '--priority', 'json_body:priority'), GeneratedMapping('assignee_id', '--assignee-id', 'json_body:assignee_id'), GeneratedMapping('project', '--project', 'json_body:project_id'), GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('parent_id', '--parent', 'json_body:parent_issue_id'), GeneratedMapping('label_ids', 'repeat:issue label add', 'json_body:label_id'), GeneratedMapping('properties', 'repeat:--property', 'json_body:properties'),), ('nonblank:title', 'description_exactly_one'),
    minimum_cli_version='0.5.2',
)

ISSUE_GET_BINDING = GeneratedBinding(
    'issues.get', 'default', ('issue', 'get'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('resolve_properties', '--resolve-properties', 'query:resolve_properties'),), ('nonblank:issue_id',),
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
    (GeneratedMapping('filter.status', '--status', 'query:status'), GeneratedMapping('filter.priority', '--priority', 'query:priority'), GeneratedMapping('filter.assignee_id', '--assignee-id', 'query:assignee_id'), GeneratedMapping('filter.limit', '--limit', 'query:limit'), GeneratedMapping('filter.offset', '--offset', 'query:offset'), GeneratedMapping('filter.project_id', '--project', 'query:project_id'), GeneratedMapping('filter.metadata', 'repeat:--metadata', 'query:metadata'), GeneratedMapping('filter.sort', '--sort', 'query:sort'), GeneratedMapping('filter.direction', '--direction', 'query:direction'), GeneratedMapping('filter.property_filters', 'repeat:--property', 'query:properties'), GeneratedMapping('filter.fields', '--fields', 'query:fields'), GeneratedMapping('filter.resolve_properties', '--resolve-properties', 'query:resolve_properties'),), ('direction_requires_sort', 'offset_nonnegative', 'position_forbids_direction'),
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

ISSUES_MOVE_AFTER_BINDING = GeneratedBinding(
    'issues.move_after', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('other_issue', '--after', 'path:after_id'),), (),
)

ISSUES_MOVE_AFTER_BOUND_BINDING = GeneratedBinding(
    'issues.move_after_bound', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('other_issue', '--after', 'path:after_id'),), (),
)

ISSUES_MOVE_BEFORE_BINDING = GeneratedBinding(
    'issues.move_before', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('other_issue', '--before', 'path:before_id'),), (),
)

ISSUES_MOVE_BEFORE_BOUND_BINDING = GeneratedBinding(
    'issues.move_before_bound', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('other_issue', '--before', 'path:before_id'),), (),
)

ISSUES_MOVE_TO_BOTTOM_BINDING = GeneratedBinding(
    'issues.move_to_bottom', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('literal.true', '--bottom', 'local_control:bottom'),), (),
)

ISSUES_MOVE_TO_BOTTOM_BOUND_BINDING = GeneratedBinding(
    'issues.move_to_bottom_bound', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('literal.true', '--bottom', 'local_control:bottom'),), (),
)

ISSUES_MOVE_TO_TOP_BINDING = GeneratedBinding(
    'issues.move_to_top', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('literal.true', '--top', 'local_control:top'),), (),
)

ISSUES_MOVE_TO_TOP_BOUND_BINDING = GeneratedBinding(
    'issues.move_to_top_bound', 'default', ('issue', 'reorder'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('literal.true', '--top', 'local_control:top'),), (),
)

ISSUE_PROPERTY_LIST_BINDING = GeneratedBinding(
    'issues.properties.list', 'default', ('issue', 'property', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUE_PROPERTY_SET_BINDING = GeneratedBinding(
    'issues.properties.set', 'default', ('issue', 'property', 'set'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('value', '--value', 'json_body:value'),), ('nonblank:issue_id', 'nonblank:name', 'nonblank:body'),
)

ISSUE_PROPERTY_UNSET_BINDING = GeneratedBinding(
    'issues.properties.unset', 'default', ('issue', 'property', 'unset'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('name', '--name', 'json_body:name'),), ('nonblank:issue_id', 'nonblank:name'),
)

ISSUE_PULL_REQUESTS_BINDING = GeneratedBinding(
    'issues.pull_requests', 'default', ('issue', 'pull-requests'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), ('nonblank:issue_id',),
)

ISSUES_REFRESH_BINDING = GeneratedBinding(
    'issues.refresh', 'default', (),
    (), (),
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
    (GeneratedMapping('task_run_id', 'pos:0', 'path:task_run_id'), GeneratedMapping('issue_id', '--issue', 'query:issue_id'), GeneratedMapping('since', '--since', 'query:since'),), ('nonblank:task_run_id', 'since_cursor_int32'),
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
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('status', 'pos:1', 'json_body:status'),), (),
)

ISSUES_SET_STATUS_BOUND_BINDING = GeneratedBinding(
    'issues.set_status_bound', 'default', (),
    (), (),
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

ISSUE_TIMELINE_BINDING = GeneratedBinding(
    'issues.timeline', 'default', ('issue', 'timeline'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('activity_only', '--activity-only', 'query:activity_only'), GeneratedMapping('actions', '--action', 'query:action'), GeneratedMapping('since', '--since', 'query:since'), GeneratedMapping('tail', '--tail', 'query:tail'),), (),
    minimum_cli_version='0.5.3',
)

ISSUES_UNASSIGN_BINDING = GeneratedBinding(
    'issues.unassign', 'default', ('issue', 'assign'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('literal.true', '--unassign', 'local_control:unassign'),), (),
)

ISSUES_UNASSIGN_BOUND_BINDING = GeneratedBinding(
    'issues.unassign_bound', 'default', (),
    (), (),
)

ISSUES_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'issues.update', 'default', ('issue', 'update'),
    (), (),
)

ISSUES_UPDATE_BOUND_BINDING = GeneratedBinding(
    'issues.update_bound', 'default', (),
    (), (),
)

ISSUES_USAGE_MANUAL_BINDING = GeneratedBinding(
    'issues.usage', 'default', ('issue', 'usage'),
    (), (),
)

ISSUE_WAKEUP_CREATE_BINDING = GeneratedBinding(
    'issues.wakeups.create', 'default', ('issue', 'wakeup', 'create'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('agent_id', '--agent-id', 'json_body:agent_id'), GeneratedMapping('instruction', '--instruction', 'json_body:instruction'), GeneratedMapping('kind', '--kind', 'json_body:kind'), GeneratedMapping('mode', '--mode', 'json_body:mode'), GeneratedMapping('event_types', '--event', 'json_body:event_types'), GeneratedMapping('filter_actor_type', '--filter-actor-type', 'json_body:filter_actor_type'), GeneratedMapping('filter_actor_id', '--filter-actor-id', 'json_body:filter_actor_id'), GeneratedMapping('filter_agent_id', '--filter-agent-id', 'json_body:filter_agent_id'), GeneratedMapping('filter_task_id', '--task-id', 'json_body:filter_task_id'), GeneratedMapping('parent_comment_id', '--parent', 'json_body:parent_comment_id'), GeneratedMapping('after_seconds', '--after', 'json_body:after_seconds'), GeneratedMapping('at', '--at', 'json_body:at'), GeneratedMapping('interval_seconds', '--every', 'json_body:interval_seconds'), GeneratedMapping('cron_expression', '--cron', 'json_body:cron_expression'), GeneratedMapping('timezone', '--timezone', 'json_body:timezone'),), (),
    minimum_cli_version='0.5.3',
)

ISSUE_WAKEUP_DISABLE_BINDING = GeneratedBinding(
    'issues.wakeups.disable', 'default', ('issue', 'wakeup', 'disable'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('wakeup_id', 'pos:1', 'path:wakeup_id'),), (),
    minimum_cli_version='0.5.3',
)

ISSUE_WAKEUP_EVENTS_BINDING = GeneratedBinding(
    'issues.wakeups.events', 'default', ('issue', 'wakeup', 'events'),
    (), (),
    minimum_cli_version='0.5.3',
)

ISSUE_WAKEUP_GET_BINDING = GeneratedBinding(
    'issues.wakeups.get', 'default', ('issue', 'wakeup', 'get'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('wakeup_id', 'pos:1', 'path:wakeup_id'),), (),
    minimum_cli_version='0.5.3',
)

ISSUE_WAKEUP_LIST_BINDING = GeneratedBinding(
    'issues.wakeups.list', 'default', ('issue', 'wakeup', 'list'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'),), (),
    minimum_cli_version='0.5.3',
)

ISSUE_WAKEUP_UPDATE_BINDING = GeneratedBinding(
    'issues.wakeups.update', 'default', ('issue', 'wakeup', 'update'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('agent_id', '--agent-id', 'json_body:agent_id'), GeneratedMapping('instruction', '--instruction', 'json_body:instruction'), GeneratedMapping('kind', '--kind', 'json_body:kind'), GeneratedMapping('mode', '--mode', 'json_body:mode'), GeneratedMapping('event_types', '--event', 'json_body:event_types'), GeneratedMapping('filter_actor_type', '--filter-actor-type', 'json_body:filter_actor_type'), GeneratedMapping('filter_actor_id', '--filter-actor-id', 'json_body:filter_actor_id'), GeneratedMapping('filter_agent_id', '--filter-agent-id', 'json_body:filter_agent_id'), GeneratedMapping('filter_task_id', '--task-id', 'json_body:filter_task_id'), GeneratedMapping('parent_comment_id', '--parent', 'json_body:parent_comment_id'), GeneratedMapping('after_seconds', '--after', 'json_body:after_seconds'), GeneratedMapping('at', '--at', 'json_body:at'), GeneratedMapping('interval_seconds', '--every', 'json_body:interval_seconds'), GeneratedMapping('cron_expression', '--cron', 'json_body:cron_expression'), GeneratedMapping('timezone', '--timezone', 'json_body:timezone'), GeneratedMapping('wakeup_id', 'pos:1', 'path:wakeup_id'),), (),
    minimum_cli_version='0.5.3',
)

LABELS_CREATE_MANUAL_BINDING = GeneratedBinding(
    'labels.create', 'default', ('label', 'create'),
    (), (),
    minimum_cli_version='0.5.0',
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
    minimum_cli_version='0.5.0',
)

LABELS_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'labels.update', 'default', ('label', 'update'),
    (), (),
    minimum_cli_version='0.5.0',
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
    (GeneratedMapping('name', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('description_file', '--description-file', 'local_control:description'),), ('nonblank:name',),
)

PROJECTS_DELETE_MANUAL_BINDING = GeneratedBinding(
    'projects.delete', 'default', ('project', 'delete'),
    (), (),
)

PROJECT_GET_BINDING = GeneratedBinding(
    'projects.get', 'default', ('project', 'get'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'),), ('nonblank:project_id',),
)

PROJECT_ISSUE_CREATE_BINDING = GeneratedBinding(
    'projects.issues.create', 'default', ('issue', 'create'),
    (GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'local_control:description'), GeneratedMapping('description_file', '--description-file', 'local_control:description'), GeneratedMapping('description_input', 'description-selector', 'local_control:description'), GeneratedMapping('priority', '--priority', 'json_body:priority'), GeneratedMapping('assignee_id', '--assignee-id', 'json_body:assignee_id'), GeneratedMapping('parent_id', '--parent', 'json_body:parent_issue_id'), GeneratedMapping('label_ids', 'repeat:issue label add', 'json_body:label_id'),), (),
)

PROJECT_LIST_BINDING = GeneratedBinding(
    'projects.list', 'default', ('project', 'list'),
    (), (),
)

PROJECTS_REFRESH_BINDING = GeneratedBinding(
    'projects.refresh', 'default', (),
    (), (),
)

PROJECT_RESOURCE_ADD_BINDING = GeneratedBinding(
    'projects.resources.add_local_directory', 'default', ('project', 'resource', 'add'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('local_path', '--local-path', 'local_control:absolute_path'), GeneratedMapping('daemon_id', '--daemon-id', 'json_body:daemon_id'), GeneratedMapping('label', '--ref-label', 'json_body:label'), GeneratedMapping('literal.local_directory', '--type', 'json_body:type'),), ('nonblank:project_id', 'nonblank:local_path', 'nonblank:daemon_id', 'blank_label_omitted'),
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
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('resource_id', 'pos:1', 'path:resource_id'), GeneratedMapping('local_path', '--local-path', 'local_control:absolute_path'),), ('nonblank:project_id', 'nonblank:resource_id', 'nonblank:local_path', 'preserve_daemon_and_label'),
)

PROJECT_STATUS_BINDING = GeneratedBinding(
    'projects.set_status', 'default', ('project', 'status'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('status', 'pos:1', 'json_body:status'),), ('strict:ProjectStatus',),
)

PROJECT_UPDATE_BINDING = GeneratedBinding(
    'projects.update', 'default', ('project', 'update'),
    (GeneratedMapping('project_id', 'pos:0', 'path:project_id'), GeneratedMapping('name', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'),), ('at_least_one:name_description', 'description_none_rejected', 'unset_omits', 'empty_emits'),
)

PROJECTS_UPDATE_BOUND_BINDING = GeneratedBinding(
    'projects.update_bound', 'default', (),
    (), (),
)

PROPERTY_ARCHIVE_BINDING = GeneratedBinding(
    'properties.archive', 'default', ('property', 'archive'),
    (GeneratedMapping('property_ref', 'pos:0', 'path:property_ref'),), ('nonblank:name',),
)

PROPERTY_CREATE_BINDING = GeneratedBinding(
    'properties.create', 'default', ('property', 'create'),
    (GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('property_type', '--type', 'json_body:property_type'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('icon', '--icon', 'json_body:icon'), GeneratedMapping('options_values', 'repeat:--option', 'json_body:options'),), ('nonblank:name', 'nonblank:name'),
)

PROPERTY_GET_BINDING = GeneratedBinding(
    'properties.get', 'default', ('property', 'get'),
    (GeneratedMapping('property_ref', 'pos:0', 'path:property_ref'),), ('nonblank:name',),
)

PROPERTY_LIST_BINDING = GeneratedBinding(
    'properties.list', 'default', ('property', 'list'),
    (GeneratedMapping('include_archived', '--include-archived', 'query:include_archived'),), (),
)

PROPERTY_UNARCHIVE_BINDING = GeneratedBinding(
    'properties.unarchive', 'default', ('property', 'unarchive'),
    (GeneratedMapping('property_ref', 'pos:0', 'path:property_ref'),), ('nonblank:name',),
)

PROPERTY_UPDATE_BINDING = GeneratedBinding(
    'properties.update', 'default', ('property', 'update'),
    (GeneratedMapping('property_ref', 'pos:0', 'path:property_ref'), GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('icon', '--icon', 'json_body:icon'), GeneratedMapping('options_values', 'repeat:--option', 'json_body:options'),), ('nonblank:name',),
)

REPOSITORIES_ADD_BINDING = GeneratedBinding(
    'repositories.add', 'default', ('repo', 'add'),
    (GeneratedMapping('urls', 'repeat:pos:0', 'json_body:repos'), GeneratedMapping('description', '--description', 'json_body:description'),), (),
)

REPOSITORY_CHECKOUT_BINDING = GeneratedBinding(
    'repositories.checkout', 'default', ('repo', 'checkout'),
    (GeneratedMapping('url', 'pos:0', 'path:url'), GeneratedMapping('ref', '--ref', 'query:ref'), GeneratedMapping('fresh', '--fresh', 'local_control:fresh'),), (),
    minimum_cli_version='0.5.3',
)

REPOSITORIES_LIST_BINDING = GeneratedBinding(
    'repositories.list', 'default', ('repo', 'list'),
    (), (),
)

REPOSITORIES_REMOVE_BINDING = GeneratedBinding(
    'repositories.remove', 'default', ('repo', 'remove'),
    (GeneratedMapping('urls', 'repeat:pos:0', 'json_body:repos'),), (),
)

RUNTIME_PROFILE_CREATE_BINDING = GeneratedBinding(
    'runtime_profiles.create', 'default', ('runtime', 'profile', 'create'),
    (GeneratedMapping('runtime_type', '--runtime-type', 'json_body:runtime_type'), GeneratedMapping('protocol_family', '--protocol-family', 'json_body:protocol_family'), GeneratedMapping('command_name', '--command-name', 'json_body:command_name'), GeneratedMapping('display_name', '--display-name', 'json_body:display_name'), GeneratedMapping('description', '--description', 'json_body:description'),), (),
    minimum_cli_version='0.5.3',
)

RUNTIME_PROFILE_DELETE_BINDING = GeneratedBinding(
    'runtime_profiles.delete', 'default', ('runtime', 'profile', 'delete'),
    (GeneratedMapping('profile_id', 'pos:0', 'path:profile_id'),), (),
    minimum_cli_version='0.5.3',
)

RUNTIME_PROFILE_LIST_BINDING = GeneratedBinding(
    'runtime_profiles.list', 'default', ('runtime', 'profile', 'list'),
    (), (),
    minimum_cli_version='0.5.3',
)

RUNTIME_PROFILE_SET_PATH_BINDING = GeneratedBinding(
    'runtime_profiles.set_path', 'default', ('runtime', 'profile', 'set-path'),
    (GeneratedMapping('profile_id', 'pos:0', 'path:profile_id'), GeneratedMapping('path', '--path', 'local_control:absolute_path'),), (),
    minimum_cli_version='0.5.3',
)

RUNTIME_PROFILE_UNSET_PATH_BINDING = GeneratedBinding(
    'runtime_profiles.unset_path', 'default', ('runtime', 'profile', 'unset-path'),
    (GeneratedMapping('profile_id', 'pos:0', 'path:profile_id'),), (),
    minimum_cli_version='0.5.3',
)

RUNTIME_PROFILE_UPDATE_BINDING = GeneratedBinding(
    'runtime_profiles.update', 'default', ('runtime', 'profile', 'update'),
    (GeneratedMapping('profile_id', 'pos:0', 'path:profile_id'), GeneratedMapping('display_name', '--display-name', 'json_body:display_name'), GeneratedMapping('command_name', '--command-name', 'json_body:command_name'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('enabled', '--enabled', 'json_body:enabled'),), (),
    minimum_cli_version='0.5.3',
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
    (GeneratedMapping('runtime_id', 'pos:0', 'path:runtime_id'), GeneratedMapping('target_version', '--target-version', 'json_body:target_version'), GeneratedMapping('wait', '--wait', 'local_control:wait'),), ('nonblank:runtime',),
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

SKILL_LABELS_ADD_BINDING = GeneratedBinding(
    'skills.labels.add', 'default', ('skill', 'label', 'add'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'), GeneratedMapping('label_id', 'pos:1', 'path:label_id'),), ('nonblank:skill_id', 'nonblank:label_id'),
    minimum_cli_version='0.5.0',
)

SKILL_LABELS_LIST_BINDING = GeneratedBinding(
    'skills.labels.list', 'default', ('skill', 'label', 'list'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'),), ('nonblank:skill_id',),
    minimum_cli_version='0.5.0',
)

SKILL_LABELS_REMOVE_BINDING = GeneratedBinding(
    'skills.labels.remove', 'default', ('skill', 'label', 'remove'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'), GeneratedMapping('label_id', 'pos:1', 'path:label_id'),), ('nonblank:skill_id', 'nonblank:label_id'),
    minimum_cli_version='0.5.0',
)

SKILL_LIST_BINDING = GeneratedBinding(
    'skills.list', 'default', ('skill', 'list'),
    (), (),
    minimum_cli_version='0.5.0',
)

SKILL_REFRESH_BINDING = GeneratedBinding(
    'skills.refresh', 'default', ('skill', 'refresh'),
    (GeneratedMapping('skill_id', 'pos:0', 'path:skill_id'),), ('nonblank:skill_id',),
)

SKILL_SEARCH_BINDING = GeneratedBinding(
    'skills.search', 'default', ('skill', 'search'),
    (GeneratedMapping('query', 'pos:0', 'path:query'),), ('nonblank:query',),
)

SKILLS_UPDATE_MANUAL_BINDING = GeneratedBinding(
    'skills.update', 'default', ('skill', 'update'),
    (), (),
)

SQUADS_ACTIVITY_BINDING = GeneratedBinding(
    'squads.activity', 'default', ('squad', 'activity'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('outcome', 'pos:1', 'path:outcome'), GeneratedMapping('reason', '--reason', 'json_body:reason'),), (),
    minimum_cli_version='0.5.3',
)

SQUADS_CREATE_BINDING = GeneratedBinding(
    'squads.create', 'default', ('squad', 'create'),
    (GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('leader', '--leader', 'json_body:leader'), GeneratedMapping('description', '--description', 'json_body:description'),), (),
    minimum_cli_version='0.5.3',
)

SQUADS_DELETE_BINDING = GeneratedBinding(
    'squads.delete', 'default', ('squad', 'delete'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'),), (),
    minimum_cli_version='0.5.3',
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

SQUADS_MEMBERS_SET_ROLE_BINDING = GeneratedBinding(
    'squads.members.set_role', 'default', ('squad', 'member', 'set-role'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'), GeneratedMapping('member_id', '--member-id', 'json_body:member_id'), GeneratedMapping('member_type', '--member-type', 'json_body:member_type'), GeneratedMapping('role', '--role', 'json_body:role'),), (),
    minimum_cli_version='0.5.3',
)

SQUADS_UPDATE_BINDING = GeneratedBinding(
    'squads.update', 'default', ('squad', 'update'),
    (GeneratedMapping('squad_id', 'pos:0', 'path:squad_id'), GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('instructions', '--instructions', 'json_body:instructions'), GeneratedMapping('leader', '--leader', 'json_body:leader'), GeneratedMapping('avatar_url', '--avatar-url', 'json_body:avatar_url'),), (),
    minimum_cli_version='0.5.3',
)

USER_PROFILE_GET_BINDING = GeneratedBinding(
    'users.profile_get', 'default', ('user', 'profile', 'get'),
    (), (),
)

USER_PROFILE_UPDATE_BINDING = GeneratedBinding(
    'users.profile_update', 'default', ('user', 'profile', 'update'),
    (GeneratedMapping('description', '--description', 'json_body:profile_description'),), (),
)

WORKSPACES_CREATE_BINDING = GeneratedBinding(
    'workspaces.create', 'default', ('workspace', 'create'),
    (GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('slug', '--slug', 'json_body:slug'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('context', '--context', 'json_body:context'), GeneratedMapping('issue_prefix', '--issue-prefix', 'json_body:issue_prefix'),), (),
    minimum_cli_version='0.5.3',
)

WORKSPACE_GET_BINDING = GeneratedBinding(
    'workspaces.get', 'default', ('workspace', 'get'),
    (GeneratedMapping('workspace_id', 'pos:0', 'path:workspace_id'),), ('nonblank:workspace_id',),
)

WORKSPACE_LIST_BINDING = GeneratedBinding(
    'workspaces.list', 'default', ('workspace', 'list'),
    (), (),
)

WORKSPACE_MCP_ADD_BINDING = GeneratedBinding(
    'workspaces.mcp.add', 'default', ('workspace', 'mcp', 'add'),
    (GeneratedMapping('server_name', 'pos:0', 'path:server_name'), GeneratedMapping('server_config_file', '--server-config-file', 'json_body:server_config'), GeneratedMapping('server_config_stdin', '--server-config-stdin', 'json_body:server_config'), GeneratedMapping('server_config', '--server-config', 'json_body:server_config'),), ('nonblank:name',),
)

WORKSPACE_MCP_LIST_BINDING = GeneratedBinding(
    'workspaces.mcp.list', 'default', ('workspace', 'mcp', 'list'),
    (), (),
)

WORKSPACE_MCP_REMOVE_BINDING = GeneratedBinding(
    'workspaces.mcp.remove', 'default', ('workspace', 'mcp', 'remove'),
    (GeneratedMapping('server_id', 'pos:0', 'path:server_id'),), ('nonblank:server_id',),
)

WORKSPACE_MCP_UPDATE_BINDING = GeneratedBinding(
    'workspaces.mcp.update', 'default', ('workspace', 'mcp', 'update'),
    (GeneratedMapping('server_id', 'pos:0', 'path:server_id'), GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('server_config_file', '--server-config-file', 'json_body:server_config'), GeneratedMapping('server_config_stdin', '--server-config-stdin', 'json_body:server_config'), GeneratedMapping('server_config', '--server-config', 'json_body:server_config'),), ('nonblank:server_id',),
)

WORKSPACES_MEMBERS_INVITE_BINDING = GeneratedBinding(
    'workspaces.members.invite', 'default', ('workspace', 'member', 'invite'),
    (GeneratedMapping('email', 'pos:0', 'path:email'), GeneratedMapping('workspace_id', 'pos:1', 'path:workspace_id'), GeneratedMapping('role', '--role', 'json_body:role'),), (),
    minimum_cli_version='0.5.3',
)

WORKSPACE_MEMBERS_LIST_BINDING = GeneratedBinding(
    'workspaces.members.list', 'default', ('workspace', 'member', 'list'),
    (GeneratedMapping('workspace_id', 'pos:0', 'path:workspace_id'),), ('nonblank:workspace_id',),
)

WORKSPACES_SWITCH_MANUAL_BINDING = GeneratedBinding(
    'workspaces.switch', 'default', ('workspace', 'switch'),
    (), (),
)

WORKSPACES_UPDATE_BINDING = GeneratedBinding(
    'workspaces.update', 'default', ('workspace', 'update'),
    (GeneratedMapping('workspace_id', 'pos:0', 'path:workspace_id'), GeneratedMapping('name', '--name', 'json_body:name'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('context', '--context', 'json_body:context'), GeneratedMapping('issue_prefix', '--issue-prefix', 'json_body:issue_prefix'),), (),
    minimum_cli_version='0.5.3',
)

OPERATION_BINDINGS: tuple[GeneratedBinding, ...] = (
    AGENTS_ARCHIVE_MANUAL_BINDING,
    AGENT_AVATAR_BINDING,
    AGENT_COPY_BINDING,
    AGENTS_CREATE_MANUAL_BINDING,
    AGENTS_ENV_GET_BINDING,
    AGENTS_ENV_SET_BINDING,
    AGENT_GET_BINDING,
    AGENT_LIST_BINDING,
    AGENT_MCP_ADD_BINDING,
    AGENT_MCP_ADD_BOUND_BINDING,
    AGENT_MCP_DISABLE_BINDING,
    AGENT_MCP_DISABLE_BOUND_BINDING,
    AGENT_MCP_ENABLE_BINDING,
    AGENT_MCP_ENABLE_BOUND_BINDING,
    AGENT_MCP_LIST_BINDING,
    AGENT_MCP_REMOVE_BINDING,
    AGENT_MCP_REMOVE_BOUND_BINDING,
    AGENTS_RESTORE_MANUAL_BINDING,
    AGENTS_SKILLS_ADD_BINDING,
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
    AUTOPILOTS_TRIGGER_LIST_BINDING,
    AUTOPILOT_TRIGGER_ROTATE_URL_BINDING,
    AUTOPILOT_TRIGGER_UPDATE_BINDING,
    AUTOPILOT_UPDATE_BINDING,
    CHAT_HISTORY_BINDING,
    CHAT_THREAD_BINDING,
    CLI_COMMAND_BINDING,
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
    ISSUES_ASSIGN_BOUND_BINDING,
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
    COMMENT_UPDATE_BINDING,
    ISSUE_CREATE_BINDING,
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
    ISSUES_MOVE_AFTER_BINDING,
    ISSUES_MOVE_AFTER_BOUND_BINDING,
    ISSUES_MOVE_BEFORE_BINDING,
    ISSUES_MOVE_BEFORE_BOUND_BINDING,
    ISSUES_MOVE_TO_BOTTOM_BINDING,
    ISSUES_MOVE_TO_BOTTOM_BOUND_BINDING,
    ISSUES_MOVE_TO_TOP_BINDING,
    ISSUES_MOVE_TO_TOP_BOUND_BINDING,
    ISSUE_PROPERTY_LIST_BINDING,
    ISSUE_PROPERTY_SET_BINDING,
    ISSUE_PROPERTY_UNSET_BINDING,
    ISSUE_PULL_REQUESTS_BINDING,
    ISSUES_REFRESH_BINDING,
    ISSUES_REORDER_MANUAL_BINDING,
    ISSUE_RERUN_BINDING,
    ISSUE_RUN_MESSAGES_BINDING,
    ISSUE_RUNS_BINDING,
    ISSUE_SEARCH_BINDING,
    ISSUE_STATUS_BINDING,
    ISSUES_SET_STATUS_BOUND_BINDING,
    ISSUE_SUBSCRIBERS_ADD_BINDING,
    ISSUE_SUBSCRIBERS_LIST_BINDING,
    ISSUE_SUBSCRIBERS_REMOVE_BINDING,
    ISSUE_TIMELINE_BINDING,
    ISSUES_UNASSIGN_BINDING,
    ISSUES_UNASSIGN_BOUND_BINDING,
    ISSUES_UPDATE_MANUAL_BINDING,
    ISSUES_UPDATE_BOUND_BINDING,
    ISSUES_USAGE_MANUAL_BINDING,
    ISSUE_WAKEUP_CREATE_BINDING,
    ISSUE_WAKEUP_DISABLE_BINDING,
    ISSUE_WAKEUP_EVENTS_BINDING,
    ISSUE_WAKEUP_GET_BINDING,
    ISSUE_WAKEUP_LIST_BINDING,
    ISSUE_WAKEUP_UPDATE_BINDING,
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
    PROJECT_ISSUE_CREATE_BINDING,
    PROJECT_LIST_BINDING,
    PROJECTS_REFRESH_BINDING,
    PROJECT_RESOURCE_ADD_BINDING,
    PROJECT_RESOURCE_LIST_BINDING,
    PROJECT_RESOURCE_REMOVE_BINDING,
    PROJECT_RESOURCE_UPDATE_BINDING,
    PROJECT_STATUS_BINDING,
    PROJECT_UPDATE_BINDING,
    PROJECTS_UPDATE_BOUND_BINDING,
    PROPERTY_ARCHIVE_BINDING,
    PROPERTY_CREATE_BINDING,
    PROPERTY_GET_BINDING,
    PROPERTY_LIST_BINDING,
    PROPERTY_UNARCHIVE_BINDING,
    PROPERTY_UPDATE_BINDING,
    REPOSITORIES_ADD_BINDING,
    REPOSITORY_CHECKOUT_BINDING,
    REPOSITORIES_LIST_BINDING,
    REPOSITORIES_REMOVE_BINDING,
    RUNTIME_PROFILE_CREATE_BINDING,
    RUNTIME_PROFILE_DELETE_BINDING,
    RUNTIME_PROFILE_LIST_BINDING,
    RUNTIME_PROFILE_SET_PATH_BINDING,
    RUNTIME_PROFILE_UNSET_PATH_BINDING,
    RUNTIME_PROFILE_UPDATE_BINDING,
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
    SKILL_LABELS_ADD_BINDING,
    SKILL_LABELS_LIST_BINDING,
    SKILL_LABELS_REMOVE_BINDING,
    SKILL_LIST_BINDING,
    SKILL_REFRESH_BINDING,
    SKILL_SEARCH_BINDING,
    SKILLS_UPDATE_MANUAL_BINDING,
    SQUADS_ACTIVITY_BINDING,
    SQUADS_CREATE_BINDING,
    SQUADS_DELETE_BINDING,
    SQUAD_GET_BINDING,
    SQUAD_LIST_BINDING,
    SQUAD_MEMBERS_ADD_BINDING,
    SQUAD_MEMBERS_LIST_BINDING,
    SQUAD_MEMBERS_REMOVE_BINDING,
    SQUADS_MEMBERS_SET_ROLE_BINDING,
    SQUADS_UPDATE_BINDING,
    USER_PROFILE_GET_BINDING,
    USER_PROFILE_UPDATE_BINDING,
    WORKSPACES_CREATE_BINDING,
    WORKSPACE_GET_BINDING,
    WORKSPACE_LIST_BINDING,
    WORKSPACE_MCP_ADD_BINDING,
    WORKSPACE_MCP_LIST_BINDING,
    WORKSPACE_MCP_REMOVE_BINDING,
    WORKSPACE_MCP_UPDATE_BINDING,
    WORKSPACES_MEMBERS_INVITE_BINDING,
    WORKSPACE_MEMBERS_LIST_BINDING,
    WORKSPACES_SWITCH_MANUAL_BINDING,
    WORKSPACES_UPDATE_BINDING,
)

PUBLIC_INVENTORY: tuple[GeneratedInventoryItem, ...] = (
    GeneratedInventoryItem(
        'command:multica.agent.archive', 'command', 'multica agent archive',
        'transport', None, 'cli:multica agent archive',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.avatar', 'command', 'multica agent avatar',
        'transport', None, 'cli:multica agent avatar',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.copy', 'command', 'multica agent copy',
        'transport', None, 'cli:multica agent copy',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.create', 'command', 'multica agent create',
        'transport', None, 'cli:multica agent create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.env.get', 'command', 'multica agent env get',
        'typed', 'multica_py.resources.agents.AgentResource.env_get', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.env.set', 'command', 'multica agent env set',
        'typed', 'multica_py.resources.agents.AgentResource.env_set', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.get', 'command', 'multica agent get',
        'transport', None, 'cli:multica agent get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.list', 'command', 'multica agent list',
        'transport', None, 'cli:multica agent list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.mcp.add', 'command', 'multica agent mcp add',
        'transport', None, 'cli:multica agent mcp add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.mcp.disable', 'command', 'multica agent mcp disable',
        'transport', None, 'cli:multica agent mcp disable',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.mcp.enable', 'command', 'multica agent mcp enable',
        'transport', None, 'cli:multica agent mcp enable',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.mcp.list', 'command', 'multica agent mcp list',
        'transport', None, 'cli:multica agent mcp list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.mcp.remove', 'command', 'multica agent mcp remove',
        'transport', None, 'cli:multica agent mcp remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.restore', 'command', 'multica agent restore',
        'transport', None, 'cli:multica agent restore',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.skills.add', 'command', 'multica agent skills add',
        'typed', 'multica_py.resources.agents.AgentResource.skills_add', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.skills.list', 'command', 'multica agent skills list',
        'transport', None, 'cli:multica agent skills list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.skills.set', 'command', 'multica agent skills set',
        'transport', None, 'cli:multica agent skills set',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.tasks', 'command', 'multica agent tasks',
        'transport', None, 'cli:multica agent tasks',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.agent.update', 'command', 'multica agent update',
        'transport', None, 'cli:multica agent update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.attachment.download', 'command', 'multica attachment download',
        'transport', None, 'cli:multica attachment download',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.attachment.upload', 'command', 'multica attachment upload',
        'transport', None, 'cli:multica attachment upload',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.auth.logout', 'command', 'multica auth logout',
        'transport', None, 'cli:multica auth logout',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.auth.status', 'command', 'multica auth status',
        'transport', None, 'cli:multica auth status',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.create', 'command', 'multica autopilot create',
        'transport', None, 'cli:multica autopilot create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.delete', 'command', 'multica autopilot delete',
        'transport', None, 'cli:multica autopilot delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.get', 'command', 'multica autopilot get',
        'transport', None, 'cli:multica autopilot get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.list', 'command', 'multica autopilot list',
        'transport', None, 'cli:multica autopilot list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.runs', 'command', 'multica autopilot runs',
        'transport', None, 'cli:multica autopilot runs',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.trigger', 'command', 'multica autopilot trigger',
        'transport', None, 'cli:multica autopilot trigger',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.trigger-add', 'command', 'multica autopilot trigger-add',
        'transport', None, 'cli:multica autopilot trigger-add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.trigger-delete', 'command', 'multica autopilot trigger-delete',
        'transport', None, 'cli:multica autopilot trigger-delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.trigger-list', 'command', 'multica autopilot trigger-list',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.trigger_list', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.trigger-rotate-url', 'command', 'multica autopilot trigger-rotate-url',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.trigger_rotate_url', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.trigger-update', 'command', 'multica autopilot trigger-update',
        'transport', None, 'cli:multica autopilot trigger-update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.autopilot.update', 'command', 'multica autopilot update',
        'transport', None, 'cli:multica autopilot update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.chat.history', 'command', 'multica chat history',
        'typed', 'multica_py.resources.chats.ChatResource.history', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.chat.thread', 'command', 'multica chat thread',
        'typed', 'multica_py.resources.chats.ChatResource.thread', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.config.set', 'command', 'multica config set',
        'transport', None, 'cli:multica config set',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.config.show', 'command', 'multica config show',
        'transport', None, 'cli:multica config show',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.disk-usage', 'command', 'multica daemon disk-usage',
        'transport', None, 'cli:multica daemon disk-usage',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.logs', 'command', 'multica daemon logs',
        'transport', None, 'cli:multica daemon logs',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.probe-runtimes', 'command', 'multica daemon probe-runtimes',
        'outside-public-scope', None, None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.restart', 'command', 'multica daemon restart',
        'transport', None, 'cli:multica daemon restart',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.start', 'command', 'multica daemon start',
        'transport', None, 'cli:multica daemon start',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.status', 'command', 'multica daemon status',
        'transport', None, 'cli:multica daemon status',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.daemon.stop', 'command', 'multica daemon stop',
        'transport', None, 'cli:multica daemon stop',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.assign', 'command', 'multica issue assign',
        'transport', None, 'cli:multica issue assign',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.cancel-task', 'command', 'multica issue cancel-task',
        'transport', None, 'cli:multica issue cancel-task',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.children', 'command', 'multica issue children',
        'transport', None, 'cli:multica issue children',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.comment.add', 'command', 'multica issue comment add',
        'transport', None, 'cli:multica issue comment add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.comment.delete', 'command', 'multica issue comment delete',
        'transport', None, 'cli:multica issue comment delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.comment.list', 'command', 'multica issue comment list',
        'transport', None, 'cli:multica issue comment list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.comment.resolve', 'command', 'multica issue comment resolve',
        'transport', None, 'cli:multica issue comment resolve',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.comment.unresolve', 'command', 'multica issue comment unresolve',
        'transport', None, 'cli:multica issue comment unresolve',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.comment.update', 'command', 'multica issue comment update',
        'transport', None, 'cli:multica issue comment update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.create', 'command', 'multica issue create',
        'transport', None, 'cli:multica issue create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.get', 'command', 'multica issue get',
        'transport', None, 'cli:multica issue get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.label.add', 'command', 'multica issue label add',
        'transport', None, 'cli:multica issue label add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.label.list', 'command', 'multica issue label list',
        'transport', None, 'cli:multica issue label list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.label.remove', 'command', 'multica issue label remove',
        'transport', None, 'cli:multica issue label remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.list', 'command', 'multica issue list',
        'transport', None, 'cli:multica issue list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.metadata.delete', 'command', 'multica issue metadata delete',
        'transport', None, 'cli:multica issue metadata delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.metadata.get', 'command', 'multica issue metadata get',
        'transport', None, 'cli:multica issue metadata get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.metadata.list', 'command', 'multica issue metadata list',
        'transport', None, 'cli:multica issue metadata list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.metadata.set', 'command', 'multica issue metadata set',
        'transport', None, 'cli:multica issue metadata set',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.property.list', 'command', 'multica issue property list',
        'transport', None, 'cli:multica issue property list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.property.set', 'command', 'multica issue property set',
        'transport', None, 'cli:multica issue property set',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.property.unset', 'command', 'multica issue property unset',
        'transport', None, 'cli:multica issue property unset',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.pull-requests', 'command', 'multica issue pull-requests',
        'transport', None, 'cli:multica issue pull-requests',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.reorder', 'command', 'multica issue reorder',
        'transport', None, 'cli:multica issue reorder',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.rerun', 'command', 'multica issue rerun',
        'transport', None, 'cli:multica issue rerun',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.run-messages', 'command', 'multica issue run-messages',
        'transport', None, 'cli:multica issue run-messages',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.runs', 'command', 'multica issue runs',
        'transport', None, 'cli:multica issue runs',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.search', 'command', 'multica issue search',
        'transport', None, 'cli:multica issue search',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.status', 'command', 'multica issue status',
        'transport', None, 'cli:multica issue status',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.subscriber.add', 'command', 'multica issue subscriber add',
        'transport', None, 'cli:multica issue subscriber add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.subscriber.list', 'command', 'multica issue subscriber list',
        'transport', None, 'cli:multica issue subscriber list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.subscriber.remove', 'command', 'multica issue subscriber remove',
        'transport', None, 'cli:multica issue subscriber remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.timeline', 'command', 'multica issue timeline',
        'typed', 'multica_py.resources.issues.IssueResource.timeline', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.update', 'command', 'multica issue update',
        'transport', None, 'cli:multica issue update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.usage', 'command', 'multica issue usage',
        'transport', None, 'cli:multica issue usage',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.wakeup.create', 'command', 'multica issue wakeup create',
        'typed', 'multica_py.resources.issue_wakeups.IssueWakeupResource.create', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.wakeup.disable', 'command', 'multica issue wakeup disable',
        'typed', 'multica_py.resources.issue_wakeups.IssueWakeupResource.disable', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.wakeup.events', 'command', 'multica issue wakeup events',
        'typed', 'multica_py.resources.issue_wakeups.IssueWakeupResource.events', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.wakeup.get', 'command', 'multica issue wakeup get',
        'typed', 'multica_py.resources.issue_wakeups.IssueWakeupResource.get', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.wakeup.list', 'command', 'multica issue wakeup list',
        'typed', 'multica_py.resources.issue_wakeups.IssueWakeupResource.list', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.issue.wakeup.update', 'command', 'multica issue wakeup update',
        'typed', 'multica_py.resources.issue_wakeups.IssueWakeupResource.update', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.label.create', 'command', 'multica label create',
        'transport', None, 'cli:multica label create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.label.delete', 'command', 'multica label delete',
        'transport', None, 'cli:multica label delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.label.get', 'command', 'multica label get',
        'transport', None, 'cli:multica label get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.label.list', 'command', 'multica label list',
        'transport', None, 'cli:multica label list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.label.update', 'command', 'multica label update',
        'transport', None, 'cli:multica label update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.login', 'command', 'multica login',
        'transport', None, 'cli:multica login',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.create', 'command', 'multica project create',
        'transport', None, 'cli:multica project create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.delete', 'command', 'multica project delete',
        'transport', None, 'cli:multica project delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.get', 'command', 'multica project get',
        'transport', None, 'cli:multica project get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.list', 'command', 'multica project list',
        'transport', None, 'cli:multica project list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.resource.add', 'command', 'multica project resource add',
        'transport', None, 'cli:multica project resource add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.resource.list', 'command', 'multica project resource list',
        'transport', None, 'cli:multica project resource list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.resource.remove', 'command', 'multica project resource remove',
        'transport', None, 'cli:multica project resource remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.resource.update', 'command', 'multica project resource update',
        'transport', None, 'cli:multica project resource update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.status', 'command', 'multica project status',
        'transport', None, 'cli:multica project status',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.project.update', 'command', 'multica project update',
        'transport', None, 'cli:multica project update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.property.archive', 'command', 'multica property archive',
        'transport', None, 'cli:multica property archive',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.property.create', 'command', 'multica property create',
        'transport', None, 'cli:multica property create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.property.get', 'command', 'multica property get',
        'transport', None, 'cli:multica property get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.property.list', 'command', 'multica property list',
        'transport', None, 'cli:multica property list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.property.unarchive', 'command', 'multica property unarchive',
        'transport', None, 'cli:multica property unarchive',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.property.update', 'command', 'multica property update',
        'transport', None, 'cli:multica property update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.repo.add', 'command', 'multica repo add',
        'transport', None, 'cli:multica repo add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.repo.checkout', 'command', 'multica repo checkout',
        'typed', 'multica_py.resources.repositories.RepositoryResource.checkout', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.repo.list', 'command', 'multica repo list',
        'transport', None, 'cli:multica repo list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.repo.remove', 'command', 'multica repo remove',
        'transport', None, 'cli:multica repo remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.activity', 'command', 'multica runtime activity',
        'transport', None, 'cli:multica runtime activity',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.delete', 'command', 'multica runtime delete',
        'transport', None, 'cli:multica runtime delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.list', 'command', 'multica runtime list',
        'transport', None, 'cli:multica runtime list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.profile.create', 'command', 'multica runtime profile create',
        'typed', 'multica_py.resources.runtime_profiles.RuntimeProfileResource.create', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.profile.delete', 'command', 'multica runtime profile delete',
        'typed', 'multica_py.resources.runtime_profiles.RuntimeProfileResource.delete', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.profile.list', 'command', 'multica runtime profile list',
        'typed', 'multica_py.resources.runtime_profiles.RuntimeProfileResource.list', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.profile.set-path', 'command', 'multica runtime profile set-path',
        'typed', 'multica_py.resources.runtime_profiles.RuntimeProfileResource.set_path', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.profile.unset-path', 'command', 'multica runtime profile unset-path',
        'typed', 'multica_py.resources.runtime_profiles.RuntimeProfileResource.unset_path', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.profile.update', 'command', 'multica runtime profile update',
        'typed', 'multica_py.resources.runtime_profiles.RuntimeProfileResource.update', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.rename', 'command', 'multica runtime rename',
        'transport', None, 'cli:multica runtime rename',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.update', 'command', 'multica runtime update',
        'transport', None, 'cli:multica runtime update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.runtime.usage', 'command', 'multica runtime usage',
        'transport', None, 'cli:multica runtime usage',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.setup.cloud', 'command', 'multica setup cloud',
        'transport', None, 'cli:multica setup cloud',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.setup.self-host', 'command', 'multica setup self-host',
        'transport', None, 'cli:multica setup self-host',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.create', 'command', 'multica skill create',
        'transport', None, 'cli:multica skill create',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.delete', 'command', 'multica skill delete',
        'transport', None, 'cli:multica skill delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.files.delete', 'command', 'multica skill files delete',
        'transport', None, 'cli:multica skill files delete',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.files.list', 'command', 'multica skill files list',
        'transport', None, 'cli:multica skill files list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.files.upsert', 'command', 'multica skill files upsert',
        'transport', None, 'cli:multica skill files upsert',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.get', 'command', 'multica skill get',
        'transport', None, 'cli:multica skill get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.import', 'command', 'multica skill import',
        'transport', None, 'cli:multica skill import',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.label.add', 'command', 'multica skill label add',
        'transport', None, 'cli:multica skill label add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.label.list', 'command', 'multica skill label list',
        'transport', None, 'cli:multica skill label list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.label.remove', 'command', 'multica skill label remove',
        'transport', None, 'cli:multica skill label remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.list', 'command', 'multica skill list',
        'transport', None, 'cli:multica skill list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.refresh', 'command', 'multica skill refresh',
        'transport', None, 'cli:multica skill refresh',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.search', 'command', 'multica skill search',
        'transport', None, 'cli:multica skill search',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.skill.update', 'command', 'multica skill update',
        'transport', None, 'cli:multica skill update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.activity', 'command', 'multica squad activity',
        'typed', 'multica_py.resources.squads.SquadResource.activity', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.create', 'command', 'multica squad create',
        'typed', 'multica_py.resources.squads.SquadResource.create', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.delete', 'command', 'multica squad delete',
        'typed', 'multica_py.resources.squads.SquadResource.delete', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.get', 'command', 'multica squad get',
        'transport', None, 'cli:multica squad get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.list', 'command', 'multica squad list',
        'transport', None, 'cli:multica squad list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.member.add', 'command', 'multica squad member add',
        'transport', None, 'cli:multica squad member add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.member.list', 'command', 'multica squad member list',
        'transport', None, 'cli:multica squad member list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.member.remove', 'command', 'multica squad member remove',
        'transport', None, 'cli:multica squad member remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.member.set-role', 'command', 'multica squad member set-role',
        'typed', 'multica_py.resources.squads.SquadResource.member_set_role', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.squad.update', 'command', 'multica squad update',
        'typed', 'multica_py.resources.squads.SquadResource.update', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.update', 'command', 'multica update',
        'transport', None, 'cli:multica update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.user.profile.get', 'command', 'multica user profile get',
        'transport', None, 'cli:multica user profile get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.user.profile.update', 'command', 'multica user profile update',
        'transport', None, 'cli:multica user profile update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.version', 'command', 'multica version',
        'transport', None, 'cli:multica version',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.create', 'command', 'multica workspace create',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.create', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.get', 'command', 'multica workspace get',
        'transport', None, 'cli:multica workspace get',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.list', 'command', 'multica workspace list',
        'transport', None, 'cli:multica workspace list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.mcp.add', 'command', 'multica workspace mcp add',
        'transport', None, 'cli:multica workspace mcp add',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.mcp.list', 'command', 'multica workspace mcp list',
        'transport', None, 'cli:multica workspace mcp list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.mcp.remove', 'command', 'multica workspace mcp remove',
        'transport', None, 'cli:multica workspace mcp remove',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.mcp.update', 'command', 'multica workspace mcp update',
        'transport', None, 'cli:multica workspace mcp update',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.member.invite', 'command', 'multica workspace member invite',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.member_invite', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.member.list', 'command', 'multica workspace member list',
        'transport', None, 'cli:multica workspace member list',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.switch', 'command', 'multica workspace switch',
        'transport', None, 'cli:multica workspace switch',
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'command:multica.workspace.update', 'command', 'multica workspace update',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.update', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'field:agent', 'field', 'agent',
        'typed-equivalent', 'Agent', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:agent_skills', 'field', 'agent_skills',
        'typed-equivalent', 'tuple[AgentSkill, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:agent_tasks', 'field', 'agent_tasks',
        'typed-equivalent', 'tuple[AgentTask, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:agent_wire', 'field', 'agent_wire',
        'typed-equivalent', 'AgentWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:attachment_result', 'field', 'attachment_result',
        'typed-equivalent', 'AttachmentResult', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:attachment_result_wire', 'field', 'attachment_result_wire',
        'typed-equivalent', 'AttachmentResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot', 'field', 'autopilot',
        'typed-equivalent', 'Autopilot', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_list_page', 'field', 'autopilot_list_page',
        'typed-equivalent', 'AutopilotListPage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_list_page_wire', 'field', 'autopilot_list_page_wire',
        'typed-equivalent', 'AutopilotListWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_run', 'field', 'autopilot_run',
        'typed-equivalent', 'AutopilotRun', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_run_list_page', 'field', 'autopilot_run_list_page',
        'typed-equivalent', 'AutopilotRunListPage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_run_list_page_wire', 'field', 'autopilot_run_list_page_wire',
        'typed-equivalent', 'AutopilotRunListPageWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_run_wire', 'field', 'autopilot_run_wire',
        'typed-equivalent', 'AutopilotRunWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_subscriber', 'field', 'autopilot_subscriber',
        'typed-equivalent', 'AutopilotSubscriber', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_subscriber_wire', 'field', 'autopilot_subscriber_wire',
        'typed-equivalent', 'AutopilotSubscriberWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_trigger', 'field', 'autopilot_trigger',
        'typed-equivalent', 'AutopilotTrigger', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_trigger_create', 'field', 'autopilot_trigger_create',
        'typed-equivalent', 'TriggerCreateFields', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_trigger_update', 'field', 'autopilot_trigger_update',
        'typed-equivalent', 'TriggerUpdateFields', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_trigger_wire', 'field', 'autopilot_trigger_wire',
        'typed-equivalent', 'AutopilotTriggerWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:autopilot_wire', 'field', 'autopilot_wire',
        'typed-equivalent', 'AutopilotWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:cli_result', 'field', 'cli_result',
        'typed-equivalent', 'CliResult', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comment', 'field', 'comment',
        'typed-equivalent', 'Comment', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comment_page', 'field', 'comment_page',
        'typed-equivalent', 'Page[Comment]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comment_thread_page', 'field', 'comment_thread_page',
        'typed-equivalent', 'Page[CommentThread]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comment_threads_wire', 'field', 'comment_threads_wire',
        'typed-equivalent', 'list[CommentThreadWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comment_wire', 'field', 'comment_wire',
        'typed-equivalent', 'CommentWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comments', 'field', 'comments',
        'typed-equivalent', 'tuple[Comment, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:comments_wire', 'field', 'comments_wire',
        'typed-equivalent', 'list[CommentWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue', 'field', 'issue',
        'typed-equivalent', 'Issue', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_children_result_wire', 'field', 'issue_children_result_wire',
        'typed-equivalent', 'IssueChildrenResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_list_filter', 'field', 'issue_list_filter',
        'typed-equivalent', 'IssueListFilter', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_list_page', 'field', 'issue_list_page',
        'typed-equivalent', 'IssueListPage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_list_page_wire', 'field', 'issue_list_page_wire',
        'typed-equivalent', 'IssueListPageWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_pull_requests_result_wire', 'field', 'issue_pull_requests_result_wire',
        'typed-equivalent', 'IssuePullRequestsResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_search_result_wire', 'field', 'issue_search_result_wire',
        'typed-equivalent', 'IssueSearchResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:issue_wire', 'field', 'issue_wire',
        'typed-equivalent', 'IssueWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:labels', 'field', 'labels',
        'typed-equivalent', 'tuple[Label, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:labels_wire', 'field', 'labels_wire',
        'typed-equivalent', 'list[Label]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:linked_pull_request', 'field', 'linked_pull_request',
        'typed-equivalent', 'LinkedPullRequest', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:linked_pull_requests', 'field', 'linked_pull_requests',
        'typed-equivalent', 'tuple[LinkedPullRequest, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:mcp_server', 'field', 'mcp_server',
        'typed-equivalent', 'McpServer', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:mcp_server_wire', 'field', 'mcp_server_wire',
        'typed-equivalent', 'McpServerWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:mcp_servers', 'field', 'mcp_servers',
        'typed-equivalent', 'tuple[McpServer, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:mcp_servers_wire', 'field', 'mcp_servers_wire',
        'typed-equivalent', 'list[McpServerWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:metadata_entries', 'field', 'metadata_entries',
        'typed-equivalent', 'tuple[MetadataEntry, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:metadata_entries_wire', 'field', 'metadata_entries_wire',
        'typed-equivalent', 'list[MetadataEntryWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:none', 'field', 'none',
        'typed-equivalent', 'None', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:operation_options', 'field', 'operation_options',
        'typed-equivalent', 'OperationOptions', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:page_issues', 'field', 'page_issues',
        'typed-equivalent', 'Page[Issue]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:path', 'field', 'path',
        'typed-equivalent', 'pathlib.Path', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:project', 'field', 'project',
        'typed-equivalent', 'Project', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:project_resource', 'field', 'project_resource',
        'typed-equivalent', 'ProjectResourceRecord', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:project_resource_wire', 'field', 'project_resource_wire',
        'typed-equivalent', 'ProjectResourceRecordWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:project_resources', 'field', 'project_resources',
        'typed-equivalent', 'tuple[ProjectResourceRecord, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:project_resources_wire', 'field', 'project_resources_wire',
        'typed-equivalent', 'list[ProjectResourceRecordWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:project_wire', 'field', 'project_wire',
        'typed-equivalent', 'ProjectWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_definition', 'field', 'property_definition',
        'typed-equivalent', 'PropertyDefinition', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_definition_wire', 'field', 'property_definition_wire',
        'typed-equivalent', 'PropertyDefinitionWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_definitions', 'field', 'property_definitions',
        'typed-equivalent', 'tuple[PropertyDefinition, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_definitions_wire', 'field', 'property_definitions_wire',
        'typed-equivalent', 'list[PropertyDefinitionWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_filter', 'field', 'property_filter',
        'typed-equivalent', 'str', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_sort', 'field', 'property_sort',
        'typed-equivalent', 'str', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_value', 'field', 'property_value',
        'typed-equivalent', 'PropertyValue', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_value_wire', 'field', 'property_value_wire',
        'typed-equivalent', 'PropertyValueWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_values', 'field', 'property_values',
        'typed-equivalent', 'tuple[PropertyValue, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:property_values_wire', 'field', 'property_values_wire',
        'typed-equivalent', 'list[PropertyValueWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:repository_mutation_result', 'field', 'repository_mutation_result',
        'typed-equivalent', 'RepositoryMutationResult', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:repository_mutation_result_wire', 'field', 'repository_mutation_result_wire',
        'typed-equivalent', 'RepositoryMutationResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:repository_record', 'field', 'repository_record',
        'typed-equivalent', 'RepositoryRecord', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:repository_record_wire', 'field', 'repository_record_wire',
        'typed-equivalent', 'RepositoryRecordWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:repository_records', 'field', 'repository_records',
        'typed-equivalent', 'tuple[RepositoryRecord, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:repository_records_wire', 'field', 'repository_records_wire',
        'typed-equivalent', 'list[RepositoryRecordWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:run_message', 'field', 'run_message',
        'typed-equivalent', 'RunMessage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:run_messages', 'field', 'run_messages',
        'typed-equivalent', 'tuple[RunMessage, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:run_messages_wire', 'field', 'run_messages_wire',
        'typed-equivalent', 'list[RunMessageWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_activity', 'field', 'runtime_activity',
        'typed-equivalent', 'RuntimeActivity', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_activity_wire', 'field', 'runtime_activity_wire',
        'typed-equivalent', 'RuntimeActivityWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_definition', 'field', 'runtime_definition',
        'typed-equivalent', 'RuntimeDefinition', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_definition_wire', 'field', 'runtime_definition_wire',
        'typed-equivalent', 'RuntimeDefinitionWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_definitions', 'field', 'runtime_definitions',
        'typed-equivalent', 'tuple[RuntimeDefinition, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_definitions_wire', 'field', 'runtime_definitions_wire',
        'typed-equivalent', 'list[RuntimeDefinitionWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_update_result', 'field', 'runtime_update_result',
        'typed-equivalent', 'RuntimeUpdateResult', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_update_result_wire', 'field', 'runtime_update_result_wire',
        'typed-equivalent', 'RuntimeUpdateResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_usage', 'field', 'runtime_usage',
        'typed-equivalent', 'RuntimeUsage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:runtime_usage_wire', 'field', 'runtime_usage_wire',
        'typed-equivalent', 'RuntimeUsageWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill', 'field', 'skill',
        'typed-equivalent', 'Skill', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_file', 'field', 'skill_file',
        'typed-equivalent', 'SkillFile', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_files', 'field', 'skill_files',
        'typed-equivalent', 'tuple[SkillFile, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_files_wire', 'field', 'skill_files_wire',
        'typed-equivalent', 'list[SkillFileWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_search_result', 'field', 'skill_search_result',
        'typed-equivalent', 'SkillSearchResult', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_search_result_wire', 'field', 'skill_search_result_wire',
        'typed-equivalent', 'SkillSearchResultWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_search_results', 'field', 'skill_search_results',
        'typed-equivalent', 'tuple[SkillSearchResult, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_search_results_wire', 'field', 'skill_search_results_wire',
        'typed-equivalent', 'list[SkillSearchResultWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:skill_wire', 'field', 'skill_wire',
        'typed-equivalent', 'SkillWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:squad', 'field', 'squad',
        'typed-equivalent', 'Squad', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:squad_member', 'field', 'squad_member',
        'typed-equivalent', 'SquadMember', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:squad_members', 'field', 'squad_members',
        'typed-equivalent', 'tuple[SquadMember, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:squad_members_wire', 'field', 'squad_members_wire',
        'typed-equivalent', 'list[SquadMemberWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:squad_wire', 'field', 'squad_wire',
        'typed-equivalent', 'SquadWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:subscriber', 'field', 'subscriber',
        'typed-equivalent', 'Subscriber', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:subscribers', 'field', 'subscribers',
        'typed-equivalent', 'tuple[Subscriber, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:subscribers_wire', 'field', 'subscribers_wire',
        'typed-equivalent', 'list[SubscriberWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:task_run', 'field', 'task_run',
        'typed-equivalent', 'TaskRun', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:task_runs', 'field', 'task_runs',
        'typed-equivalent', 'tuple[TaskRun, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:task_runs_wire', 'field', 'task_runs_wire',
        'typed-equivalent', 'list[TaskRunWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:user_profile', 'field', 'user_profile',
        'typed-equivalent', 'UserProfile', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:user_profile_wire', 'field', 'user_profile_wire',
        'typed-equivalent', 'UserProfileWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:workspace', 'field', 'workspace',
        'typed-equivalent', 'Workspace', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:workspace_member', 'field', 'workspace_member',
        'typed-equivalent', 'WorkspaceMember', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:workspace_members', 'field', 'workspace_members',
        'typed-equivalent', 'tuple[WorkspaceMember, ...]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:workspace_members_wire', 'field', 'workspace_members_wire',
        'typed-equivalent', 'list[WorkspaceMemberWire]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'field:workspace_wire', 'field', 'workspace_wire',
        'typed-equivalent', 'WorkspaceWire', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:agent_avatar', 'input', 'agent_avatar',
        'typed', 'multica_py.resources.agents.AgentResource.avatar', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_copy', 'input', 'agent_copy',
        'typed', 'multica_py.resources.agents.AgentResource.copy', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_get', 'input', 'agent_get',
        'typed', 'multica_py.resources.agents.AgentResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:agent_list', 'input', 'agent_list',
        'typed', 'multica_py.resources.agents.AgentResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_add', 'input', 'agent_mcp_add',
        'typed', 'multica_py.resources.agent_mcp.AgentMcpResource.add', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_add_bound', 'input', 'agent_mcp_add_bound',
        'typed', 'multica_py.entities.agents.Agent.add_mcp_server', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_disable', 'input', 'agent_mcp_disable',
        'typed', 'multica_py.resources.agent_mcp.AgentMcpResource.disable', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_disable_bound', 'input', 'agent_mcp_disable_bound',
        'typed', 'multica_py.entities.agents.Agent.disable_mcp_server', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_enable', 'input', 'agent_mcp_enable',
        'typed', 'multica_py.resources.agent_mcp.AgentMcpResource.enable', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_enable_bound', 'input', 'agent_mcp_enable_bound',
        'typed', 'multica_py.entities.agents.Agent.enable_mcp_server', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_list', 'input', 'agent_mcp_list',
        'typed', 'multica_py.resources.agent_mcp.AgentMcpResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_remove', 'input', 'agent_mcp_remove',
        'typed', 'multica_py.resources.agent_mcp.AgentMcpResource.remove', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_mcp_remove_bound', 'input', 'agent_mcp_remove_bound',
        'typed', 'multica_py.entities.agents.Agent.remove_mcp_server', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_skills_list', 'input', 'agent_skills_list',
        'typed', 'multica_py.resources.agent_skills.AgentSkillResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_skills_set', 'input', 'agent_skills_set',
        'typed', 'multica_py.resources.agent_skills.AgentSkillResource.set', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agent_tasks', 'input', 'agent_tasks',
        'typed', 'multica_py.resources.agents.AgentResource.tasks', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agents_archive_manual', 'input', 'agents_archive_manual',
        'typed', 'multica_py.resources.agents.AgentResource.archive', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:agents_create_manual', 'input', 'agents_create_manual',
        'typed', 'multica_py.resources.agents.AgentResource.create', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:agents_restore_manual', 'input', 'agents_restore_manual',
        'typed', 'multica_py.resources.agents.AgentResource.restore', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:agents_update_manual', 'input', 'agents_update_manual',
        'typed', 'multica_py.resources.agents.AgentResource.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:attachment_download', 'input', 'attachment_download',
        'typed', 'multica_py.resources.attachments.AttachmentResource.download', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:attachment_upload', 'input', 'attachment_upload',
        'typed', 'multica_py.resources.attachments.AttachmentResource.upload', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:attachments_download_bytes_manual', 'input', 'attachments_download_bytes_manual',
        'typed', 'multica_py.resources.attachments.AttachmentResource.download_bytes', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:attachments_upload_bytes_manual', 'input', 'attachments_upload_bytes_manual',
        'typed', 'multica_py.resources.attachments.AttachmentResource.upload_bytes', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:auth_login_manual', 'input', 'auth_login_manual',
        'typed', 'multica_py.resources.auth.AuthResource.login', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:auth_logout_manual', 'input', 'auth_logout_manual',
        'typed', 'multica_py.resources.auth.AuthResource.logout', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:auth_status_manual', 'input', 'auth_status_manual',
        'typed', 'multica_py.resources.auth.AuthResource.status', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:autopilot_create', 'input', 'autopilot_create',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.create', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_delete', 'input', 'autopilot_delete',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.delete', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_get', 'input', 'autopilot_get',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.get', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_history', 'input', 'autopilot_history',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.history', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_list', 'input', 'autopilot_list',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_trigger', 'input', 'autopilot_trigger',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.trigger', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_trigger_add', 'input', 'autopilot_trigger_add',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.trigger_add', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_trigger_delete', 'input', 'autopilot_trigger_delete',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.trigger_delete', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_trigger_update', 'input', 'autopilot_trigger_update',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.trigger_update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:autopilot_update', 'input', 'autopilot_update',
        'typed', 'multica_py.resources.autopilots.AutopilotResource.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:cli_command', 'input', 'cli_command',
        'typed', 'multica_py.resources.cli.CliResource.command', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:comment_add', 'input', 'comment_add',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.add', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:comment_delete', 'input', 'comment_delete',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.delete', None,
        'requires_cli>=0.4.44',
    ),
    GeneratedInventoryItem(
        'input:comment_list', 'input', 'comment_list',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:comment_list_flat', 'input', 'comment_list_flat',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.list_flat', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:comment_list_recent', 'input', 'comment_list_recent',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.list_recent', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:comment_list_thread', 'input', 'comment_list_thread',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.list_thread', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:comment_update', 'input', 'comment_update',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.update', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:configuration_get_manual', 'input', 'configuration_get_manual',
        'typed', 'multica_py.resources.configuration.ConfigurationResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:configuration_set_manual', 'input', 'configuration_set_manual',
        'typed', 'multica_py.resources.configuration.ConfigurationResource.set', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:configuration_show_manual', 'input', 'configuration_show_manual',
        'typed', 'multica_py.resources.configuration.ConfigurationResource.show', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:daemon_disk_usage_manual', 'input', 'daemon_disk_usage_manual',
        'typed', 'multica_py.resources.daemon.DaemonResource.disk_usage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:daemon_logs_manual', 'input', 'daemon_logs_manual',
        'typed', 'multica_py.resources.daemon.DaemonResource.logs', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:daemon_restart_manual', 'input', 'daemon_restart_manual',
        'typed', 'multica_py.resources.daemon.DaemonResource.restart', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:daemon_start_manual', 'input', 'daemon_start_manual',
        'typed', 'multica_py.resources.daemon.DaemonResource.start', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:daemon_status_manual', 'input', 'daemon_status_manual',
        'typed', 'multica_py.resources.daemon.DaemonResource.status', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:daemon_stop_manual', 'input', 'daemon_stop_manual',
        'typed', 'multica_py.resources.daemon.DaemonResource.stop', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_cancel_task', 'input', 'issue_cancel_task',
        'typed', 'multica_py.resources.issues.IssueResource.cancel_task', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_children', 'input', 'issue_children',
        'typed', 'multica_py.resources.issues.IssueResource.children', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_create', 'input', 'issue_create',
        'typed', 'multica_py.resources.issues.IssueResource.create', None,
        'requires_cli>=0.5.2',
    ),
    GeneratedInventoryItem(
        'input:issue_get', 'input', 'issue_get',
        'typed', 'multica_py.resources.issues.IssueResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_labels_add', 'input', 'issue_labels_add',
        'typed', 'multica_py.resources.issue_labels.IssueLabelResource.add', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_labels_list', 'input', 'issue_labels_list',
        'typed', 'multica_py.resources.issue_labels.IssueLabelResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_labels_remove', 'input', 'issue_labels_remove',
        'typed', 'multica_py.resources.issue_labels.IssueLabelResource.remove', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_list', 'input', 'issue_list',
        'typed', 'multica_py.resources.issues.IssueResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_metadata_delete', 'input', 'issue_metadata_delete',
        'typed', 'multica_py.resources.issue_metadata.IssueMetadataResource.delete', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_metadata_get', 'input', 'issue_metadata_get',
        'typed', 'multica_py.resources.issue_metadata.IssueMetadataResource.get', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_metadata_list', 'input', 'issue_metadata_list',
        'typed', 'multica_py.resources.issue_metadata.IssueMetadataResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_metadata_set', 'input', 'issue_metadata_set',
        'typed', 'multica_py.resources.issue_metadata.IssueMetadataResource.set', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_property_list', 'input', 'issue_property_list',
        'typed', 'multica_py.resources.issue_properties.IssuePropertyResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_property_set', 'input', 'issue_property_set',
        'typed', 'multica_py.resources.issue_properties.IssuePropertyResource.set', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_property_unset', 'input', 'issue_property_unset',
        'typed', 'multica_py.resources.issue_properties.IssuePropertyResource.unset', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_pull_requests', 'input', 'issue_pull_requests',
        'typed', 'multica_py.resources.issues.IssueResource.pull_requests', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_rerun', 'input', 'issue_rerun',
        'typed', 'multica_py.resources.issues.IssueResource.rerun', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_run_messages', 'input', 'issue_run_messages',
        'typed', 'multica_py.resources.issues.IssueResource.run_messages', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_runs', 'input', 'issue_runs',
        'typed', 'multica_py.resources.issues.IssueResource.runs', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_search', 'input', 'issue_search',
        'typed', 'multica_py.resources.issues.IssueResource.search', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issue_status', 'input', 'issue_status',
        'typed', 'multica_py.resources.issues.IssueResource.set_status', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_subscribers_add', 'input', 'issue_subscribers_add',
        'typed', 'multica_py.resources.issue_subscribers.IssueSubscriberResource.add', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_subscribers_list', 'input', 'issue_subscribers_list',
        'typed', 'multica_py.resources.issue_subscribers.IssueSubscriberResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issue_subscribers_remove', 'input', 'issue_subscribers_remove',
        'typed', 'multica_py.resources.issue_subscribers.IssueSubscriberResource.remove', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_assign_bound', 'input', 'issues_assign_bound',
        'typed', 'multica_py.resources.issues.Issue.assign', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_assign_manual', 'input', 'issues_assign_manual',
        'typed', 'multica_py.resources.issues.IssueResource.assign', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_comments_reply_manual', 'input', 'issues_comments_reply_manual',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.reply', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_comments_resolve_manual', 'input', 'issues_comments_resolve_manual',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.resolve', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_comments_unresolve_manual', 'input', 'issues_comments_unresolve_manual',
        'typed', 'multica_py.resources.issue_comments.IssueCommentResource.unresolve', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_metadata_query_manual', 'input', 'issues_metadata_query_manual',
        'typed', 'multica_py.resources.issue_metadata.IssueMetadataResource.query', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_metadata_set_typed_manual', 'input', 'issues_metadata_set_typed_manual',
        'typed', 'multica_py.resources.issue_metadata.IssueMetadataResource.set_typed', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_move_after', 'input', 'issues_move_after',
        'typed', 'multica_py.resources.issues.IssueResource.move_after', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_after_bound', 'input', 'issues_move_after_bound',
        'typed', 'multica_py.resources.issues.Issue.move_after', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_before', 'input', 'issues_move_before',
        'typed', 'multica_py.resources.issues.IssueResource.move_before', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_before_bound', 'input', 'issues_move_before_bound',
        'typed', 'multica_py.resources.issues.Issue.move_before', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_to_bottom', 'input', 'issues_move_to_bottom',
        'typed', 'multica_py.resources.issues.IssueResource.move_to_bottom', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_to_bottom_bound', 'input', 'issues_move_to_bottom_bound',
        'typed', 'multica_py.resources.issues.Issue.move_to_bottom', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_to_top', 'input', 'issues_move_to_top',
        'typed', 'multica_py.resources.issues.IssueResource.move_to_top', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_move_to_top_bound', 'input', 'issues_move_to_top_bound',
        'typed', 'multica_py.resources.issues.Issue.move_to_top', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_refresh', 'input', 'issues_refresh',
        'typed', 'multica_py.resources.issues.Issue.refresh', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_reorder_manual', 'input', 'issues_reorder_manual',
        'typed', 'multica_py.resources.issues.IssueResource.reorder', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:issues_set_status_bound', 'input', 'issues_set_status_bound',
        'typed', 'multica_py.resources.issues.Issue.set_status', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_unassign', 'input', 'issues_unassign',
        'typed', 'multica_py.resources.issues.IssueResource.unassign', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_unassign_bound', 'input', 'issues_unassign_bound',
        'typed', 'multica_py.resources.issues.Issue.unassign', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_update_bound', 'input', 'issues_update_bound',
        'typed', 'multica_py.resources.issues.Issue.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_update_manual', 'input', 'issues_update_manual',
        'typed', 'multica_py.resources.issues.IssueResource.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:issues_usage_manual', 'input', 'issues_usage_manual',
        'typed', 'multica_py.resources.issues.IssueResource.usage', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:label_get', 'input', 'label_get',
        'typed', 'multica_py.resources.labels.LabelResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:label_list', 'input', 'label_list',
        'typed', 'multica_py.resources.labels.LabelResource.list', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:labels_create_manual', 'input', 'labels_create_manual',
        'typed', 'multica_py.resources.labels.LabelResource.create', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:labels_delete_manual', 'input', 'labels_delete_manual',
        'typed', 'multica_py.resources.labels.LabelResource.delete', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:labels_update_manual', 'input', 'labels_update_manual',
        'typed', 'multica_py.resources.labels.LabelResource.update', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:maintenance_update_manual', 'input', 'maintenance_update_manual',
        'typed', 'multica_py.resources.maintenance.MaintenanceResource.update', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:maintenance_version_manual', 'input', 'maintenance_version_manual',
        'typed', 'multica_py.resources.maintenance.MaintenanceResource.version', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_create', 'input', 'project_create',
        'typed', 'multica_py.resources.projects.ProjectResource.create', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_get', 'input', 'project_get',
        'typed', 'multica_py.resources.projects.ProjectResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_issue_create', 'input', 'project_issue_create',
        'typed', 'multica_py.resources.projects.ProjectIssueCollection.create', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:project_list', 'input', 'project_list',
        'typed', 'multica_py.resources.projects.ProjectResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_resource_add', 'input', 'project_resource_add',
        'typed', 'multica_py.resources.project_resources.ProjectResourceCollection.add_local_directory', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_resource_list', 'input', 'project_resource_list',
        'typed', 'multica_py.resources.project_resources.ProjectResourceCollection.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_resource_remove', 'input', 'project_resource_remove',
        'typed', 'multica_py.resources.project_resources.ProjectResourceCollection.remove', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_resource_update', 'input', 'project_resource_update',
        'typed', 'multica_py.resources.project_resources.ProjectResourceCollection.update_local_directory', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_status', 'input', 'project_status',
        'typed', 'multica_py.resources.projects.ProjectResource.set_status', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:project_update', 'input', 'project_update',
        'typed', 'multica_py.resources.projects.ProjectResource.update', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:projects_delete_manual', 'input', 'projects_delete_manual',
        'typed', 'multica_py.resources.projects.ProjectResource.delete', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:projects_refresh', 'input', 'projects_refresh',
        'typed', 'multica_py.resources.projects.Project.refresh', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:projects_update_bound', 'input', 'projects_update_bound',
        'typed', 'multica_py.resources.projects.Project.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:property_archive', 'input', 'property_archive',
        'typed', 'multica_py.resources.properties.PropertyResource.archive', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:property_create', 'input', 'property_create',
        'typed', 'multica_py.resources.properties.PropertyResource.create', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:property_get', 'input', 'property_get',
        'typed', 'multica_py.resources.properties.PropertyResource.get', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:property_list', 'input', 'property_list',
        'typed', 'multica_py.resources.properties.PropertyResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:property_unarchive', 'input', 'property_unarchive',
        'typed', 'multica_py.resources.properties.PropertyResource.unarchive', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:property_update', 'input', 'property_update',
        'typed', 'multica_py.resources.properties.PropertyResource.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:repositories_add', 'input', 'repositories_add',
        'typed', 'multica_py.resources.repositories.RepositoryResource.add', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:repositories_list', 'input', 'repositories_list',
        'typed', 'multica_py.resources.repositories.RepositoryResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:repositories_remove', 'input', 'repositories_remove',
        'typed', 'multica_py.resources.repositories.RepositoryResource.remove', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:runtime_activity', 'input', 'runtime_activity',
        'typed', 'multica_py.resources.runtimes.RuntimeResource.activity', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:runtime_delete', 'input', 'runtime_delete',
        'typed', 'multica_py.resources.runtimes.RuntimeResource.delete', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:runtime_list', 'input', 'runtime_list',
        'typed', 'multica_py.resources.runtimes.RuntimeResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:runtime_rename', 'input', 'runtime_rename',
        'typed', 'multica_py.resources.runtimes.RuntimeResource.rename', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:runtime_update', 'input', 'runtime_update',
        'typed', 'multica_py.resources.runtimes.RuntimeResource.update', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:runtime_usage', 'input', 'runtime_usage',
        'typed', 'multica_py.resources.runtimes.RuntimeResource.usage', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:setup_cloud_manual', 'input', 'setup_cloud_manual',
        'typed', 'multica_py.resources.setup.SetupResource.cloud', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:setup_self_host_manual', 'input', 'setup_self_host_manual',
        'typed', 'multica_py.resources.setup.SetupResource.self_host', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:skill_files_delete', 'input', 'skill_files_delete',
        'typed', 'multica_py.resources.skill_files.SkillFileResource.delete', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:skill_files_list', 'input', 'skill_files_list',
        'typed', 'multica_py.resources.skill_files.SkillFileResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:skill_files_upsert', 'input', 'skill_files_upsert',
        'typed', 'multica_py.resources.skill_files.SkillFileResource.upsert', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:skill_get', 'input', 'skill_get',
        'typed', 'multica_py.resources.skills.SkillResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:skill_labels_add', 'input', 'skill_labels_add',
        'typed', 'multica_py.resources.skill_labels.SkillLabelResource.add', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:skill_labels_list', 'input', 'skill_labels_list',
        'typed', 'multica_py.resources.skill_labels.SkillLabelResource.list', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:skill_labels_remove', 'input', 'skill_labels_remove',
        'typed', 'multica_py.resources.skill_labels.SkillLabelResource.remove', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:skill_list', 'input', 'skill_list',
        'typed', 'multica_py.resources.skills.SkillResource.list', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'input:skill_refresh', 'input', 'skill_refresh',
        'typed', 'multica_py.resources.skills.SkillResource.refresh', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:skill_search', 'input', 'skill_search',
        'typed', 'multica_py.resources.skills.SkillResource.search', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:skills_create_manual', 'input', 'skills_create_manual',
        'typed', 'multica_py.resources.skills.SkillResource.create', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:skills_delete_manual', 'input', 'skills_delete_manual',
        'typed', 'multica_py.resources.skills.SkillResource.delete', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:skills_import_from_url_manual', 'input', 'skills_import_from_url_manual',
        'typed', 'multica_py.resources.skills.SkillResource.import_from_url', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:skills_update_manual', 'input', 'skills_update_manual',
        'typed', 'multica_py.resources.skills.SkillResource.update', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:squad_get', 'input', 'squad_get',
        'typed', 'multica_py.resources.squads.SquadResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:squad_list', 'input', 'squad_list',
        'typed', 'multica_py.resources.squads.SquadResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:squad_members_add', 'input', 'squad_members_add',
        'typed', 'multica_py.resources.squad_members.SquadMemberResource.add', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:squad_members_list', 'input', 'squad_members_list',
        'typed', 'multica_py.resources.squad_members.SquadMemberResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:squad_members_remove', 'input', 'squad_members_remove',
        'typed', 'multica_py.resources.squad_members.SquadMemberResource.remove', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:user_profile_get', 'input', 'user_profile_get',
        'typed', 'multica_py.resources.users.UserResource.profile_get', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:user_profile_update', 'input', 'user_profile_update',
        'typed', 'multica_py.resources.users.UserResource.profile_update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:workspace_get', 'input', 'workspace_get',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.get', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:workspace_list', 'input', 'workspace_list',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.list', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:workspace_mcp_add', 'input', 'workspace_mcp_add',
        'typed', 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.add', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:workspace_mcp_list', 'input', 'workspace_mcp_list',
        'typed', 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.list', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:workspace_mcp_remove', 'input', 'workspace_mcp_remove',
        'typed', 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.remove', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:workspace_mcp_update', 'input', 'workspace_mcp_update',
        'typed', 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.update', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'input:workspace_members_list', 'input', 'workspace_members_list',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.members', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'input:workspaces_switch_manual', 'input', 'workspaces_switch_manual',
        'typed', 'multica_py.resources.workspaces.WorkspaceResource.switch', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:action_result_none', 'output', 'action_result_none',
        'typed', 'ActionResult[None]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:action_result_repository_mutation_result', 'output', 'action_result_repository_mutation_result',
        'typed', 'ActionResult[RepositoryMutationResult]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:action_result_runtime_update_result', 'output', 'action_result_runtime_update_result',
        'typed', 'ActionResult[RuntimeUpdateResult]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:action_result_str', 'output', 'action_result_str',
        'typed', 'ActionResult[str]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:agent', 'output', 'agent',
        'typed', 'agent', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:agent_skills', 'output', 'agent_skills',
        'typed', 'agent_skills', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:agent_tasks', 'output', 'agent_tasks',
        'typed', 'agent_tasks', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:attachment_result', 'output', 'attachment_result',
        'typed', 'attachment_result', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:autopilot', 'output', 'autopilot',
        'typed', 'autopilot', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:autopilot_list_page', 'output', 'autopilot_list_page',
        'typed', 'autopilot_list_page', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:autopilot_run', 'output', 'autopilot_run',
        'typed', 'autopilot_run', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:autopilot_run_list_page', 'output', 'autopilot_run_list_page',
        'typed', 'autopilot_run_list_page', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:autopilot_trigger', 'output', 'autopilot_trigger',
        'typed', 'autopilot_trigger', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:bytes', 'output', 'bytes',
        'typed', 'bytes', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:cli_result', 'output', 'cli_result',
        'typed', 'CliResult', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:comment', 'output', 'comment',
        'typed', 'comment', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:comment_page', 'output', 'comment_page',
        'typed', 'comment_page', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:comment_thread_page', 'output', 'comment_thread_page',
        'typed', 'comment_thread_page', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:comments', 'output', 'comments',
        'typed', 'comments', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:issue', 'output', 'issue',
        'typed', 'issue', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:issue_children_result', 'output', 'issue_children_result',
        'typed', 'issue_child_stage_groups', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:issue_list_page', 'output', 'issue_list_page',
        'typed', 'issue_list_page', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:labels', 'output', 'labels',
        'typed', 'labels', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'output:linked_pull_requests', 'output', 'linked_pull_requests',
        'typed', 'linked_pull_requests', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:mapping_config', 'output', 'mapping_config',
        'typed', 'Mapping[str, str]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:metadata_entries', 'output', 'metadata_entries',
        'typed', 'metadata_entries', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:none', 'output', 'none',
        'typed', 'none', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:page_agent', 'output', 'page_agent',
        'typed', 'Page[agent]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_agent_skills', 'output', 'page_agent_skills',
        'typed', 'Page[agent_skills]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_agent_tasks', 'output', 'page_agent_tasks',
        'typed', 'Page[agent_tasks]', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:page_comments', 'output', 'page_comments',
        'typed', 'Page[Comment]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_daemon_disk_usage', 'output', 'page_daemon_disk_usage',
        'typed', 'Page[disk_usage]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_issue_usage', 'output', 'page_issue_usage',
        'typed', 'Page[issue_usage]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_issues', 'output', 'page_issues',
        'typed', 'Page[Issue]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_labels', 'output', 'page_labels',
        'typed', 'Page[labels]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_linked_pull_requests', 'output', 'page_linked_pull_requests',
        'typed', 'Page[linked_pull_requests]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_mcp_servers', 'output', 'page_mcp_servers',
        'typed', 'Page[mcp_server]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_project', 'output', 'page_project',
        'typed', 'Page[project]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_project_resources', 'output', 'page_project_resources',
        'typed', 'Page[project_resources]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_property_definitions', 'output', 'page_property_definitions',
        'typed', 'Page[property_definition]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_repository_records', 'output', 'page_repository_records',
        'typed', 'Page[repository_records]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_run_messages', 'output', 'page_run_messages',
        'typed', 'Page[run_messages]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_runtime_activity', 'output', 'page_runtime_activity',
        'typed', 'Page[runtime_activity]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_runtime_definitions', 'output', 'page_runtime_definitions',
        'typed', 'Page[runtime_definitions]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_runtime_usage', 'output', 'page_runtime_usage',
        'typed', 'Page[runtime_usage]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_skill', 'output', 'page_skill',
        'typed', 'Page[skill]', None,
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'output:page_skill_files', 'output', 'page_skill_files',
        'typed', 'Page[skill_files]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_skill_search_results', 'output', 'page_skill_search_results',
        'typed', 'Page[skill_search_result]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_squad', 'output', 'page_squad',
        'typed', 'Page[squad]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_squad_members', 'output', 'page_squad_members',
        'typed', 'Page[squad_members]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_subscribers', 'output', 'page_subscribers',
        'typed', 'Page[subscribers]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_task_runs', 'output', 'page_task_runs',
        'typed', 'Page[task_runs]', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:page_workspace', 'output', 'page_workspace',
        'typed', 'Page[workspace]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:page_workspace_members', 'output', 'page_workspace_members',
        'typed', 'Page[workspace_members]', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:path', 'output', 'path',
        'typed', 'path', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:process', 'output', 'process',
        'typed', 'ManagedProcess', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:project', 'output', 'project',
        'typed', 'project', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:project_resource', 'output', 'project_resource',
        'typed', 'project_resource', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:project_resources', 'output', 'project_resources',
        'typed', 'project_resources', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:property_definition', 'output', 'property_definition',
        'typed', 'property_definition', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:property_values', 'output', 'property_values',
        'typed', 'property_values', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:repository_mutation_result', 'output', 'repository_mutation_result',
        'typed', 'repository_mutation_result', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:repository_records', 'output', 'repository_records',
        'typed', 'repository_records', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:run_messages', 'output', 'run_messages',
        'typed', 'run_messages', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:runtime_activity', 'output', 'runtime_activity',
        'typed', 'runtime_activity', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:runtime_definition', 'output', 'runtime_definition',
        'typed', 'runtime_definition', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:runtime_definitions', 'output', 'runtime_definitions',
        'typed', 'runtime_definitions', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:runtime_update_result', 'output', 'runtime_update_result',
        'typed', 'runtime_update_result', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:runtime_usage', 'output', 'runtime_usage',
        'typed', 'runtime_usage', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:scalar_str', 'output', 'scalar_str',
        'typed', 'str', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:skill', 'output', 'skill',
        'typed', 'skill', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:skill_file', 'output', 'skill_file',
        'typed', 'skill_file', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:skill_files', 'output', 'skill_files',
        'typed', 'skill_files', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:skill_search_result', 'output', 'skill_search_result',
        'typed', 'skill_search_result', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:squad', 'output', 'squad',
        'typed', 'squad', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:squad_members', 'output', 'squad_members',
        'typed', 'squad_members', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:subscribers', 'output', 'subscribers',
        'typed', 'subscribers', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:task_runs', 'output', 'task_runs',
        'typed', 'task_runs', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'output:user_profile', 'output', 'user_profile',
        'typed', 'user_profile', None,
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'output:workspace', 'output', 'workspace',
        'typed', 'workspace', None,
        'compatible',
    ),
    GeneratedInventoryItem(
        'output:workspace_members', 'output', 'workspace_members',
        'typed', 'workspace_members', None,
        'requires_cli>=0.5.3',
    ),
    GeneratedInventoryItem(
        'transport:agent_avatar', 'transport', 'agent_avatar',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_copy', 'transport', 'agent_copy',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_get', 'transport', 'agent_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:agent_list', 'transport', 'agent_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_add', 'transport', 'agent_mcp_add',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_add_bound', 'transport', 'agent_mcp_add_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_disable', 'transport', 'agent_mcp_disable',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_disable_bound', 'transport', 'agent_mcp_disable_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_enable', 'transport', 'agent_mcp_enable',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_enable_bound', 'transport', 'agent_mcp_enable_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_list', 'transport', 'agent_mcp_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_remove', 'transport', 'agent_mcp_remove',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_mcp_remove_bound', 'transport', 'agent_mcp_remove_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_skills_list', 'transport', 'agent_skills_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_skills_set', 'transport', 'agent_skills_set',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agent_tasks', 'transport', 'agent_tasks',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agents_archive_manual', 'transport', 'agents_archive_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:agents_create_manual', 'transport', 'agents_create_manual',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:agents_restore_manual', 'transport', 'agents_restore_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:agents_update_manual', 'transport', 'agents_update_manual',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:attachment_download', 'transport', 'attachment_download',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:attachment_upload', 'transport', 'attachment_upload',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:attachments_download_bytes_manual', 'transport', 'attachments_download_bytes_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:attachments_upload_bytes_manual', 'transport', 'attachments_upload_bytes_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:auth_login_manual', 'transport', 'auth_login_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:auth_logout_manual', 'transport', 'auth_logout_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:auth_status_manual', 'transport', 'auth_status_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_create', 'transport', 'autopilot_create',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_delete', 'transport', 'autopilot_delete',
        'transport', None, 'run_text',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_get', 'transport', 'autopilot_get',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_history', 'transport', 'autopilot_history',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_list', 'transport', 'autopilot_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_trigger', 'transport', 'autopilot_trigger',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_trigger_add', 'transport', 'autopilot_trigger_add',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_trigger_delete', 'transport', 'autopilot_trigger_delete',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_trigger_update', 'transport', 'autopilot_trigger_update',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:autopilot_update', 'transport', 'autopilot_update',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:cli_command', 'transport', 'cli_command',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:comment_add', 'transport', 'comment_add',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:comment_delete', 'transport', 'comment_delete',
        'transport', None, 'run_text',
        'requires_cli>=0.4.44',
    ),
    GeneratedInventoryItem(
        'transport:comment_list', 'transport', 'comment_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:comment_list_flat', 'transport', 'comment_list_flat',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:comment_list_recent', 'transport', 'comment_list_recent',
        'transport', None, 'run_text',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:comment_list_thread', 'transport', 'comment_list_thread',
        'transport', None, 'run_text',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:comment_update', 'transport', 'comment_update',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:configuration_get_manual', 'transport', 'configuration_get_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:configuration_set_manual', 'transport', 'configuration_set_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:configuration_show_manual', 'transport', 'configuration_show_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:daemon_disk_usage_manual', 'transport', 'daemon_disk_usage_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:daemon_logs_manual', 'transport', 'daemon_logs_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:daemon_restart_manual', 'transport', 'daemon_restart_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:daemon_start_manual', 'transport', 'daemon_start_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:daemon_status_manual', 'transport', 'daemon_status_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:daemon_stop_manual', 'transport', 'daemon_stop_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_cancel_task', 'transport', 'issue_cancel_task',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_children', 'transport', 'issue_children',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_create', 'transport', 'issue_create',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.2',
    ),
    GeneratedInventoryItem(
        'transport:issue_get', 'transport', 'issue_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_labels_add', 'transport', 'issue_labels_add',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_labels_list', 'transport', 'issue_labels_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_labels_remove', 'transport', 'issue_labels_remove',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_list', 'transport', 'issue_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_metadata_delete', 'transport', 'issue_metadata_delete',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_metadata_get', 'transport', 'issue_metadata_get',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_metadata_list', 'transport', 'issue_metadata_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_metadata_set', 'transport', 'issue_metadata_set',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_property_list', 'transport', 'issue_property_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_property_set', 'transport', 'issue_property_set',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_property_unset', 'transport', 'issue_property_unset',
        'transport', None, 'run_text',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_pull_requests', 'transport', 'issue_pull_requests',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_rerun', 'transport', 'issue_rerun',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_run_messages', 'transport', 'issue_run_messages',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_runs', 'transport', 'issue_runs',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_search', 'transport', 'issue_search',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issue_status', 'transport', 'issue_status',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_subscribers_add', 'transport', 'issue_subscribers_add',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_subscribers_list', 'transport', 'issue_subscribers_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issue_subscribers_remove', 'transport', 'issue_subscribers_remove',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_assign_bound', 'transport', 'issues_assign_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_assign_manual', 'transport', 'issues_assign_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_comments_reply_manual', 'transport', 'issues_comments_reply_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_comments_resolve_manual', 'transport', 'issues_comments_resolve_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_comments_unresolve_manual', 'transport', 'issues_comments_unresolve_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_metadata_query_manual', 'transport', 'issues_metadata_query_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_metadata_set_typed_manual', 'transport', 'issues_metadata_set_typed_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_after', 'transport', 'issues_move_after',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_after_bound', 'transport', 'issues_move_after_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_before', 'transport', 'issues_move_before',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_before_bound', 'transport', 'issues_move_before_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_to_bottom', 'transport', 'issues_move_to_bottom',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_to_bottom_bound', 'transport', 'issues_move_to_bottom_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_to_top', 'transport', 'issues_move_to_top',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_move_to_top_bound', 'transport', 'issues_move_to_top_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_refresh', 'transport', 'issues_refresh',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_reorder_manual', 'transport', 'issues_reorder_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:issues_set_status_bound', 'transport', 'issues_set_status_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_unassign', 'transport', 'issues_unassign',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_unassign_bound', 'transport', 'issues_unassign_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_update_bound', 'transport', 'issues_update_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_update_manual', 'transport', 'issues_update_manual',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:issues_usage_manual', 'transport', 'issues_usage_manual',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:label_get', 'transport', 'label_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:label_list', 'transport', 'label_list',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:labels_create_manual', 'transport', 'labels_create_manual',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:labels_delete_manual', 'transport', 'labels_delete_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:labels_update_manual', 'transport', 'labels_update_manual',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:maintenance_update_manual', 'transport', 'maintenance_update_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:maintenance_version_manual', 'transport', 'maintenance_version_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_create', 'transport', 'project_create',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_get', 'transport', 'project_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_issue_create', 'transport', 'project_issue_create',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:project_list', 'transport', 'project_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_resource_add', 'transport', 'project_resource_add',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_resource_list', 'transport', 'project_resource_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_resource_remove', 'transport', 'project_resource_remove',
        'transport', None, 'run_text',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_resource_update', 'transport', 'project_resource_update',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_status', 'transport', 'project_status',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:project_update', 'transport', 'project_update',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:projects_delete_manual', 'transport', 'projects_delete_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:projects_refresh', 'transport', 'projects_refresh',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:projects_update_bound', 'transport', 'projects_update_bound',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:property_archive', 'transport', 'property_archive',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:property_create', 'transport', 'property_create',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:property_get', 'transport', 'property_get',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:property_list', 'transport', 'property_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:property_unarchive', 'transport', 'property_unarchive',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:property_update', 'transport', 'property_update',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:repositories_add', 'transport', 'repositories_add',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:repositories_list', 'transport', 'repositories_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:repositories_remove', 'transport', 'repositories_remove',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:runtime_activity', 'transport', 'runtime_activity',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:runtime_delete', 'transport', 'runtime_delete',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:runtime_list', 'transport', 'runtime_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:runtime_rename', 'transport', 'runtime_rename',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:runtime_update', 'transport', 'runtime_update',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:runtime_usage', 'transport', 'runtime_usage',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:setup_cloud_manual', 'transport', 'setup_cloud_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:setup_self_host_manual', 'transport', 'setup_self_host_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:skill_files_delete', 'transport', 'skill_files_delete',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:skill_files_list', 'transport', 'skill_files_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:skill_files_upsert', 'transport', 'skill_files_upsert',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:skill_get', 'transport', 'skill_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:skill_labels_add', 'transport', 'skill_labels_add',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:skill_labels_list', 'transport', 'skill_labels_list',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:skill_labels_remove', 'transport', 'skill_labels_remove',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:skill_list', 'transport', 'skill_list',
        'transport', None, 'run_bytes',
        'requires_cli>=0.5.0',
    ),
    GeneratedInventoryItem(
        'transport:skill_refresh', 'transport', 'skill_refresh',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:skill_search', 'transport', 'skill_search',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:skills_create_manual', 'transport', 'skills_create_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:skills_delete_manual', 'transport', 'skills_delete_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:skills_import_from_url_manual', 'transport', 'skills_import_from_url_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:skills_update_manual', 'transport', 'skills_update_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:squad_get', 'transport', 'squad_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:squad_list', 'transport', 'squad_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:squad_members_add', 'transport', 'squad_members_add',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:squad_members_list', 'transport', 'squad_members_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:squad_members_remove', 'transport', 'squad_members_remove',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:user_profile_get', 'transport', 'user_profile_get',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:user_profile_update', 'transport', 'user_profile_update',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:workspace_get', 'transport', 'workspace_get',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:workspace_list', 'transport', 'workspace_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:workspace_mcp_add', 'transport', 'workspace_mcp_add',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:workspace_mcp_list', 'transport', 'workspace_mcp_list',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:workspace_mcp_remove', 'transport', 'workspace_mcp_remove',
        'transport', None, 'run_text',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:workspace_mcp_update', 'transport', 'workspace_mcp_update',
        'transport', None, 'run_bytes',
        'intentionally_changed',
    ),
    GeneratedInventoryItem(
        'transport:workspace_members_list', 'transport', 'workspace_members_list',
        'transport', None, 'run_bytes',
        'compatible',
    ),
    GeneratedInventoryItem(
        'transport:workspaces_switch_manual', 'transport', 'workspaces_switch_manual',
        'transport', None, 'run_bytes',
        'compatible',
    ),
)

OPERATION_CONVENTIONS: tuple[GeneratedConvention, ...] = (
    GeneratedConvention(
        'agents.archive', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.archive_command',
    ),
    GeneratedConvention(
        'agents.avatar', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.avatar_command',
    ),
    GeneratedConvention(
        'agents.copy', 'default',
        'create', 'agent',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.copy_command',
    ),
    GeneratedConvention(
        'agents.create', 'default',
        'create', 'agent',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.create_command',
    ),
    GeneratedConvention(
        'agents.env.get', 'default',
        'retrieve', 'mapping_config',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.env_get_command',
    ),
    GeneratedConvention(
        'agents.env.set', 'default',
        'update', 'mapping_config',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.env_set_command',
    ),
    GeneratedConvention(
        'agents.get', 'default',
        'retrieve', 'agent',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.get_command',
    ),
    GeneratedConvention(
        'agents.list', 'default',
        'collection', 'page_agent',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.list_command',
    ),
    GeneratedConvention(
        'agents.mcp.add', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_mcp.AgentMcpResource.add_command',
    ),
    GeneratedConvention(
        'agents.mcp.add_bound', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.entities.agents.Agent.add_mcp_server_command',
    ),
    GeneratedConvention(
        'agents.mcp.disable', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_mcp.AgentMcpResource.disable_command',
    ),
    GeneratedConvention(
        'agents.mcp.disable_bound', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.entities.agents.Agent.disable_mcp_server_command',
    ),
    GeneratedConvention(
        'agents.mcp.enable', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_mcp.AgentMcpResource.enable_command',
    ),
    GeneratedConvention(
        'agents.mcp.enable_bound', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.entities.agents.Agent.enable_mcp_server_command',
    ),
    GeneratedConvention(
        'agents.mcp.list', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_mcp.AgentMcpResource.list_command',
    ),
    GeneratedConvention(
        'agents.mcp.remove', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_mcp.AgentMcpResource.remove_command',
    ),
    GeneratedConvention(
        'agents.mcp.remove_bound', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.entities.agents.Agent.remove_mcp_server_command',
    ),
    GeneratedConvention(
        'agents.restore', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.restore_command',
    ),
    GeneratedConvention(
        'agents.skills.add', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.skills_add_command',
    ),
    GeneratedConvention(
        'agents.skills.list', 'default',
        'collection', 'page_agent_skills',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_skills.AgentSkillResource.list_command',
    ),
    GeneratedConvention(
        'agents.skills.set', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.agent_skills.AgentSkillResource.set_command',
    ),
    GeneratedConvention(
        'agents.tasks', 'default',
        'collection', 'page_task_runs',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.tasks_command',
    ),
    GeneratedConvention(
        'agents.update', 'default',
        'update', 'agent',
        None,
        None, 'direct',
        (), 'multica_py.resources.agents.AgentResource.update_command',
    ),
    GeneratedConvention(
        'attachments.download', 'default',
        'scalar', 'path',
        None,
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.download_command',
    ),
    GeneratedConvention(
        'attachments.download_bytes', 'default',
        'retrieve', 'bytes',
        None,
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.download_bytes_command',
    ),
    GeneratedConvention(
        'attachments.upload', 'default',
        'retrieve', 'attachment_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.upload_command',
    ),
    GeneratedConvention(
        'attachments.upload_bytes', 'default',
        'action', 'attachment_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.attachments.AttachmentResource.upload_bytes_command',
    ),
    GeneratedConvention(
        'auth.login', 'default',
        'action', 'action_result_str',
        None,
        None, 'direct',
        (), 'multica_py.resources.auth.AuthResource.login_command',
    ),
    GeneratedConvention(
        'auth.logout', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.auth.AuthResource.logout_command',
    ),
    GeneratedConvention(
        'auth.status', 'default',
        'scalar', 'scalar_str',
        None,
        None, 'direct',
        (), 'multica_py.resources.auth.AuthResource.status_command',
    ),
    GeneratedConvention(
        'autopilots.create', 'default',
        'create', 'autopilot',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.create_command',
    ),
    GeneratedConvention(
        'autopilots.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.delete_command',
    ),
    GeneratedConvention(
        'autopilots.get', 'default',
        'retrieve', 'autopilot',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.get_command',
    ),
    GeneratedConvention(
        'autopilots.history', 'default',
        'collection', 'autopilot_run_list_page',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.history_command',
    ),
    GeneratedConvention(
        'autopilots.list', 'default',
        'collection', 'autopilot_list_page',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.list_command',
    ),
    GeneratedConvention(
        'autopilots.trigger', 'default',
        'retrieve', 'autopilot_run',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_add', 'default',
        'retrieve', 'autopilot_trigger',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_add_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_delete_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_list', 'default',
        'collection', 'mapping_config',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_list_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_rotate_url', 'default',
        'action', 'autopilot_trigger_rotate_url',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_rotate_url_command',
    ),
    GeneratedConvention(
        'autopilots.trigger_update', 'default',
        'retrieve', 'autopilot_trigger',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.trigger_update_command',
    ),
    GeneratedConvention(
        'autopilots.update', 'default',
        'update', 'autopilot',
        None,
        None, 'direct',
        (), 'multica_py.resources.autopilots.AutopilotResource.update_command',
    ),
    GeneratedConvention(
        'chats.history', 'default',
        'collection', 'chat_history',
        None,
        None, 'direct',
        (), 'multica_py.resources.chats.ChatResource.history_command',
    ),
    GeneratedConvention(
        'chats.thread', 'default',
        'collection', 'chat_thread',
        None,
        None, 'direct',
        (), 'multica_py.resources.chats.ChatResource.thread_command',
    ),
    GeneratedConvention(
        'cli.command', 'default',
        'action', 'cli_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.cli.CliResource.command_command',
    ),
    GeneratedConvention(
        'configuration.get', 'default',
        'scalar', 'scalar_str',
        None,
        None, 'direct',
        (), 'multica_py.resources.configuration.ConfigurationResource.get_command',
    ),
    GeneratedConvention(
        'configuration.set', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.configuration.ConfigurationResource.set_command',
    ),
    GeneratedConvention(
        'configuration.show', 'default',
        'mapping', 'mapping_config',
        None,
        None, 'direct',
        (), 'multica_py.resources.configuration.ConfigurationResource.show_command',
    ),
    GeneratedConvention(
        'daemon.disk_usage', 'default',
        'collection', 'page_daemon_disk_usage',
        None,
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.disk_usage_command',
    ),
    GeneratedConvention(
        'daemon.logs', 'default',
        'process', 'process',
        None,
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.logs_command',
    ),
    GeneratedConvention(
        'daemon.restart', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.restart_command',
    ),
    GeneratedConvention(
        'daemon.start', 'default',
        'process', 'process',
        None,
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.start_command',
    ),
    GeneratedConvention(
        'daemon.status', 'default',
        'retrieve', 'runtime_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.status_command',
    ),
    GeneratedConvention(
        'daemon.stop', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.daemon.DaemonResource.stop_command',
    ),
    GeneratedConvention(
        'issues.assign', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.assign_command',
    ),
    GeneratedConvention(
        'issues.assign_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.assign_command',
    ),
    GeneratedConvention(
        'issues.cancel_task', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.cancel_task_command',
    ),
    GeneratedConvention(
        'issues.children', 'default',
        'collection', 'issue_children_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.children_command',
    ),
    GeneratedConvention(
        'issues.comments.add', 'default',
        'retrieve', 'comment',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.add_command',
    ),
    GeneratedConvention(
        'issues.comments.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.delete_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'direct',
        'collection', 'page_comments',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.list_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'flat',
        'collection', 'comment_page',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.list_flat_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'recent',
        'collection', 'comment_thread_page',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.list_recent_command',
    ),
    GeneratedConvention(
        'issues.comments.list', 'thread',
        'collection', 'comment_page',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.list_thread_command',
    ),
    GeneratedConvention(
        'issues.comments.reply', 'default',
        'create', 'comment',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.reply_command',
    ),
    GeneratedConvention(
        'issues.comments.resolve', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.resolve_command',
    ),
    GeneratedConvention(
        'issues.comments.unresolve', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.unresolve_command',
    ),
    GeneratedConvention(
        'issues.comments.update', 'default',
        'update', 'comment',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_comments.IssueCommentResource.update_command',
    ),
    GeneratedConvention(
        'issues.create', 'default',
        'create', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.create_command',
    ),
    GeneratedConvention(
        'issues.get', 'default',
        'retrieve', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.get_command',
    ),
    GeneratedConvention(
        'issues.labels.add', 'default',
        'collection', 'page_labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_labels.IssueLabelResource.add_command',
    ),
    GeneratedConvention(
        'issues.labels.list', 'default',
        'collection', 'page_labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_labels.IssueLabelResource.list_command',
    ),
    GeneratedConvention(
        'issues.labels.remove', 'default',
        'collection', 'page_labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_labels.IssueLabelResource.remove_command',
    ),
    GeneratedConvention(
        'issues.list', 'default',
        'collection', 'issue_list_page',
        None,
        'IssueListFilter', 'dual_optional',
        ('omit',), 'multica_py.resources.issues.IssueResource.list_command',
    ),
    GeneratedConvention(
        'issues.metadata.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.delete_command',
    ),
    GeneratedConvention(
        'issues.metadata.get', 'default',
        'retrieve', 'metadata_entries',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.get_command',
    ),
    GeneratedConvention(
        'issues.metadata.list', 'default',
        'collection', 'metadata_entries',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.list_command',
    ),
    GeneratedConvention(
        'issues.metadata.query', 'default',
        'mapping', 'metadata_entries',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.query_command',
    ),
    GeneratedConvention(
        'issues.metadata.set', 'default',
        'update', 'metadata_entries',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.set_command',
    ),
    GeneratedConvention(
        'issues.metadata.set_typed', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_metadata.IssueMetadataResource.set_typed_command',
    ),
    GeneratedConvention(
        'issues.move_after', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.move_after_command',
    ),
    GeneratedConvention(
        'issues.move_after_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.move_after_command',
    ),
    GeneratedConvention(
        'issues.move_before', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.move_before_command',
    ),
    GeneratedConvention(
        'issues.move_before_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.move_before_command',
    ),
    GeneratedConvention(
        'issues.move_to_bottom', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.move_to_bottom_command',
    ),
    GeneratedConvention(
        'issues.move_to_bottom_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.move_to_bottom_command',
    ),
    GeneratedConvention(
        'issues.move_to_top', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.move_to_top_command',
    ),
    GeneratedConvention(
        'issues.move_to_top_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.move_to_top_command',
    ),
    GeneratedConvention(
        'issues.properties.list', 'default',
        'collection', 'property_values',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_properties.IssuePropertyResource.list_command',
    ),
    GeneratedConvention(
        'issues.properties.set', 'default',
        'update', 'property_values',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_properties.IssuePropertyResource.set_command',
    ),
    GeneratedConvention(
        'issues.properties.unset', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_properties.IssuePropertyResource.unset_command',
    ),
    GeneratedConvention(
        'issues.pull_requests', 'default',
        'collection', 'page_linked_pull_requests',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.pull_requests_command',
    ),
    GeneratedConvention(
        'issues.refresh', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.refresh_command',
    ),
    GeneratedConvention(
        'issues.reorder', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.reorder_command',
    ),
    GeneratedConvention(
        'issues.rerun', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.rerun_command',
    ),
    GeneratedConvention(
        'issues.run_messages', 'default',
        'collection', 'page_run_messages',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.run_messages_command',
    ),
    GeneratedConvention(
        'issues.runs', 'default',
        'collection', 'page_task_runs',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.runs_command',
    ),
    GeneratedConvention(
        'issues.search', 'default',
        'collection', 'page_issues',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.search_command',
    ),
    GeneratedConvention(
        'issues.set_status', 'default',
        'update', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.set_status_command',
    ),
    GeneratedConvention(
        'issues.set_status_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.set_status_command',
    ),
    GeneratedConvention(
        'issues.subscribers.add', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_subscribers.IssueSubscriberResource.add_command',
    ),
    GeneratedConvention(
        'issues.subscribers.list', 'default',
        'collection', 'page_subscribers',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_subscribers.IssueSubscriberResource.list_command',
    ),
    GeneratedConvention(
        'issues.subscribers.remove', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_subscribers.IssueSubscriberResource.remove_command',
    ),
    GeneratedConvention(
        'issues.timeline', 'default',
        'collection', 'issue_timeline',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.timeline_command',
    ),
    GeneratedConvention(
        'issues.unassign', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.unassign_command',
    ),
    GeneratedConvention(
        'issues.unassign_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.unassign_command',
    ),
    GeneratedConvention(
        'issues.update', 'default',
        'update', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.update_command',
    ),
    GeneratedConvention(
        'issues.update_bound', 'default',
        'action', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.Issue.update_command',
    ),
    GeneratedConvention(
        'issues.usage', 'default',
        'collection', 'page_issue_usage',
        None,
        None, 'direct',
        (), 'multica_py.resources.issues.IssueResource.usage_command',
    ),
    GeneratedConvention(
        'issues.wakeups.create', 'default',
        'create', 'issue_wakeup_create',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_wakeups.IssueWakeupResource.create_command',
    ),
    GeneratedConvention(
        'issues.wakeups.disable', 'default',
        'action', 'issue_wakeup_disable',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_wakeups.IssueWakeupResource.disable_command',
    ),
    GeneratedConvention(
        'issues.wakeups.events', 'default',
        'retrieve', 'issue_wakeup_events',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_wakeups.IssueWakeupResource.events_command',
    ),
    GeneratedConvention(
        'issues.wakeups.get', 'default',
        'retrieve', 'issue_wakeup_get',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_wakeups.IssueWakeupResource.get_command',
    ),
    GeneratedConvention(
        'issues.wakeups.list', 'default',
        'collection', 'issue_wakeup_list',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_wakeups.IssueWakeupResource.list_command',
    ),
    GeneratedConvention(
        'issues.wakeups.update', 'default',
        'update', 'issue_wakeup_update',
        None,
        None, 'direct',
        (), 'multica_py.resources.issue_wakeups.IssueWakeupResource.update_command',
    ),
    GeneratedConvention(
        'labels.create', 'default',
        'create', 'labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.create_command',
    ),
    GeneratedConvention(
        'labels.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.delete_command',
    ),
    GeneratedConvention(
        'labels.get', 'default',
        'retrieve', 'labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.get_command',
    ),
    GeneratedConvention(
        'labels.list', 'default',
        'collection', 'page_labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.list_command',
    ),
    GeneratedConvention(
        'labels.update', 'default',
        'update', 'labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.labels.LabelResource.update_command',
    ),
    GeneratedConvention(
        'maintenance.update', 'default',
        'process', 'process',
        None,
        None, 'direct',
        (), 'multica_py.resources.maintenance.MaintenanceResource.update_command',
    ),
    GeneratedConvention(
        'maintenance.version', 'default',
        'scalar', 'scalar_str',
        None,
        None, 'direct',
        (), 'multica_py.resources.maintenance.MaintenanceResource.version_command',
    ),
    GeneratedConvention(
        'projects.create', 'default',
        'create', 'project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.create_command',
    ),
    GeneratedConvention(
        'projects.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.delete_command',
    ),
    GeneratedConvention(
        'projects.get', 'default',
        'retrieve', 'project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.get_command',
    ),
    GeneratedConvention(
        'projects.issues.create', 'default',
        'create', 'issue',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectIssueCollection.create_command',
    ),
    GeneratedConvention(
        'projects.list', 'default',
        'collection', 'page_project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.list_command',
    ),
    GeneratedConvention(
        'projects.refresh', 'default',
        'action', 'project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.Project.refresh_command',
    ),
    GeneratedConvention(
        'projects.resources.add_local_directory', 'default',
        'retrieve', 'project_resource',
        None,
        None, 'direct',
        (), 'multica_py.resources.project_resources.ProjectResourceCollection.add_local_directory_command',
    ),
    GeneratedConvention(
        'projects.resources.list', 'default',
        'collection', 'page_project_resources',
        None,
        None, 'direct',
        (), 'multica_py.resources.project_resources.ProjectResourceCollection.list_command',
    ),
    GeneratedConvention(
        'projects.resources.remove', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.project_resources.ProjectResourceCollection.remove_command',
    ),
    GeneratedConvention(
        'projects.resources.update_local_directory', 'default',
        'retrieve', 'project_resource',
        None,
        None, 'direct',
        (), 'multica_py.resources.project_resources.ProjectResourceCollection.update_local_directory_command',
    ),
    GeneratedConvention(
        'projects.set_status', 'default',
        'update', 'project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.set_status_command',
    ),
    GeneratedConvention(
        'projects.update', 'default',
        'update', 'project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.ProjectResource.update_command',
    ),
    GeneratedConvention(
        'projects.update_bound', 'default',
        'action', 'project',
        None,
        None, 'direct',
        (), 'multica_py.resources.projects.Project.update_command',
    ),
    GeneratedConvention(
        'properties.archive', 'default',
        'action', 'property_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.properties.PropertyResource.archive_command',
    ),
    GeneratedConvention(
        'properties.create', 'default',
        'create', 'property_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.properties.PropertyResource.create_command',
    ),
    GeneratedConvention(
        'properties.get', 'default',
        'retrieve', 'property_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.properties.PropertyResource.get_command',
    ),
    GeneratedConvention(
        'properties.list', 'default',
        'collection', 'page_property_definitions',
        None,
        None, 'direct',
        (), 'multica_py.resources.properties.PropertyResource.list_command',
    ),
    GeneratedConvention(
        'properties.unarchive', 'default',
        'action', 'property_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.properties.PropertyResource.unarchive_command',
    ),
    GeneratedConvention(
        'properties.update', 'default',
        'update', 'property_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.properties.PropertyResource.update_command',
    ),
    GeneratedConvention(
        'repositories.add', 'default',
        'action', 'action_result_repository_mutation_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.add_command',
    ),
    GeneratedConvention(
        'repositories.checkout', 'default',
        'process', 'repository_checkout',
        None,
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.checkout_command',
    ),
    GeneratedConvention(
        'repositories.list', 'default',
        'collection', 'page_repository_records',
        None,
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.list_command',
    ),
    GeneratedConvention(
        'repositories.remove', 'default',
        'action', 'action_result_repository_mutation_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.repositories.RepositoryResource.remove_command',
    ),
    GeneratedConvention(
        'runtime_profiles.create', 'default',
        'create', 'runtime_profile_create',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtime_profiles.RuntimeProfileResource.create_command',
    ),
    GeneratedConvention(
        'runtime_profiles.delete', 'default',
        'action', 'runtime_profile_delete',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtime_profiles.RuntimeProfileResource.delete_command',
    ),
    GeneratedConvention(
        'runtime_profiles.list', 'default',
        'collection', 'runtime_profile_list',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtime_profiles.RuntimeProfileResource.list_command',
    ),
    GeneratedConvention(
        'runtime_profiles.set_path', 'default',
        'action', 'runtime_profile_set_path',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtime_profiles.RuntimeProfileResource.set_path_command',
    ),
    GeneratedConvention(
        'runtime_profiles.unset_path', 'default',
        'action', 'runtime_profile_unset_path',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtime_profiles.RuntimeProfileResource.unset_path_command',
    ),
    GeneratedConvention(
        'runtime_profiles.update', 'default',
        'update', 'runtime_profile_update',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtime_profiles.RuntimeProfileResource.update_command',
    ),
    GeneratedConvention(
        'runtimes.activity', 'default',
        'collection', 'page_runtime_activity',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.activity_command',
    ),
    GeneratedConvention(
        'runtimes.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.delete_command',
    ),
    GeneratedConvention(
        'runtimes.list', 'default',
        'collection', 'page_runtime_definitions',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.list_command',
    ),
    GeneratedConvention(
        'runtimes.rename', 'default',
        'update', 'runtime_definition',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.rename_command',
    ),
    GeneratedConvention(
        'runtimes.update', 'default',
        'action', 'action_result_runtime_update_result',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.update_command',
    ),
    GeneratedConvention(
        'runtimes.usage', 'default',
        'collection', 'page_runtime_usage',
        None,
        None, 'direct',
        (), 'multica_py.resources.runtimes.RuntimeResource.usage_command',
    ),
    GeneratedConvention(
        'setup.cloud', 'default',
        'process', 'process',
        None,
        None, 'direct',
        (), 'multica_py.resources.setup.SetupResource.cloud_command',
    ),
    GeneratedConvention(
        'setup.self_host', 'default',
        'process', 'process',
        None,
        None, 'direct',
        (), 'multica_py.resources.setup.SetupResource.self_host_command',
    ),
    GeneratedConvention(
        'skills.create', 'default',
        'create', 'skill',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.create_command',
    ),
    GeneratedConvention(
        'skills.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.delete_command',
    ),
    GeneratedConvention(
        'skills.files.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.skill_files.SkillFileResource.delete_command',
    ),
    GeneratedConvention(
        'skills.files.list', 'default',
        'collection', 'page_skill_files',
        None,
        None, 'direct',
        (), 'multica_py.resources.skill_files.SkillFileResource.list_command',
    ),
    GeneratedConvention(
        'skills.files.upsert', 'default',
        'retrieve', 'skill_file',
        None,
        None, 'direct',
        (), 'multica_py.resources.skill_files.SkillFileResource.upsert_command',
    ),
    GeneratedConvention(
        'skills.get', 'default',
        'retrieve', 'skill',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.get_command',
    ),
    GeneratedConvention(
        'skills.import_from_url', 'default',
        'create', 'skill',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.import_from_url_command',
    ),
    GeneratedConvention(
        'skills.labels.add', 'default',
        'collection', 'page_labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.skill_labels.SkillLabelResource.add_command',
    ),
    GeneratedConvention(
        'skills.labels.list', 'default',
        'collection', 'page_labels',
        None,
        None, 'direct',
        (), 'multica_py.resources.skill_labels.SkillLabelResource.list_command',
    ),
    GeneratedConvention(
        'skills.labels.remove', 'default',
        'collection', 'page_labels',
        'action_result_none',
        None, 'direct',
        (), 'multica_py.resources.skill_labels.SkillLabelResource.remove_command',
    ),
    GeneratedConvention(
        'skills.list', 'default',
        'collection', 'page_skill',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.list_command',
    ),
    GeneratedConvention(
        'skills.refresh', 'default',
        'action', 'skill',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.refresh_command',
    ),
    GeneratedConvention(
        'skills.search', 'default',
        'collection', 'page_skill_search_results',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.search_command',
    ),
    GeneratedConvention(
        'skills.update', 'default',
        'update', 'skill',
        None,
        None, 'direct',
        (), 'multica_py.resources.skills.SkillResource.update_command',
    ),
    GeneratedConvention(
        'squads.activity', 'default',
        'action', 'mapping_config',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.activity_command',
    ),
    GeneratedConvention(
        'squads.create', 'default',
        'create', 'squad',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.create_command',
    ),
    GeneratedConvention(
        'squads.delete', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.delete_command',
    ),
    GeneratedConvention(
        'squads.get', 'default',
        'retrieve', 'squad',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.get_command',
    ),
    GeneratedConvention(
        'squads.list', 'default',
        'collection', 'page_squad',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.list_command',
    ),
    GeneratedConvention(
        'squads.members.add', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.squad_members.SquadMemberResource.add_command',
    ),
    GeneratedConvention(
        'squads.members.list', 'default',
        'collection', 'page_squad_members',
        None,
        None, 'direct',
        (), 'multica_py.resources.squad_members.SquadMemberResource.list_command',
    ),
    GeneratedConvention(
        'squads.members.remove', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.squad_members.SquadMemberResource.remove_command',
    ),
    GeneratedConvention(
        'squads.members.set_role', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.member_set_role_command',
    ),
    GeneratedConvention(
        'squads.update', 'default',
        'update', 'squad',
        None,
        None, 'direct',
        (), 'multica_py.resources.squads.SquadResource.update_command',
    ),
    GeneratedConvention(
        'users.profile_get', 'default',
        'retrieve', 'user_profile',
        None,
        None, 'direct',
        (), 'multica_py.resources.users.UserResource.profile_get_command',
    ),
    GeneratedConvention(
        'users.profile_update', 'default',
        'update', 'user_profile',
        None,
        None, 'direct',
        (), 'multica_py.resources.users.UserResource.profile_update_command',
    ),
    GeneratedConvention(
        'workspaces.create', 'default',
        'create', 'workspace',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.create_command',
    ),
    GeneratedConvention(
        'workspaces.get', 'default',
        'retrieve', 'workspace',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.get_command',
    ),
    GeneratedConvention(
        'workspaces.list', 'default',
        'collection', 'page_workspace',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.list_command',
    ),
    GeneratedConvention(
        'workspaces.mcp.add', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.add_command',
    ),
    GeneratedConvention(
        'workspaces.mcp.list', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.list_command',
    ),
    GeneratedConvention(
        'workspaces.mcp.remove', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.remove_command',
    ),
    GeneratedConvention(
        'workspaces.mcp.update', 'default',
        'collection', 'page_mcp_servers',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspace_mcp.WorkspaceMcpResource.update_command',
    ),
    GeneratedConvention(
        'workspaces.members.invite', 'default',
        'create', 'workspace_members',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.member_invite_command',
    ),
    GeneratedConvention(
        'workspaces.members.list', 'default',
        'collection', 'page_workspace_members',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.members_command',
    ),
    GeneratedConvention(
        'workspaces.switch', 'default',
        'action', 'action_result_none',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.switch_command',
    ),
    GeneratedConvention(
        'workspaces.update', 'default',
        'update', 'workspace',
        None,
        None, 'direct',
        (), 'multica_py.resources.workspaces.WorkspaceResource.update_command',
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

def validate_positive_expected_revision(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError('value must be a positive integer')

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

def validate_since_cursor(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 2147483647:
        raise ValueError('value must be a nonnegative int32 sequence cursor')

def validate_thread_cursor_limit(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError('value must be a positive integer')

__all__ = ('AGENTS_ARCHIVE_MANUAL_BINDING', 'AGENTS_CREATE_MANUAL_BINDING', 'AGENTS_ENV_GET_BINDING', 'AGENTS_ENV_SET_BINDING', 'AGENTS_RESTORE_MANUAL_BINDING', 'AGENTS_SKILLS_ADD_BINDING', 'AGENTS_UPDATE_MANUAL_BINDING', 'AGENT_AVATAR_BINDING', 'AGENT_COPY_BINDING', 'AGENT_GET_BINDING', 'AGENT_LIST_BINDING', 'AGENT_MCP_ADD_BINDING', 'AGENT_MCP_ADD_BOUND_BINDING', 'AGENT_MCP_DISABLE_BINDING', 'AGENT_MCP_DISABLE_BOUND_BINDING', 'AGENT_MCP_ENABLE_BINDING', 'AGENT_MCP_ENABLE_BOUND_BINDING', 'AGENT_MCP_LIST_BINDING', 'AGENT_MCP_REMOVE_BINDING', 'AGENT_MCP_REMOVE_BOUND_BINDING', 'AGENT_SKILLS_LIST_BINDING', 'AGENT_SKILLS_SET_BINDING', 'AGENT_TASKS_BINDING', 'ATTACHMENTS_DOWNLOAD_BYTES_MANUAL_BINDING', 'ATTACHMENTS_UPLOAD_BYTES_MANUAL_BINDING', 'ATTACHMENT_DOWNLOAD_BINDING', 'ATTACHMENT_UPLOAD_BINDING', 'AUTH_LOGIN_MANUAL_BINDING', 'AUTH_LOGOUT_MANUAL_BINDING', 'AUTH_STATUS_MANUAL_BINDING', 'AUTOPILOTS_TRIGGER_LIST_BINDING', 'AUTOPILOT_CREATE_BINDING', 'AUTOPILOT_DELETE_BINDING', 'AUTOPILOT_GET_BINDING', 'AUTOPILOT_HISTORY_BINDING', 'AUTOPILOT_LIST_BINDING', 'AUTOPILOT_TRIGGER_ADD_BINDING', 'AUTOPILOT_TRIGGER_BINDING', 'AUTOPILOT_TRIGGER_DELETE_BINDING', 'AUTOPILOT_TRIGGER_ROTATE_URL_BINDING', 'AUTOPILOT_TRIGGER_UPDATE_BINDING', 'AUTOPILOT_UPDATE_BINDING', 'CHAT_HISTORY_BINDING', 'CHAT_THREAD_BINDING', 'CLI_COMMAND_BINDING', 'COMMENT_ADD_BINDING', 'COMMENT_DELETE_BINDING', 'COMMENT_LIST_BINDING', 'COMMENT_LIST_FLAT_BINDING', 'COMMENT_LIST_RECENT_BINDING', 'COMMENT_LIST_THREAD_BINDING', 'COMMENT_UPDATE_BINDING', 'CONFIGURATION_GET_MANUAL_BINDING', 'CONFIGURATION_SET_MANUAL_BINDING', 'CONFIGURATION_SHOW_MANUAL_BINDING', 'DAEMON_DISK_USAGE_MANUAL_BINDING', 'DAEMON_LOGS_MANUAL_BINDING', 'DAEMON_RESTART_MANUAL_BINDING', 'DAEMON_START_MANUAL_BINDING', 'DAEMON_STATUS_MANUAL_BINDING', 'DAEMON_STOP_MANUAL_BINDING', 'ISSUES_ASSIGN_BOUND_BINDING', 'ISSUES_ASSIGN_MANUAL_BINDING', 'ISSUES_COMMENTS_REPLY_MANUAL_BINDING', 'ISSUES_COMMENTS_RESOLVE_MANUAL_BINDING', 'ISSUES_COMMENTS_UNRESOLVE_MANUAL_BINDING', 'ISSUES_METADATA_QUERY_MANUAL_BINDING', 'ISSUES_METADATA_SET_TYPED_MANUAL_BINDING', 'ISSUES_MOVE_AFTER_BINDING', 'ISSUES_MOVE_AFTER_BOUND_BINDING', 'ISSUES_MOVE_BEFORE_BINDING', 'ISSUES_MOVE_BEFORE_BOUND_BINDING', 'ISSUES_MOVE_TO_BOTTOM_BINDING', 'ISSUES_MOVE_TO_BOTTOM_BOUND_BINDING', 'ISSUES_MOVE_TO_TOP_BINDING', 'ISSUES_MOVE_TO_TOP_BOUND_BINDING', 'ISSUES_REFRESH_BINDING', 'ISSUES_REORDER_MANUAL_BINDING', 'ISSUES_SET_STATUS_BOUND_BINDING', 'ISSUES_UNASSIGN_BINDING', 'ISSUES_UNASSIGN_BOUND_BINDING', 'ISSUES_UPDATE_BOUND_BINDING', 'ISSUES_UPDATE_MANUAL_BINDING', 'ISSUES_USAGE_MANUAL_BINDING', 'ISSUE_CANCEL_TASK_BINDING', 'ISSUE_CHILDREN_BINDING', 'ISSUE_CREATE_BINDING', 'ISSUE_GET_BINDING', 'ISSUE_LABELS_ADD_BINDING', 'ISSUE_LABELS_LIST_BINDING', 'ISSUE_LABELS_REMOVE_BINDING', 'ISSUE_LIST_BINDING', 'ISSUE_METADATA_DELETE_BINDING', 'ISSUE_METADATA_GET_BINDING', 'ISSUE_METADATA_LIST_BINDING', 'ISSUE_METADATA_SET_BINDING', 'ISSUE_PROPERTY_LIST_BINDING', 'ISSUE_PROPERTY_SET_BINDING', 'ISSUE_PROPERTY_UNSET_BINDING', 'ISSUE_PULL_REQUESTS_BINDING', 'ISSUE_RERUN_BINDING', 'ISSUE_RUNS_BINDING', 'ISSUE_RUN_MESSAGES_BINDING', 'ISSUE_SEARCH_BINDING', 'ISSUE_STATUS_BINDING', 'ISSUE_SUBSCRIBERS_ADD_BINDING', 'ISSUE_SUBSCRIBERS_LIST_BINDING', 'ISSUE_SUBSCRIBERS_REMOVE_BINDING', 'ISSUE_TIMELINE_BINDING', 'ISSUE_WAKEUP_CREATE_BINDING', 'ISSUE_WAKEUP_DISABLE_BINDING', 'ISSUE_WAKEUP_EVENTS_BINDING', 'ISSUE_WAKEUP_GET_BINDING', 'ISSUE_WAKEUP_LIST_BINDING', 'ISSUE_WAKEUP_UPDATE_BINDING', 'LABELS_CREATE_MANUAL_BINDING', 'LABELS_DELETE_MANUAL_BINDING', 'LABELS_UPDATE_MANUAL_BINDING', 'LABEL_GET_BINDING', 'LABEL_LIST_BINDING', 'MAINTENANCE_UPDATE_MANUAL_BINDING', 'MAINTENANCE_VERSION_MANUAL_BINDING', 'MAX_CLI_VERSION', 'MIN_CLI_VERSION', 'OPERATION_BINDINGS', 'OPERATION_CONVENTIONS', 'PROJECTS_DELETE_MANUAL_BINDING', 'PROJECTS_REFRESH_BINDING', 'PROJECTS_UPDATE_BOUND_BINDING', 'PROJECT_CREATE_BINDING', 'PROJECT_GET_BINDING', 'PROJECT_ISSUE_CREATE_BINDING', 'PROJECT_LIST_BINDING', 'PROJECT_RESOURCE_ADD_BINDING', 'PROJECT_RESOURCE_LIST_BINDING', 'PROJECT_RESOURCE_REMOVE_BINDING', 'PROJECT_RESOURCE_UPDATE_BINDING', 'PROJECT_STATUS_BINDING', 'PROJECT_UPDATE_BINDING', 'PROPERTY_ARCHIVE_BINDING', 'PROPERTY_CREATE_BINDING', 'PROPERTY_GET_BINDING', 'PROPERTY_LIST_BINDING', 'PROPERTY_UNARCHIVE_BINDING', 'PROPERTY_UPDATE_BINDING', 'PUBLIC_INVENTORY', 'REPOSITORIES_ADD_BINDING', 'REPOSITORIES_LIST_BINDING', 'REPOSITORIES_REMOVE_BINDING', 'REPOSITORY_CHECKOUT_BINDING', 'RUNTIME_ACTIVITY_BINDING', 'RUNTIME_DELETE_BINDING', 'RUNTIME_LIST_BINDING', 'RUNTIME_PROFILE_CREATE_BINDING', 'RUNTIME_PROFILE_DELETE_BINDING', 'RUNTIME_PROFILE_LIST_BINDING', 'RUNTIME_PROFILE_SET_PATH_BINDING', 'RUNTIME_PROFILE_UNSET_PATH_BINDING', 'RUNTIME_PROFILE_UPDATE_BINDING', 'RUNTIME_RENAME_BINDING', 'RUNTIME_UPDATE_BINDING', 'RUNTIME_USAGE_BINDING', 'SETUP_CLOUD_MANUAL_BINDING', 'SETUP_SELF_HOST_MANUAL_BINDING', 'SKILLS_CREATE_MANUAL_BINDING', 'SKILLS_DELETE_MANUAL_BINDING', 'SKILLS_IMPORT_FROM_URL_MANUAL_BINDING', 'SKILLS_UPDATE_MANUAL_BINDING', 'SKILL_FILES_DELETE_BINDING', 'SKILL_FILES_LIST_BINDING', 'SKILL_FILES_UPSERT_BINDING', 'SKILL_GET_BINDING', 'SKILL_LABELS_ADD_BINDING', 'SKILL_LABELS_LIST_BINDING', 'SKILL_LABELS_REMOVE_BINDING', 'SKILL_LIST_BINDING', 'SKILL_REFRESH_BINDING', 'SKILL_SEARCH_BINDING', 'SQUADS_ACTIVITY_BINDING', 'SQUADS_CREATE_BINDING', 'SQUADS_DELETE_BINDING', 'SQUADS_MEMBERS_SET_ROLE_BINDING', 'SQUADS_UPDATE_BINDING', 'SQUAD_GET_BINDING', 'SQUAD_LIST_BINDING', 'SQUAD_MEMBERS_ADD_BINDING', 'SQUAD_MEMBERS_LIST_BINDING', 'SQUAD_MEMBERS_REMOVE_BINDING', 'TARGET_VERSION', 'USER_PROFILE_GET_BINDING', 'USER_PROFILE_UPDATE_BINDING', 'WORKSPACES_CREATE_BINDING', 'WORKSPACES_MEMBERS_INVITE_BINDING', 'WORKSPACES_SWITCH_MANUAL_BINDING', 'WORKSPACES_UPDATE_BINDING', 'WORKSPACE_GET_BINDING', 'WORKSPACE_LIST_BINDING', 'WORKSPACE_MCP_ADD_BINDING', 'WORKSPACE_MCP_LIST_BINDING', 'WORKSPACE_MCP_REMOVE_BINDING', 'WORKSPACE_MCP_UPDATE_BINDING', 'WORKSPACE_MEMBERS_LIST_BINDING', 'AutopilotExecutionMode', 'GeneratedBinding', 'GeneratedConvention', 'GeneratedInventoryItem', 'GeneratedMapping', 'IssueSort', 'LabelResourceType', 'SortDirection', 'normalize_optional_label', 'validate_comment_cursor', 'validate_description_input', 'validate_issue_sort', 'validate_issue_status', 'validate_nonblank', 'validate_nonnegative_limit', 'validate_positive_expected_revision', 'validate_positive_limit', 'validate_positive_max_concurrent_tasks', 'validate_project_description', 'validate_project_status', 'validate_project_update', 'validate_resource_update', 'validate_since_cursor', 'validate_thread_cursor_limit')

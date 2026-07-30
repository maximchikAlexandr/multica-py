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

AUTOPILOT_RUN_BINDING = GeneratedBinding(
    'autopilots.run', 'default', ('autopilot', 'run'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'),), ('nonblank:autopilot_id',),
)

AUTOPILOT_UPDATE_BINDING = GeneratedBinding(
    'autopilots.update', 'default', ('autopilot', 'update'),
    (GeneratedMapping('autopilot_id', 'pos:0', 'path:autopilot_id'), GeneratedMapping('title', '--title', 'json_body:title'), GeneratedMapping('description', '--description', 'json_body:description'), GeneratedMapping('agent', '--agent', 'json_body:assignee_id'), GeneratedMapping('project_id', '--project', 'json_body:project_id'), GeneratedMapping('priority', '--priority', 'json_body:priority'), GeneratedMapping('status', '--status', 'json_body:status'), GeneratedMapping('execution_mode', '--mode', 'json_body:execution_mode'), GeneratedMapping('issue_title_template', '--issue-title-template', 'json_body:issue_title_template'), GeneratedMapping('subscribers', 'repeat:--subscriber', 'json_body:subscribers'), GeneratedMapping('clear_subscribers', '--clear-subscribers', 'json_body:clear_subscribers'),), ('nonblank:autopilot_id',),
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
    (GeneratedMapping('filter.status', '--status', 'query:status'), GeneratedMapping('filter.priority', '--priority', 'query:priority'), GeneratedMapping('filter.assignee_id', '--assignee-id', 'query:assignee_id'), GeneratedMapping('filter.limit', '--limit', 'query:limit'), GeneratedMapping('filter.sort', '--sort', 'query:sort'), GeneratedMapping('filter.direction', '--direction', 'query:direction'),), ('direction_requires_sort', 'position_forbids_direction'),
)

ISSUE_STATUS_BINDING = GeneratedBinding(
    'issues.set_status', 'default', ('issue', 'status'),
    (GeneratedMapping('issue_id', 'pos:0', 'path:issue_id'), GeneratedMapping('status', 'pos:1', 'json_body:status'),), ('strict:IssueStatus',),
)

PROJECT_CREATE_BINDING = GeneratedBinding(
    'projects.create', 'default', ('project', 'create'),
    (GeneratedMapping('request.name', '--title', 'json_body:title'), GeneratedMapping('request.description', '--description', 'json_body:description'),), ('nonblank:request.name',),
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

OPERATION_BINDINGS: tuple[GeneratedBinding, ...] = (
    AUTOPILOT_CREATE_BINDING,
    AUTOPILOT_DELETE_BINDING,
    AUTOPILOT_GET_BINDING,
    AUTOPILOT_HISTORY_BINDING,
    AUTOPILOT_LIST_BINDING,
    AUTOPILOT_RUN_BINDING,
    AUTOPILOT_UPDATE_BINDING,
    COMMENT_ADD_BINDING,
    COMMENT_DELETE_BINDING,
    COMMENT_LIST_BINDING,
    COMMENT_LIST_FLAT_BINDING,
    COMMENT_LIST_RECENT_BINDING,
    COMMENT_LIST_THREAD_BINDING,
    ISSUE_CREATE_BINDING,
    ISSUE_LABELS_ADD_BINDING,
    ISSUE_LABELS_LIST_BINDING,
    ISSUE_LABELS_REMOVE_BINDING,
    ISSUE_LIST_BINDING,
    ISSUE_STATUS_BINDING,
    PROJECT_CREATE_BINDING,
    PROJECT_RESOURCE_ADD_BINDING,
    PROJECT_RESOURCE_LIST_BINDING,
    PROJECT_RESOURCE_REMOVE_BINDING,
    PROJECT_RESOURCE_UPDATE_BINDING,
    PROJECT_STATUS_BINDING,
    PROJECT_UPDATE_BINDING,
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

__all__ = ('TARGET_VERSION', 'MIN_CLI_VERSION', 'MAX_CLI_VERSION', 'AutopilotExecutionMode', 'IssueSort', 'SortDirection', 'GeneratedMapping', 'GeneratedBinding', 'AUTOPILOT_CREATE_BINDING', 'AUTOPILOT_DELETE_BINDING', 'AUTOPILOT_GET_BINDING', 'AUTOPILOT_HISTORY_BINDING', 'AUTOPILOT_LIST_BINDING', 'AUTOPILOT_RUN_BINDING', 'AUTOPILOT_UPDATE_BINDING', 'COMMENT_ADD_BINDING', 'COMMENT_DELETE_BINDING', 'COMMENT_LIST_BINDING', 'COMMENT_LIST_FLAT_BINDING', 'COMMENT_LIST_RECENT_BINDING', 'COMMENT_LIST_THREAD_BINDING', 'ISSUE_CREATE_BINDING', 'ISSUE_LABELS_ADD_BINDING', 'ISSUE_LABELS_LIST_BINDING', 'ISSUE_LABELS_REMOVE_BINDING', 'ISSUE_LIST_BINDING', 'ISSUE_STATUS_BINDING', 'PROJECT_CREATE_BINDING', 'PROJECT_RESOURCE_ADD_BINDING', 'PROJECT_RESOURCE_LIST_BINDING', 'PROJECT_RESOURCE_REMOVE_BINDING', 'PROJECT_RESOURCE_UPDATE_BINDING', 'PROJECT_STATUS_BINDING', 'PROJECT_UPDATE_BINDING', 'OPERATION_BINDINGS', 'normalize_optional_label', 'validate_comment_cursor', 'validate_description_input', 'validate_issue_sort', 'validate_issue_status', 'validate_nonblank', 'validate_nonnegative_limit', 'validate_positive_limit', 'validate_project_description', 'validate_project_status', 'validate_project_update', 'validate_resource_update', 'validate_thread_cursor_limit')

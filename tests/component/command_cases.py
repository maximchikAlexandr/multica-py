from __future__ import annotations

import pathlib

from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.models.agents import AgentCreateRequest, AgentUpdateRequest
from multica_py.models.issues import (
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueReorderRequest,
    IssueUpdateRequest,
)
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.skills import SkillCreateRequest, SkillUpdateRequest
from multica_py.models.system import AttachmentResult
from tests.component.resource_payloads import *  # noqa: F403
from tests.component.resource_support import CommandCase

# ruff: noqa: F405

_PR_LOCAL_DIR = str(pathlib.Path("/tmp/sandbox").resolve())
_TMP_AVATAR = str(pathlib.Path("/tmp/avatar.png").resolve())
_TMP_FILE = str(pathlib.Path("/tmp/file.txt").resolve())
_TMP_OUT = str(pathlib.Path("/tmp/out.txt").resolve())

# fmt: off
SUCCESS_COMMAND_CASES: tuple[CommandCase, ...] = (
    CommandCase(id='agents.list', sdk_method='agents.list', invoke=lambda c: c.agents.list(), expected_argv=('agent', 'list', '--output', 'json'), stdout=P_ID_AG_001_NAME_HELPER_SKILLS, check='nonempty'),
    CommandCase(id='agents.archive', sdk_method='agents.archive', invoke=lambda c: c.agents.archive("ag_001"), expected_argv=('agent', 'archive', 'ag_001'), check='none'),
    CommandCase(id='agents.create', sdk_method='agents.create', invoke=lambda c: c.agents.create(AgentCreateRequest(name="Helper")), expected_argv=('agent', 'create', '--name', 'Helper', '--output', 'json'), stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2),
    CommandCase(id='agents.get', sdk_method='agents.get', invoke=lambda c: c.agents.get("ag_001"), expected_argv=('agent', 'get', 'ag_001', '--output', 'json'), stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2),
    CommandCase(id='agents.restore', sdk_method='agents.restore', invoke=lambda c: c.agents.restore("ag_001"), expected_argv=('agent', 'restore', 'ag_001'), check='none'),
    CommandCase(id='agents.skills.list', sdk_method='agents.skills.list', invoke=lambda c: c.agents.skills.list("ag_001"), expected_argv=('agent', 'skill', 'list', 'ag_001', '--output', 'json'), stdout=P_ID_SK_001_NAME_SKILL, check='nonempty'),
    CommandCase(id='agents.skills.set', sdk_method='agents.skills.set', invoke=lambda c: c.agents.skills.set("ag_001", ("sk_001",)), expected_argv=('agent', 'skill', 'set', 'ag_001', '--skill-id', 'sk_001'), check='none'),
    CommandCase(id='agents.tasks', sdk_method='agents.tasks', invoke=lambda c: c.agents.tasks("ag_001"), expected_argv=('agent', 'tasks', 'ag_001', '--output', 'json'), stdout=P_ID_TASK_001_STATUS_DONE_ISSUE, check='nonempty'),
    CommandCase(id='agents.update', sdk_method='agents.update', invoke=lambda c: c.agents.update("ag_001", AgentUpdateRequest(name="Helper")), expected_argv=('agent', 'update', 'ag_001', '--name', 'Helper', '--output', 'json'), stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2),
    CommandCase(id='agents.upload_avatar', sdk_method='agents.upload_avatar', invoke=lambda c: c.agents.upload_avatar("ag_001", "/tmp/avatar.png"), expected_argv=('agent', 'avatar', 'upload', 'ag_001', '--image', _TMP_AVATAR), check='none'),
    CommandCase(id='attachments.list.all', sdk_method='attachments.list', invoke=lambda c: c.attachments._run_json_decode_list(("attachment", "list"), AttachmentResult), expected_argv=('attachment', 'list', '--output', 'json'), stdout=P_ID_AT_001_FILENAME_FILE_TXT_U, check='nonempty'),
    CommandCase(id='attachments.list.iss_001', sdk_method='attachments.list', invoke=lambda c: c.attachments.list("iss_001"), expected_argv=('attachment', 'list', 'iss_001', '--output', 'json'), stdout=P_ID_AT_001_FILENAME_FILE_TXT_U, check='nonempty'),
    CommandCase(id='attachments.upload', sdk_method='attachments.upload', invoke=lambda c: c.attachments.upload("iss_001", "/tmp/file.txt"), expected_argv=('attachment', 'upload', 'iss_001', '--file', _TMP_FILE, '--output', 'json'), stdout=P_ID_ATT_001_FILENAME_FILE_TXT),
    CommandCase(id='attachments.download', sdk_method='attachments.download', invoke=lambda c: c.attachments.download("att_001", "/tmp/out.txt"), expected_argv=('attachment', 'download', 'att_001', '--output', _TMP_OUT), check='none'),
    CommandCase(id='auth.login', sdk_method='auth.login', invoke=lambda c: c.auth.login("secret-token"), expected_argv=('auth', 'login', '--token', 'secret-token'), stdout=P_LOGIN_SUCCESSFUL, check='auth_login'),
    CommandCase(id='auth.status', sdk_method='auth.status', invoke=lambda c: c.auth.status(), expected_argv=('auth', 'status', '--output', 'json'), stdout=P_AUTHENTICATED_TRUE_USER_ID_USR, check='auth_status'),
    CommandCase(id='auth.logout', sdk_method='auth.logout', invoke=lambda c: c.auth.logout(), expected_argv=('auth', 'logout', '--output', 'json'), stdout=P_AUTHENTICATED_FALSE_USER_ID_NU, check='auth_logout'),
    CommandCase(id='autopilots.list', sdk_method='autopilots.list', invoke=lambda c: c.autopilots.list(), expected_argv=('autopilot', 'list', '--output', 'json'), stdout=P_AUTOPILOTS_ID_AP_001_NAME_NI, check='nonempty'),
    CommandCase(id='autopilots.create', sdk_method='autopilots.create', invoke=lambda c: c.autopilots.create("AP"), expected_argv=('autopilot', 'create', '--name', 'AP', '--output', 'json'), stdout=P_ID_AP_001_NAME_AP_ENABLED_FAL),
    CommandCase(id='autopilots.get', sdk_method='autopilots.get', invoke=lambda c: c.autopilots.get("ap_001"), expected_argv=('autopilot', 'get', 'ap_001', '--output', 'json'), stdout=P_ID_AP_001_NAME_AP_ENABLED_FAL),
    CommandCase(id='autopilots.update', sdk_method='autopilots.update', invoke=lambda c: c.autopilots.update("ap_001", name="Renamed"), expected_argv=('autopilot', 'update', 'ap_001', '--name', 'Renamed', '--output', 'json'), stdout=P_ID_AP_001_NAME_AP_ENABLED_FAL),
    CommandCase(id='autopilots.delete', sdk_method='autopilots.delete', invoke=lambda c: c.autopilots.delete("ap_001"), expected_argv=('autopilot', 'delete', 'ap_001'), check='none'),
    CommandCase(id='autopilots.run', sdk_method='autopilots.run', invoke=lambda c: c.autopilots.run("ap_001"), expected_argv=('autopilot', 'run', 'ap_001', '--output', 'json'), stdout=P_ID_RUN_001_STATUS_COMPLETED),
    CommandCase(id='autopilots.history', sdk_method='autopilots.history', invoke=lambda c: c.autopilots.history("ap_001"), expected_argv=('autopilot', 'history', 'ap_001', '--output', 'json'), stdout=P_ID_RUN_001_STATUS_COMPLETED_2, check='nonempty'),
    CommandCase(id='autopilots.get_run', sdk_method='autopilots.get_run', invoke=lambda c: c.autopilots.get_run("run_001"), expected_argv=('autopilot', 'run', 'get', 'run_001', '--output', 'json'), stdout=P_ID_RUN_001_STATUS_COMPLETED),
    CommandCase(id='autopilots.triggers.list', sdk_method='autopilots.triggers.list', invoke=lambda c: c.autopilots.triggers.list("ap_001"), expected_argv=('autopilot', 'trigger', 'list', 'ap_001', '--output', 'json'), stdout=P_ID_TR_001_TYPE_WEBHOOK_CONFIG, check='nonempty'),
    CommandCase(id='autopilots.triggers.create', sdk_method='autopilots.triggers.create', invoke=lambda c: c.autopilots.triggers.create("ap_001", "webhook"), expected_argv=('autopilot', 'trigger', 'create', 'ap_001', '--type', 'webhook', '--output', 'json'), stdout=P_ID_TR_001_TYPE_WEBHOOK_CONFIG_2),
    CommandCase(id='autopilots.triggers.delete', sdk_method='autopilots.triggers.delete', invoke=lambda c: c.autopilots.triggers.delete("ap_001", "tr_001"), expected_argv=('autopilot', 'trigger', 'delete', 'ap_001', '--trigger-id', 'tr_001'), check='none'),
    CommandCase(id='configuration.show', sdk_method='configuration.show', invoke=lambda c: c.configuration.show(), expected_argv=('config', 'show'), stdout=P_WORKSPACE_WS_001_PROFILE_DEFAU),
    CommandCase(id='configuration.get', sdk_method='configuration.get', invoke=lambda c: c.configuration.get("key"), expected_argv=('config', 'get', 'key'), stdout=P_VALUE),
    CommandCase(id='configuration.set', sdk_method='configuration.set', invoke=lambda c: c.configuration.set("key", "val"), expected_argv=('config', 'set', 'key', 'val'), check='none'),
    CommandCase(id='daemon.status', sdk_method='daemon.status', invoke=lambda c: c.daemon.status(), expected_argv=('daemon', 'status', '--output', 'json'), stdout=P_RUNNING_TRUE_PID_12345_UPTIME_, check='daemon_status'),
    CommandCase(id='daemon.disk_usage', sdk_method='daemon.disk_usage', invoke=lambda c: c.daemon.disk_usage(), expected_argv=('daemon', 'disk-usage', '--output', 'json'), stdout=P_PATH_TMP_SIZE_BYTES_1024, check='nonempty'),
    CommandCase(id='daemon.start', sdk_method='daemon.start', invoke=lambda c: c.daemon.start(), expected_argv=('daemon', 'start')),
    CommandCase(id='daemon.stop', sdk_method='daemon.stop', invoke=lambda c: c.daemon.stop(), expected_argv=('daemon', 'stop', '--output', 'json'), stdout=P_RUNNING_FALSE),
    CommandCase(id='daemon.restart', sdk_method='daemon.restart', invoke=lambda c: c.daemon.restart(), expected_argv=('daemon', 'restart', '--output', 'json'), stdout=P_RUNNING_TRUE_PID_12345_UPTIME_),
    CommandCase(id='daemon.logs', sdk_method='daemon.logs', invoke=lambda c: c.daemon.logs(), expected_argv=('daemon', 'logs')),
    CommandCase(id='issues.list', sdk_method='issues.list', invoke=lambda c: c.issues.list(), expected_argv=('issue', 'list', '--output', 'json'), stdout=P_ISSUES_ID_ISS_001_TITLE_ISSU, check='nonempty'),
    CommandCase(id='issues.get', sdk_method='issues.get', invoke=lambda c: c.issues.get("iss_001"), expected_argv=('issue', 'get', 'iss_001', '--output', 'json'), stdout=P_ID_ISS_001_TITLE_TEST_ISSUE_DE),
    CommandCase(id='issues.create', sdk_method='issues.create', invoke=lambda c: c.issues.create(IssueCreateRequest(title="New issue")), expected_argv=('issue', 'create', '--title', 'New issue', '--output', 'json'), stdout=P_ID_ISS_001_TITLE_TEST_ISSUE_ST),
    CommandCase(id='issues.update', sdk_method='issues.update', invoke=lambda c: c.issues.update("iss_001", IssueUpdateRequest(title="Updated")), expected_argv=('issue', 'update', 'iss_001', '--title', 'Updated', '--output', 'json'), stdout=P_ID_ISS_001_TITLE_TEST_ISSUE_ST),
    CommandCase(id='issues.assign', sdk_method='issues.assign', invoke=lambda c: c.issues.assign(IssueAssignmentRequest(issue_id="iss_001", member_id="usr_001")), expected_argv=('issue', 'assign', 'iss_001', '--to-id', 'usr_001', '--output', 'json'), stdout=P_ID_ISS_001_TITLE_TEST_ISSUE_ST),
    CommandCase(id='issues.set_status', sdk_method='issues.set_status', invoke=lambda c: c.issues.set_status("iss_001", IssueStatus.done), expected_argv=('issue', 'status', 'iss_001', 'done', '--output', 'json'), stdout=P_ID_ISS_001_TITLE_TEST_ISSUE_ST_2, check='issue_done'),
    CommandCase(id='issues.deprioritize', sdk_method='issues.deprioritize', invoke=lambda c: c.issues.deprioritize("iss_001"), expected_argv=('issue', 'deprioritize', 'iss_001'), stdout=P_ISSUE_ISS_001_DEPRIORITIZED, check='deprioritized'),
    CommandCase(id='issues.reorder', sdk_method='issues.reorder', invoke=lambda c: c.issues.reorder(IssueReorderRequest(issue_id="iss_001", top=True)), expected_argv=('issue', 'reorder', 'iss_001', '--top', '--output', 'json'), stdout=P_ID_ISS_001_TITLE_TEST_ISSUE_ST),
    CommandCase(id='issues.search', sdk_method='issues.search', invoke=lambda c: c.issues.search("bug"), expected_argv=('issue', 'search', 'bug', '--output', 'json'), stdout=P_EMPTY),
    CommandCase(id='issues.children', sdk_method='issues.children', invoke=lambda c: c.issues.children("iss_001"), expected_argv=('issue', 'children', 'iss_001', '--output', 'json'), stdout=P_NAME_TODO_COUNT_1, check='nonempty'),
    CommandCase(id='issues.pull_requests', sdk_method='issues.pull_requests', invoke=lambda c: c.issues.pull_requests("iss_001"), expected_argv=('issue', 'pull-requests', 'iss_001', '--output', 'json'), stdout=P_URL_HTTPS_EXAMPLE_COM_PR_1, check='nonempty'),
    CommandCase(id='issues.runs', sdk_method='issues.runs', invoke=lambda c: c.issues.runs("iss_001"), expected_argv=('issue', 'runs', 'iss_001', '--output', 'json'), stdout=P_ID_RUN_001_STATUS_DONE, check='nonempty'),
    CommandCase(id='issues.run_messages', sdk_method='issues.run_messages', invoke=lambda c: c.issues.run_messages("iss_001", "run_001"), expected_argv=('issue', 'run-messages', 'iss_001', '--run-id', 'run_001', '--output', 'json'), stdout=P_ID_MSG_001_RUN_ID_RUN_001_ROL, check='nonempty'),
    CommandCase(id='issues.usage', sdk_method='issues.usage', invoke=lambda c: c.issues.usage("iss_001"), expected_argv=('issue', 'usage', 'iss_001', '--output', 'json'), stdout=P_TOTAL_RUNS_3),
    CommandCase(id='issues.rerun', sdk_method='issues.rerun', invoke=lambda c: c.issues.rerun("iss_001", "run_001"), expected_argv=('issue', 'rerun', 'iss_001', '--run-id', 'run_001'), check='none'),
    CommandCase(id='issues.cancel_task', sdk_method='issues.cancel_task', invoke=lambda c: c.issues.cancel_task("iss_001", "run_001"), expected_argv=('issue', 'cancel-task', 'iss_001', '--run-id', 'run_001'), check='none'),
    CommandCase(id='issues.comments.list', sdk_method='issues.comments.list', invoke=lambda c: c.issues.comments.list("iss_001"), expected_argv=('issue', 'comment', 'list', 'iss_001', '--output', 'json'), stdout=P_ID_CMT_001_CONTENT_HELLO, check='nonempty'),
    CommandCase(id='issues.comments.add', sdk_method='issues.comments.add', invoke=lambda c: c.issues.comments.add("iss_001", "hello"), expected_argv=('issue', 'comment', 'add', 'iss_001', '--content', 'hello', '--output', 'json'), stdout=P_ID_CMT_001_CONTENT_HELLO_2),
    CommandCase(id='issues.comments.reply', sdk_method='issues.comments.reply', invoke=lambda c: c.issues.comments.reply("iss_001", "th_001", "reply"), expected_argv=('issue', 'comment', 'add', 'iss_001', '--content', 'reply', '--parent', 'th_001', '--output', 'json'), stdout=P_ID_CMT_001_CONTENT_HELLO_2),
    CommandCase(id='issues.comments.delete', sdk_method='issues.comments.delete', invoke=lambda c: c.issues.comments.delete("cmt_001"), expected_argv=('issue', 'comment', 'delete', 'cmt_001'), check='none'),
    CommandCase(id='issues.comments.resolve', sdk_method='issues.comments.resolve', invoke=lambda c: c.issues.comments.resolve("th_001"), expected_argv=('issue', 'comment', 'resolve', 'th_001'), check='none'),
    CommandCase(id='issues.comments.unresolve', sdk_method='issues.comments.unresolve', invoke=lambda c: c.issues.comments.unresolve("th_001"), expected_argv=('issue', 'comment', 'unresolve', 'th_001'), check='none'),
    CommandCase(id='issues.labels.list', sdk_method='issues.labels.list', invoke=lambda c: c.issues.labels.list("iss_001"), expected_argv=('issue', 'label', 'list', 'iss_001', '--output', 'json'), stdout=P_ID_LBL_001_NAME_BUG_COLOR, check='labels'),
    CommandCase(id='issues.labels.add', sdk_method='issues.labels.add', invoke=lambda c: c.issues.labels.add("iss_001", "lbl_001"), expected_argv=('issue', 'label', 'add', 'iss_001', 'lbl_001', '--output', 'json'), stdout=P_ID_LBL_001_NAME_BUG_COLOR, check='labels'),
    CommandCase(id='issues.labels.remove', sdk_method='issues.labels.remove', invoke=lambda c: c.issues.labels.remove("iss_001", "lbl_001"), expected_argv=('issue', 'label', 'remove', 'iss_001', 'lbl_001', '--output', 'json'), stdout=P_EMPTY),
    CommandCase(id='issues.metadata.list', sdk_method='issues.metadata.list', invoke=lambda c: c.issues.metadata.list("iss_001"), expected_argv=('issue', 'metadata', 'list', 'iss_001', '--output', 'json'), stdout=P_KEY_FLAG_VALUE_TRUE, check='nonempty'),
    CommandCase(id='issues.metadata.get', sdk_method='issues.metadata.get', invoke=lambda c: c.issues.metadata.get("iss_001", "flag"), expected_argv=('issue', 'metadata', 'get', 'iss_001', '--key', 'flag', '--output', 'json'), stdout=P_KEY_FLAG_VALUE_TRUE_2),
    CommandCase(id='issues.metadata.set', sdk_method='issues.metadata.set', invoke=lambda c: c.issues.metadata.set("iss_001", "flag", True), expected_argv=('issue', 'metadata', 'set', 'iss_001', '--key', 'flag', '--value', 'true', '--type', 'boolean', '--output', 'json'), stdout=P_KEY_FLAG_VALUE_TRUE_2),
    CommandCase(id='issues.metadata.delete', sdk_method='issues.metadata.delete', invoke=lambda c: c.issues.metadata.delete("iss_001", "flag"), expected_argv=('issue', 'metadata', 'delete', 'iss_001', '--key', 'flag'), check='none'),
    CommandCase(id='issues.subscribers.list', sdk_method='issues.subscribers.list', invoke=lambda c: c.issues.subscribers.list("iss_001"), expected_argv=('issue', 'subscriber', 'list', 'iss_001', '--output', 'json'), stdout=P_ISSUE_ID_ISS_001_USER_TYPE_MEM, check='nonempty'),
    CommandCase(id='issues.subscribers.add', sdk_method='issues.subscribers.add', invoke=lambda c: c.issues.subscribers.add("iss_001", "usr_001"), expected_argv=('issue', 'subscriber', 'add', 'iss_001', '--user-id', 'usr_001'), stdout=P_ID_USR_001_NAME_USER, check='none'),
    CommandCase(id='issues.subscribers.remove', sdk_method='issues.subscribers.remove', invoke=lambda c: c.issues.subscribers.remove("iss_001", "usr_001"), expected_argv=('issue', 'subscriber', 'remove', 'iss_001', '--user-id', 'usr_001'), check='none'),
    CommandCase(id='labels.list', sdk_method='labels.list', invoke=lambda c: c.labels.list(), expected_argv=('label', 'list', '--output', 'json'), stdout=P_ID_LBL_001_NAME_BUG_COLOR_R, check='labels'),
    CommandCase(id='labels.get', sdk_method='labels.get', invoke=lambda c: c.labels.get("lbl_001"), expected_argv=('label', 'get', 'lbl_001', '--output', 'json'), stdout=P_ID_LBL_001_NAME_BUG_COLOR_F),
    CommandCase(id='labels.create', sdk_method='labels.create', invoke=lambda c: c.labels.create("bug"), expected_argv=('label', 'create', '--name', 'bug', '--output', 'json'), stdout=P_ID_LBL_001_NAME_BUG_COLOR_F),
    CommandCase(id='labels.update', sdk_method='labels.update', invoke=lambda c: c.labels.update("lbl_001", name="feature"), expected_argv=('label', 'update', 'lbl_001', '--name', 'feature', '--output', 'json'), stdout=P_ID_LBL_001_NAME_BUG_COLOR_F),
    CommandCase(id='labels.delete', sdk_method='labels.delete', invoke=lambda c: c.labels.delete("lbl_001"), expected_argv=('label', 'delete', 'lbl_001'), check='none'),
    CommandCase(id='maintenance.version', sdk_method='maintenance.version', invoke=lambda c: c.maintenance.version(), expected_argv=('version', '--output', 'json'), stdout=P_VERSION_0_1_0_COMMIT_ABC123_BU, check='maintenance_version'),
    CommandCase(id="maintenance.update", sdk_method="maintenance.update", invoke=lambda c: c.maintenance.update(), expected_argv=("update",)),
    CommandCase(id='projects.list', sdk_method='projects.list', invoke=lambda c: c.projects.list(), expected_argv=('project', 'list', '--output', 'json'), stdout=P_ID_PR_001_TITLE_PROJECT_ALPHA, check='nonempty'),
    CommandCase(id='projects.get', sdk_method='projects.get', invoke=lambda c: c.projects.get("pr_001"), expected_argv=('project', 'get', 'pr_001', '--output', 'json'), stdout=P_ID_PR_001_TITLE_ALPHA_STATUS),
    CommandCase(id='projects.create', sdk_method='projects.create', invoke=lambda c: c.projects.create(ProjectCreateRequest(name="Alpha")), expected_argv=('project', 'create', '--title', 'Alpha', '--output', 'json'), stdout=P_ID_PR_001_TITLE_ALPHA_STATUS),
    CommandCase(id='projects.update', sdk_method='projects.update', invoke=lambda c: c.projects.update("pr_001", ProjectUpdateRequest(name="Beta")), expected_argv=('project', 'update', 'pr_001', '--title', 'Beta', '--output', 'json'), stdout=P_ID_PR_001_TITLE_ALPHA_STATUS),
    CommandCase(id='projects.delete', sdk_method='projects.delete', invoke=lambda c: c.projects.delete("pr_001"), expected_argv=('project', 'delete', 'pr_001'), check='none'),
    CommandCase(id='projects.set_status', sdk_method='projects.set_status', invoke=lambda c: c.projects.set_status("pr_001", ProjectStatus.completed), expected_argv=('project', 'status', 'pr_001', 'completed', '--output', 'json'), stdout=P_ID_PR_001_TITLE_PROJECT_ALPHA_2, check='project_completed'),
    CommandCase(id='repositories.list', sdk_method='repositories.list', invoke=lambda c: c.repositories.list(), expected_argv=('repo', 'list', '--output', 'json'), stdout=P_ID_RP_001_NAME_MAIN_REPO_URL, check='nonempty'),
    CommandCase(id='repositories.get', sdk_method='repositories.get', invoke=lambda c: c.repositories.get("repo_001"), expected_argv=('repo', 'get', 'repo_001', '--output', 'json'), stdout=P_ID_REPO_001_NAME_REPO),
    CommandCase(id='repositories.checkout', sdk_method='repositories.checkout', invoke=lambda c: c.repositories.checkout("repo_001", "main"), expected_argv=('repo', 'checkout', 'repo_001', '--branch', 'main', '--output', 'json'), stdout=P_PATH_TMP_REPO_BRANCH_MAIN_SUC),
    CommandCase(id='runtimes.list', sdk_method='runtimes.list', invoke=lambda c: c.runtimes.list(), expected_argv=('runtime', 'list', '--output', 'json'), stdout=P_ID_RT_001_NAME_PYTHON3_VERSIO, check='nonempty'),
    CommandCase(id='runtimes.get', sdk_method='runtimes.get', invoke=lambda c: c.runtimes.get("rt_001"), expected_argv=('runtime', 'get', 'rt_001', '--output', 'json'), stdout=P_ID_RT_001_NAME_PYTHON),
    CommandCase(id='setup.cloud', sdk_method='setup.cloud', invoke=lambda c: c.setup.cloud(), expected_argv=('setup', 'cloud'), stdout=P_CLOUD_SETUP_INITIATED),
    CommandCase(id='setup.self_host', sdk_method='setup.self_host', invoke=lambda c: c.setup.self_host("https://example.com"), expected_argv=('setup', 'self-host', '--url', 'https://example.com')),
    CommandCase(id='skills.list', sdk_method='skills.list', invoke=lambda c: c.skills.list(), expected_argv=('skill', 'list', '--output', 'json'), stdout=P_ID_SK_001_NAME_PYTHON_FILE_CO, check='nonempty'),
    CommandCase(id='skills.get', sdk_method='skills.get', invoke=lambda c: c.skills.get("sk_001"), expected_argv=('skill', 'get', 'sk_001', '--output', 'json'), stdout=P_ID_SK_001_NAME_SKILL_2),
    CommandCase(id='skills.create', sdk_method='skills.create', invoke=lambda c: c.skills.create(SkillCreateRequest(name="Skill")), expected_argv=('skill', 'create', '--name', 'Skill', '--output', 'json'), stdout=P_ID_SK_001_NAME_SKILL_2),
    CommandCase(id='skills.update', sdk_method='skills.update', invoke=lambda c: c.skills.update("sk_001", SkillUpdateRequest(name="Renamed")), expected_argv=('skill', 'update', 'sk_001', '--name', 'Renamed', '--output', 'json'), stdout=P_ID_SK_001_NAME_SKILL_2),
    CommandCase(id='skills.delete', sdk_method='skills.delete', invoke=lambda c: c.skills.delete("sk_001"), expected_argv=('skill', 'delete', 'sk_001'), check='none'),
    CommandCase(id='skills.import_from_url', sdk_method='skills.import_from_url', invoke=lambda c: c.skills.import_from_url("https://example.com/skill"), expected_argv=('skill', 'import', '--url', 'https://example.com/skill', '--output', 'json'), stdout=P_ID_SK_001_NAME_SKILL_2),
    CommandCase(id='skills.files.list', sdk_method='skills.files.list', invoke=lambda c: c.skills.files.list("sk_001"), expected_argv=('skill', 'file', 'list', 'sk_001', '--output', 'json'), stdout=P_ID_F_001_PATH_SKILL_MD_CONTEN, check='nonempty'),
    CommandCase(id='skills.files.upsert', sdk_method='skills.files.upsert', invoke=lambda c: c.skills.files.upsert("sk_001", "SKILL.md", "# Skill"), expected_argv=('skill', 'file', 'upsert', 'sk_001', '--path', 'SKILL.md', '--content', '# Skill', '--output', 'json'), stdout=P_ID_F_001_PATH_SKILL_MD_CONTENT),
    CommandCase(id='skills.files.delete', sdk_method='skills.files.delete', invoke=lambda c: c.skills.files.delete("sk_001", "f_001"), expected_argv=('skill', 'file', 'delete', 'sk_001', '--file-id', 'f_001'), check='none'),
    CommandCase(id='squads.list', sdk_method='squads.list', invoke=lambda c: c.squads.list(), expected_argv=('squad', 'list', '--output', 'json'), stdout=P_ID_SQ_001_NAME_TEAM_A_MEMBER, check='nonempty'),
    CommandCase(id='squads.get', sdk_method='squads.get', invoke=lambda c: c.squads.get("sq_001"), expected_argv=('squad', 'get', 'sq_001', '--output', 'json'), stdout=P_ID_SQ_001_NAME_SQUAD),
    CommandCase(id='users.list', sdk_method='users.list', invoke=lambda c: c.users.list(), expected_argv=('user', 'list', '--output', 'json'), stdout=P_ID_US_001_NAME_ALICE_ID_U, check='nonempty'),
    CommandCase(id='users.get', sdk_method='users.get', invoke=lambda c: c.users.get("usr_001"), expected_argv=('user', 'get', 'usr_001', '--output', 'json'), stdout=P_ID_USR_001_NAME_ALICE),
    CommandCase(id='workspaces.list', sdk_method='workspaces.list', invoke=lambda c: c.workspaces.list(), expected_argv=('workspace', 'list', '--output', 'json'), stdout=P_ID_WS_001_NAME_MAIN_WORKSPACE, check='nonempty'),
    CommandCase(id='workspaces.get', sdk_method='workspaces.get', invoke=lambda c: c.workspaces.get("ws_001"), expected_argv=('workspace', 'get', 'ws_001', '--output', 'json'), stdout=P_ID_WS_001_NAME_MAIN),
    CommandCase(id='workspaces.members', sdk_method='workspaces.members', invoke=lambda c: c.workspaces.members("ws_001"), expected_argv=('workspace', 'member', 'list', 'ws_001', '--output', 'json'), stdout=P_ID_USR_001_NAME_ALICE_2, check='nonempty'),
    CommandCase(id='workspaces.switch', sdk_method='workspaces.switch', invoke=lambda c: c.workspaces.switch("ws_001"), expected_argv=('workspace', 'switch', 'ws_001'), check='none'),
    CommandCase(id='workspaces.watch', sdk_method='workspaces.watch', invoke=lambda c: c.workspaces.watch("ws_001"), expected_argv=('workspace', 'watch', 'ws_001'), check='none'),
    CommandCase(id='workspaces.unwatch', sdk_method='workspaces.unwatch', invoke=lambda c: c.workspaces.unwatch("ws_001"), expected_argv=('workspace', 'unwatch', 'ws_001'), check='none'),
)

PROJECT_RESOURCE_COMMAND_CASES: tuple[CommandCase, ...] = (
    CommandCase(id='projects.resources.list', sdk_method='projects.resources.list', invoke=lambda c: c.projects.resources.list("pr_001"), expected_argv=('project', 'resource', 'list', 'pr_001', '--output', 'json'), stdout=P_PROJECT_RESOURCE_LIST, check='nonempty'),
    CommandCase(id='projects.resources.add_local_directory', sdk_method='projects.resources.add_local_directory', invoke=lambda c: c.projects.resources.add_local_directory("pr_001", ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id="daemon-001")), expected_argv=('project', 'resource', 'add', 'pr_001', '--type', 'local_directory', '--local-path', _PR_LOCAL_DIR, '--daemon-id', 'daemon-001', '--output', 'json'), stdout=P_PROJECT_RESOURCE_RECORD),
    CommandCase(id='projects.resources.add_local_directory.label', sdk_method='projects.resources.add_local_directory', invoke=lambda c: c.projects.resources.add_local_directory("pr_001", ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id="daemon-001", label="main")), expected_argv=('project', 'resource', 'add', 'pr_001', '--type', 'local_directory', '--local-path', _PR_LOCAL_DIR, '--daemon-id', 'daemon-001', '--ref-label', 'main', '--output', 'json'), stdout=P_PROJECT_RESOURCE_RECORD),
    CommandCase(id='projects.resources.update_local_directory', sdk_method='projects.resources.update_local_directory', invoke=lambda c: c.projects.resources.update_local_directory("pr_001", "res_001", ProjectResourceUpdateLocalDirectoryRequest(local_path="/tmp/sandbox")), expected_argv=('project', 'resource', 'update', 'pr_001', 'res_001', '--local-path', _PR_LOCAL_DIR, '--output', 'json'), stdout=P_PROJECT_RESOURCE_RECORD),
    CommandCase(id='projects.resources.remove', sdk_method='projects.resources.remove', invoke=lambda c: c.projects.resources.remove("pr_001", "res_001"), expected_argv=('project', 'resource', 'remove', 'pr_001', 'res_001'), check='none'),
)

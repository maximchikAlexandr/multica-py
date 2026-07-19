from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from multica_py.client import MulticaClient
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.models.agents import AgentCreateRequest, AgentUpdateRequest
from multica_py.models.issues import (
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueReorderRequest,
    IssueUpdateRequest,
)
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.skills import SkillCreateRequest, SkillUpdateRequest
from multica_py.models.system import AttachmentResult


@dataclass(frozen=True)
class FakeCliCase:
    fixture: str
    sdk_call: Callable[[MulticaClient], object]
    check: Callable[[object], None]
    sdk_method: str
    id: str = ""


def _fc(
    fixture: str,
    call: Callable[[MulticaClient], object],
    check: Callable[[object], None],
    sdk_method: str,
    *,
    id: str | None = None,
) -> FakeCliCase:
    return FakeCliCase(
        fixture=fixture,
        sdk_call=call,
        check=check,
        sdk_method=sdk_method,
        id=id or sdk_method,
    )


def _check_nonempty(r: object) -> None:
    assert r is not None
    assert len(r) > 0  # type: ignore[arg-type]


def _check_not_none(r: object) -> None:
    assert r is not None


def _check_none(r: object) -> None:
    assert r is None


def _check_labels(r: object) -> None:
    _check_nonempty(r)
    assert r[0].id == "lbl_001"  # type: ignore[index]


def _check_auth_login(r: object) -> None:
    assert r == "Login successful"


def _check_auth_status(r: object) -> None:
    assert r.authenticated is True  # type: ignore[attr-defined]


def _check_auth_logout(r: object) -> None:
    assert r.authenticated is False  # type: ignore[attr-defined]


def _check_daemon_status(r: object) -> None:
    assert r.running is True  # type: ignore[attr-defined]


def _check_issue_status_done(r: object) -> None:
    assert r.status == IssueStatus.done  # type: ignore[attr-defined]


def _check_deprioritized(r: object) -> None:
    assert "deprioritized" in r  # type: ignore[operator]


def _check_project_completed(r: object) -> None:
    assert r.status == ProjectStatus.completed  # type: ignore[attr-defined]


def _check_maintenance_version(r: object) -> None:
    assert r.version == "0.1.0"  # type: ignore[attr-defined]


# fmt: off
FAKE_CLI_CASES: tuple[FakeCliCase, ...] = (
    _fc("agents/agent_list.json", lambda c: c.agents.list(), _check_nonempty, "agents.list"),
    _fc("agents/agent_archive_ag_001.json", lambda c: c.agents.archive("ag_001"), _check_none, "agents.archive"),
    _fc("agents/agent_create.json", lambda c: c.agents.create(AgentCreateRequest(name="Helper")), _check_not_none, "agents.create"),
    _fc("agents/agent_get_ag_001.json", lambda c: c.agents.get("ag_001"), _check_not_none, "agents.get"),
    _fc("agents/agent_restore_ag_001.json", lambda c: c.agents.restore("ag_001"), _check_none, "agents.restore"),
    _fc("agents/agent_skill_list_ag_001.json", lambda c: c.agents.skills.list("ag_001"), _check_nonempty, "agents.skills.list"),
    _fc("agents/agent_skill_set_ag_001.json", lambda c: c.agents.skills.set("ag_001", ("sk_001",)), _check_none, "agents.skills.set"),
    _fc("agents/agent_tasks_ag_001.json", lambda c: c.agents.tasks("ag_001"), _check_nonempty, "agents.tasks"),
    _fc("agents/agent_update_ag_001.json", lambda c: c.agents.update("ag_001", AgentUpdateRequest(name="Helper")), _check_not_none, "agents.update"),
    _fc("agents/agent_avatar_upload_ag_001.json", lambda c: c.agents.upload_avatar("ag_001", "/tmp/avatar.png"), _check_none, "agents.upload_avatar"),
    _fc("attachments/attachment_list.json", lambda c: c.attachments._run_json_decode_list(("attachment", "list"), AttachmentResult), _check_nonempty, "attachments.list", id="attachments.list.all"),
    _fc("attachments/attachment_list_iss_001.json", lambda c: c.attachments.list("iss_001"), _check_nonempty, "attachments.list", id="attachments.list.iss_001"),
    _fc("attachments/attachment_upload_iss_001.json", lambda c: c.attachments.upload("iss_001", "/tmp/file.txt"), _check_not_none, "attachments.upload"),
    _fc("attachments/attachment_download_att_001.json", lambda c: c.attachments.download("att_001", "/tmp/out.txt"), _check_none, "attachments.download"),
    _fc("auth/auth_login.json", lambda c: c.auth.login("secret-token"), _check_auth_login, "auth.login"),
    _fc("auth/auth_status.json", lambda c: c.auth.status(), _check_auth_status, "auth.status"),
    _fc("auth/auth_logout.json", lambda c: c.auth.logout(), _check_auth_logout, "auth.logout"),
    _fc("autopilots/autopilot_list.json", lambda c: c.autopilots.list(), _check_nonempty, "autopilots.list"),
    _fc("autopilots/autopilot_create.json", lambda c: c.autopilots.create("AP"), _check_not_none, "autopilots.create"),
    _fc("autopilots/autopilot_get_ap_001.json", lambda c: c.autopilots.get("ap_001"), _check_not_none, "autopilots.get"),
    _fc("autopilots/autopilot_update_ap_001.json", lambda c: c.autopilots.update("ap_001", name="Renamed"), _check_not_none, "autopilots.update"),
    _fc("autopilots/autopilot_delete_ap_001.json", lambda c: c.autopilots.delete("ap_001"), _check_none, "autopilots.delete"),
    _fc("autopilots/autopilot_run_ap_001.json", lambda c: c.autopilots.run("ap_001"), _check_not_none, "autopilots.run"),
    _fc("autopilots/autopilot_history_ap_001.json", lambda c: c.autopilots.history("ap_001"), _check_nonempty, "autopilots.history"),
    _fc("autopilots/autopilot_run_get_run_001.json", lambda c: c.autopilots.get_run("run_001"), _check_not_none, "autopilots.get_run"),
    _fc("autopilots/autopilot_trigger_list_ap_001.json", lambda c: c.autopilots.triggers.list("ap_001"), _check_nonempty, "autopilots.triggers.list"),
    _fc("autopilots/autopilot_trigger_create_ap_001.json", lambda c: c.autopilots.triggers.create("ap_001", "webhook"), _check_not_none, "autopilots.triggers.create"),
    _fc("autopilots/autopilot_trigger_delete_ap_001.json", lambda c: c.autopilots.triggers.delete("ap_001", "tr_001"), _check_none, "autopilots.triggers.delete"),
    _fc("configuration/config_show.json", lambda c: c.configuration.show(), _check_not_none, "configuration.show"),
    _fc("configuration/config_get_key.json", lambda c: c.configuration.get("key"), _check_not_none, "configuration.get"),
    _fc("configuration/config_set_key_val.json", lambda c: c.configuration.set("key", "val"), _check_none, "configuration.set"),
    _fc("daemon/daemon_status.json", lambda c: c.daemon.status(), _check_daemon_status, "daemon.status"),
    _fc("daemon/daemon_disk-usage.json", lambda c: c.daemon.disk_usage(), _check_nonempty, "daemon.disk_usage"),
    _fc("daemon/daemon_start.json", lambda c: c.daemon.start(), _check_not_none, "daemon.start"),
    _fc("daemon/daemon_stop.json", lambda c: c.daemon.stop(), _check_not_none, "daemon.stop"),
    _fc("daemon/daemon_restart.json", lambda c: c.daemon.restart(), _check_not_none, "daemon.restart"),
    _fc("daemon/daemon_logs.json", lambda c: c.daemon.logs(), _check_not_none, "daemon.logs"),
    _fc("issues/issue_list.json", lambda c: c.issues.list(), _check_nonempty, "issues.list"),
    _fc("issues/issue_get_iss_001.json", lambda c: c.issues.get("iss_001"), _check_not_none, "issues.get"),
    _fc("issues/issue_create.json", lambda c: c.issues.create(IssueCreateRequest(title="New issue")), _check_not_none, "issues.create"),
    _fc("issues/issue_update_iss_001.json", lambda c: c.issues.update("iss_001", IssueUpdateRequest(title="Updated")), _check_not_none, "issues.update"),
    _fc("issues/issue_assign_iss_001.json", lambda c: c.issues.assign(IssueAssignmentRequest(issue_id="iss_001", member_id="usr_001")), _check_not_none, "issues.assign"),
    _fc("issues/issue_status_iss_001_done.json", lambda c: c.issues.set_status("iss_001", IssueStatus.done), _check_issue_status_done, "issues.set_status"),
    _fc("issues/issue_deprioritize_iss_001.json", lambda c: c.issues.deprioritize("iss_001"), _check_deprioritized, "issues.deprioritize"),
    _fc("issues/issue_reorder_iss_001.json", lambda c: c.issues.reorder(IssueReorderRequest(issue_id="iss_001", top=True)), _check_not_none, "issues.reorder"),
    _fc("issues/issue_search_bug.json", lambda c: c.issues.search("bug"), _check_not_none, "issues.search"),
    _fc("issues/issue_children_iss_001.json", lambda c: c.issues.children("iss_001"), _check_nonempty, "issues.children"),
    _fc("issues/issue_pull-requests_iss_001.json", lambda c: c.issues.pull_requests("iss_001"), _check_nonempty, "issues.pull_requests"),
    _fc("issues/issue_runs_iss_001.json", lambda c: c.issues.runs("iss_001"), _check_nonempty, "issues.runs"),
    _fc("issues/issue_run-messages_iss_001.json", lambda c: c.issues.run_messages("iss_001", "run_001"), _check_nonempty, "issues.run_messages"),
    _fc("issues/issue_usage_iss_001.json", lambda c: c.issues.usage("iss_001"), _check_not_none, "issues.usage"),
    _fc("issues/issue_rerun_iss_001.json", lambda c: c.issues.rerun("iss_001", "run_001"), _check_none, "issues.rerun"),
    _fc("issues/issue_cancel-task_iss_001.json", lambda c: c.issues.cancel_task("iss_001", "run_001"), _check_none, "issues.cancel_task"),
    _fc("issues/issue_comment_list_iss_001.json", lambda c: c.issues.comments.list("iss_001"), _check_nonempty, "issues.comments.list"),
    _fc("issues/issue_comment_add_iss_001.json", lambda c: c.issues.comments.add("iss_001", "hello"), _check_not_none, "issues.comments.add"),
    _fc("issues/issue_comment_add_iss_001.json", lambda c: c.issues.comments.reply("iss_001", "th_001", "reply"), _check_not_none, "issues.comments.reply"),
    _fc("issues/issue_comment_delete_cmt_001.json", lambda c: c.issues.comments.delete("cmt_001"), _check_none, "issues.comments.delete"),
    _fc("issues/issue_comment_resolve_th_001.json", lambda c: c.issues.comments.resolve("th_001"), _check_none, "issues.comments.resolve"),
    _fc("issues/issue_comment_unresolve_th_001.json", lambda c: c.issues.comments.unresolve("th_001"), _check_none, "issues.comments.unresolve"),
    _fc("issues/issue_label_list_iss_001.json", lambda c: c.issues.labels.list("iss_001"), _check_labels, "issues.labels.list"),
    _fc("issues/issue_label_add_iss_001_lbl_001.json", lambda c: c.issues.labels.add("iss_001", "lbl_001"), _check_labels, "issues.labels.add"),
    _fc("issues/issue_label_remove_iss_001_lbl_001.json", lambda c: c.issues.labels.remove("iss_001", "lbl_001"), _check_not_none, "issues.labels.remove"),
    _fc("issues/issue_metadata_list_iss_001.json", lambda c: c.issues.metadata.list("iss_001"), _check_nonempty, "issues.metadata.list"),
    _fc("issues/issue_metadata_get_iss_001.json", lambda c: c.issues.metadata.get("iss_001", "flag"), _check_not_none, "issues.metadata.get"),
    _fc("issues/issue_metadata_set_iss_001.json", lambda c: c.issues.metadata.set("iss_001", "flag", True), _check_not_none, "issues.metadata.set"),
    _fc("issues/issue_metadata_delete_iss_001.json", lambda c: c.issues.metadata.delete("iss_001", "flag"), _check_none, "issues.metadata.delete"),
    _fc("issues/issue_subscriber_list_iss_001.json", lambda c: c.issues.subscribers.list("iss_001"), _check_nonempty, "issues.subscribers.list"),
    _fc("issues/issue_subscriber_add_iss_001.json", lambda c: c.issues.subscribers.add("iss_001", "usr_001"), _check_none, "issues.subscribers.add"),
    _fc("issues/issue_subscriber_remove_iss_001.json", lambda c: c.issues.subscribers.remove("iss_001", "usr_001"), _check_none, "issues.subscribers.remove"),
    _fc("labels/label_list.json", lambda c: c.labels.list(), _check_labels, "labels.list"),
    _fc("labels/label_get_lbl_001.json", lambda c: c.labels.get("lbl_001"), _check_not_none, "labels.get"),
    _fc("labels/label_create.json", lambda c: c.labels.create("bug"), _check_not_none, "labels.create"),
    _fc("labels/label_update_lbl_001.json", lambda c: c.labels.update("lbl_001", name="feature"), _check_not_none, "labels.update"),
    _fc("labels/label_delete_lbl_001.json", lambda c: c.labels.delete("lbl_001"), _check_none, "labels.delete"),
    _fc("maintenance/maintenance_version.json", lambda c: c.maintenance.version(), _check_maintenance_version, "maintenance.version"),
    _fc("maintenance/update.json", lambda c: c.maintenance.update(), _check_not_none, "maintenance.update"),
    _fc("projects/project_list.json", lambda c: c.projects.list(), _check_nonempty, "projects.list"),
    _fc("projects/project_get_pr_001.json", lambda c: c.projects.get("pr_001"), _check_not_none, "projects.get"),
    _fc("projects/project_create.json", lambda c: c.projects.create(ProjectCreateRequest(name="Alpha")), _check_not_none, "projects.create"),
    _fc("projects/project_update_pr_001.json", lambda c: c.projects.update("pr_001", ProjectUpdateRequest(name="Beta")), _check_not_none, "projects.update"),
    _fc("projects/project_delete_pr_001.json", lambda c: c.projects.delete("pr_001"), _check_none, "projects.delete"),
    _fc("projects/project_status_pr_001_completed.json", lambda c: c.projects.set_status("pr_001", ProjectStatus.completed), _check_project_completed, "projects.set_status"),
    _fc("repositories/repo_list.json", lambda c: c.repositories.list(), _check_nonempty, "repositories.list"),
    _fc("repositories/repo_get_repo_001.json", lambda c: c.repositories.get("repo_001"), _check_not_none, "repositories.get"),
    _fc("repositories/repo_checkout_repo_001.json", lambda c: c.repositories.checkout("repo_001", "main"), _check_not_none, "repositories.checkout"),
    _fc("runtimes/runtime_list.json", lambda c: c.runtimes.list(), _check_nonempty, "runtimes.list"),
    _fc("runtimes/runtime_get_rt_001.json", lambda c: c.runtimes.get("rt_001"), _check_not_none, "runtimes.get"),
    _fc("setup/setup_cloud.json", lambda c: c.setup.cloud(), _check_not_none, "setup.cloud"),
    _fc("setup/setup_self-host.json", lambda c: c.setup.self_host("https://example.com"), _check_not_none, "setup.self_host"),
    _fc("skills/skill_list.json", lambda c: c.skills.list(), _check_nonempty, "skills.list"),
    _fc("skills/skill_get_sk_001.json", lambda c: c.skills.get("sk_001"), _check_not_none, "skills.get"),
    _fc("skills/skill_create.json", lambda c: c.skills.create(SkillCreateRequest(name="Skill")), _check_not_none, "skills.create"),
    _fc("skills/skill_update_sk_001.json", lambda c: c.skills.update("sk_001", SkillUpdateRequest(name="Renamed")), _check_not_none, "skills.update"),
    _fc("skills/skill_delete_sk_001.json", lambda c: c.skills.delete("sk_001"), _check_none, "skills.delete"),
    _fc("skills/skill_import.json", lambda c: c.skills.import_from_url("https://example.com/skill"), _check_not_none, "skills.import_from_url"),
    _fc("skills/skill_file_list_sk_001.json", lambda c: c.skills.files.list("sk_001"), _check_nonempty, "skills.files.list"),
    _fc("skills/skill_file_upsert_sk_001.json", lambda c: c.skills.files.upsert("sk_001", "SKILL.md", "# Skill"), _check_not_none, "skills.files.upsert"),
    _fc("skills/skill_file_delete_sk_001.json", lambda c: c.skills.files.delete("sk_001", "f_001"), _check_none, "skills.files.delete"),
    _fc("squads/squad_list.json", lambda c: c.squads.list(), _check_nonempty, "squads.list"),
    _fc("squads/squad_get_sq_001.json", lambda c: c.squads.get("sq_001"), _check_not_none, "squads.get"),
    _fc("users/user_list.json", lambda c: c.users.list(), _check_nonempty, "users.list"),
    _fc("users/user_get_usr_001.json", lambda c: c.users.get("usr_001"), _check_not_none, "users.get"),
    _fc("workspaces/workspace_list.json", lambda c: c.workspaces.list(), _check_nonempty, "workspaces.list"),
    _fc("workspaces/workspace_get_ws_001.json", lambda c: c.workspaces.get("ws_001"), _check_not_none, "workspaces.get"),
    _fc("workspaces/workspace_member_list_ws_001.json", lambda c: c.workspaces.members("ws_001"), _check_nonempty, "workspaces.members"),
    _fc("workspaces/workspace_switch_ws_001.json", lambda c: c.workspaces.switch("ws_001"), _check_none, "workspaces.switch"),
    _fc("workspaces/workspace_watch_ws_001.json", lambda c: c.workspaces.watch("ws_001"), _check_none, "workspaces.watch"),
    _fc("workspaces/workspace_unwatch_ws_001.json", lambda c: c.workspaces.unwatch("ws_001"), _check_none, "workspaces.unwatch"),
)
# fmt: on

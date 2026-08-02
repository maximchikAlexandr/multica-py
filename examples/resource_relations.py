"""Traverse the bound resource graph through explicit load points.

The IDs are placeholders for prepared resources. Reading a relation property
is passive; all(), page(), iteration, and prefetch() may invoke the CLI.
"""

from multica_py import ClientConfig, MulticaClient


def inspect_workspace(client: MulticaClient, workspace_id: str) -> None:
    workspace = client.workspaces.get(workspace_id)

    members = workspace.members.all()
    first_issue_page = workspace.issues.page(limit=20)
    projects = workspace.projects.all()
    client.prefetch(projects, lambda project: project.issues, max_parallel=4)

    print(
        f"{workspace.name}: {len(members)} members, "
        f"{first_issue_page.total} issues, {len(projects)} projects"
    )
    for project in projects:
        resources = project.resources.all()
        print(f"  {project.name}: {len(project.issues)} issues, {len(resources)} resources")


def inspect_execution_resources(
    client: MulticaClient,
    agent_id: str,
    skill_id: str,
    squad_id: str,
) -> None:
    agent = client.agents.get(agent_id)
    skill = client.skills.get(skill_id)
    squad = client.squads.get(squad_id)

    print(f"agent skills: {len(agent.skills.all())}")
    print(f"skill files: {len(skill.files.all())}")
    print(f"squad members: {len(squad.members.all())}")


def inspect_issue(client: MulticaClient, issue_id: str) -> None:
    issue = client.issues.get(issue_id)
    comments = issue.comments.all()
    metadata = issue.metadata.all()

    for thread in issue.recent_comment_threads(limit=10).all():
        print(f"thread {thread.id}: {len(thread.comments.all())} comments")
    for run in issue.runs.all():
        print(f"run {run.id}: {len(run.messages.all())} messages")

    print(f"{issue.title}: {len(comments)} comments, metadata={tuple(metadata)}")
    _ = issue.to_data()


def inspect_autopilot(client: MulticaClient, autopilot_id: str) -> None:
    autopilot = client.autopilots.get(autopilot_id)
    triggers = autopilot.triggers

    # A complete get envelope can seed triggers without another CLI call.
    trigger_values = tuple(triggers) if triggers.loaded else triggers.all()
    runs = autopilot.runs.all()
    print(f"{autopilot.title}: {len(trigger_values)} triggers, {len(runs)} runs")


def main() -> None:
    client = MulticaClient(ClientConfig())
    inspect_workspace(client, "ws_123")
    inspect_execution_resources(client, "agent_123", "skill_123", "squad_123")
    inspect_issue(client, "issue_123")
    inspect_autopilot(client, "autopilot_123")


if __name__ == "__main__":
    main()

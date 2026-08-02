"""Read-only examples for the bound resource graph.

The IDs below are placeholders for a prepared workspace. Property access is
passive; explicit load points are marked with ``all()``, ``page()``, or
``prefetch()``.
"""

from multica_py import ClientConfig, MulticaClient


def load_graph(client: MulticaClient) -> None:
    # Workspace and project phase.
    workspace = client.workspaces.get("ws_1")
    _ = workspace.members  # no subprocess call
    workspace.members.all()
    workspace.issues.page(limit=20)
    workspace.autopilots.all()

    project = client.projects.get("project_1")
    project.resources.all()
    project.issues.all()

    # Agent, skill, squad, and workspace-member phase.
    agent = client.agents.get("agent_1")
    agent.skills.all()
    agent.tasks.all()
    agent.issues.all()
    skill = client.skills.get("skill_1")
    skill.files.all()
    squad = client.squads.get("squad_1")
    squad.members.all()
    squad.issues.all()

    # Issue, comment, metadata, and run phase.
    issue = client.issues.get("issue_1")
    issue.comments.all()
    for thread in issue.recent_comment_threads(limit=10).all():
        thread.comments.all()
    issue.labels.all()
    issue.metadata.all()
    for run in issue.runs.all():
        run.messages.all()

    # Autopilot phase. A complete get envelope may seed triggers/subscribers;
    # omitted fields stay unloaded until their governed read path is used.
    autopilot = client.autopilots.get("autopilot_1")
    triggers = autopilot.triggers
    if triggers.loaded:
        tuple(triggers)
    else:
        triggers.all()
    autopilot.subscribers.all()
    autopilot.runs.all()

    # Bounded prefetch is explicit and uses one selector shape per call.
    client.prefetch((workspace,), lambda item: item.members)
    client.prefetch((autopilot,), lambda item: item.runs)

    # Snapshot/lifecycle boundary: this is passive and excludes client state.
    _ = issue.to_data()


def main() -> None:
    load_graph(MulticaClient(ClientConfig()))


if __name__ == "__main__":
    main()

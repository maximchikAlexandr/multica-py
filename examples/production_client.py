"""Construct one production client and derive workspace-scoped views."""

from datetime import timedelta

from multica_py import ClientConfig, CompatibilityPolicy, MulticaClient


def build_client() -> MulticaClient:
    return MulticaClient(
        ClientConfig(
            server_url="https://multica.example.com",
            profile="automation",
            compatibility=CompatibilityPolicy.strict,
            timeout=timedelta(seconds=30),
            max_processes=4,
        )
    )


def inspect_workspace(client: MulticaClient, workspace_id: str) -> None:
    workspace_client = client.with_workspace(workspace_id)
    workspace = workspace_client.workspaces.get(workspace_id)

    projects = workspace.projects.all()
    workspace_client.prefetch(projects, lambda project: project.issues, max_parallel=4)

    for project in projects:
        print(f"{project.name}: {len(project.issues)} issues")

    # Public parity families share the same immutable client and previewable plans.
    print(client.chats.history_command(limit=10).commands)
    print(client.issues.wakeups.list_command("issue_123").commands)
    print(client.repositories.checkout_command("https://example.com/repo.git").commands)
    print(client.runtime_profiles.list_command().commands)


if __name__ == "__main__":
    inspect_workspace(build_client(), "ws_123")

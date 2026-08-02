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


def workspace_summary(client: MulticaClient, workspace_id: str) -> None:
    workspace_client = client.with_workspace(workspace_id)
    workspace = workspace_client.workspaces.get(workspace_id)

    projects = workspace.projects.all()
    workspace_client.prefetch(projects, lambda project: project.issues, max_parallel=4)

    for project in projects:
        print(f"{project.name}: {len(project.issues)} issues")


if __name__ == "__main__":
    workspace_summary(build_client(), "ws_123")

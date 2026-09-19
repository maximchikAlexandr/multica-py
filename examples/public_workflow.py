"""Small examples for the direct, bound public SDK surface.

The IDs are placeholders for prepared resources. Calling ``main`` therefore
requires a configured Multica installation, but all examples use public
methods and keep options out of operation-specific argv.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from multica_py import ClientConfig, MulticaClient, OperationOptions
from multica_py.models.agents import AgentConversationStarter


def run_workflow(client: MulticaClient, project_id: str, issue_id: str) -> None:
    options = OperationOptions(profile="automation", timeout=timedelta(seconds=30))
    scoped = client.with_options(profile="automation", timeout=timedelta(seconds=30))

    project = scoped.projects.get(project_id)
    issue = project.issues.create(
        title="Deploy", description="Deploy the reviewed release", options=options
    )
    issue = issue.move_to_top(options=options)
    print(issue.permalink())

    raw = scoped.cli.command("issue", "get", issue_id, options=options)
    print(raw.run().stdout)

    starter_preview = scoped.agents.create_command(
        name="Release helper",
        conversation_starters=(
            AgentConversationStarter(label="Deploy", prompt="Deploy the release."),
        ),
        options=options,
    )
    print(starter_preview.commands)

    projected = scoped.issues.list(
        fields=("id", "title", "properties"),
        property_filters=("Environment=prod",),
        resolve_properties=True,
        options=options,
    )
    print(tuple(item.id for item in projected.items))
    skill = scoped.skills.get("skill_123")
    print(scoped.skills.files.list(skill.id, with_content=True).items)
    print(skill.labels.all())
    scoped.issues.comments.update("comment_123", "Revised", expected_revision=3)

    upload = scoped.attachments.upload_command(
        Path("artifact.zip"), task_id=issue.id, options=options
    )
    upload.run()


def main() -> None:
    client = MulticaClient(
        ClientConfig(
            app_url="https://app.multica.example",
            workspace_slug="team-space",
        )
    )
    run_workflow(client, "project_123", "issue_456")


if __name__ == "__main__":
    main()

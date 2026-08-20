"""Load typed singular references without implicit transport calls.

The IDs are placeholders for prepared resources. Reading ``parent`` or
``project`` only creates/returns a passive handle; ``get()``, ``refresh()``,
command execution, and ``prefetch()`` are the explicit load points.
"""

from __future__ import annotations

from collections.abc import Sequence

from multica_py import ClientConfig, MulticaClient
from multica_py.entities import Issue, Project
from multica_py.models.relations import LazyRef


def load_optional_issue_parent(issue: Issue) -> Issue | None:
    """Load an optional parent, then read its cached value."""

    parent: LazyRef[Issue | None] = issue.parent
    if not parent.loaded:
        parent.get()
    return parent.value


def load_optional_project(issue: Issue) -> Project | None:
    """Load an optional project, then read its cached value."""

    project: LazyRef[Project | None] = issue.project
    if not project.loaded:
        project.get()
    return project.value


def inspect_issue(issue: Issue) -> None:
    """Demonstrate passive inspection, explicit load, and refresh."""

    parent = issue.parent  # property access performs no I/O
    project = issue.project  # property access performs no I/O
    if parent.loaded:
        print(f"cached parent: {parent.value}")
    elif issue.parent_id is not None:
        print(f"loaded parent: {load_optional_issue_parent(issue)}")
    else:
        print("parent is absent or has no source context")

    if project.loaded:
        print(f"cached project: {project.value}")
    elif issue.project_id is not None:
        print(f"loaded project: {load_optional_project(issue)}")
    else:
        print("project is absent or has no source context")

    # Refresh is explicit and replaces a loaded target; a loaded None is a
    # cached no-step operation.
    if parent.loaded:
        parent.refresh()


def prefetch_parents(client: MulticaClient, issues: Sequence[Issue]) -> None:
    """Bound parallelism, then read each independently cached parent value."""

    # The runtime-bound client is intentionally opaque in the entity model;
    # the public prefetch protocol still accepts these bound Issue wrappers.
    client.prefetch(issues, lambda issue: issue.parent, max_parallel=2)  # type: ignore[type-var]
    for issue in issues:
        parent = issue.parent
        if parent.loaded:
            print(f"prefetched parent for {issue.id}: {parent.value}")


def main() -> None:
    client = MulticaClient(ClientConfig())
    issues = client.issues.list(limit=20).items
    for issue in issues:
        inspect_issue(issue)
    prefetch_parents(client, issues)


if __name__ == "__main__":
    main()

# Changelog

## Unreleased — unified SDK operation contracts

This release makes the canonical/direct-resource page and action contracts
explicit. Relation `.all()` tuple snapshots remain unchanged.

- **Projects update** — before: `client.projects.update(id, ProjectUpdateRequest(...))` with `None` meaning omission; after: `client.projects.update(id, name="New name")` or a reusable typed request, with `Unset` omitted and approved nullable `None` sent as clear.
- **Issues list** — before: tuple-like/resource-specific page access; after: `page = client.issues.list(status=IssueStatus.backlog)` and `for summary in page.items` (the typed `IssueListFilter` alternative remains supported).
- **Projects list** — before: `tuple[Project, ...]`; after: immutable `Page[Project]`, accessed through `.items`, iteration, `len()`, or indexing.
- **Delete actions** — before: bare `None`; after: `ActionResult[None]`, checked through `.success` and optional redacted `.message`.
- **Repository mutations** — before: direct `RepositoryMutationResult`; after: `ActionResult[RepositoryMutationResult]`, with the payload in `.value`.
- **Command execution** — before: resource-specific command assumptions; after: `*_command()` returns `Command[T]` matching eager `T`, `commands` previews are redacted and I/O-free, and `.run()` executes the same plan.

## 0.1.0 (unreleased)

- Initial SDK release
- Complete Multica CLI coverage from pinned baseline `48b8dbf`
- Library-only: install from GitHub via `uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@v0.1.0"` (no PyPI publish yet)
- Removed earlier in-tree CLI (`multica-py` console script); SDK is consumed as a Python library

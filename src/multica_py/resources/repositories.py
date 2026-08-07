from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.models.system import RepositoryMutationResult, RepositoryRecord
from multica_py.resources._base import BaseResource


class RepositoryResource(BaseResource):
    def list_command(self) -> Command[tuple[RepositoryRecord, ...]]:
        return self._decoded_list_command(("repo", "list"), RepositoryRecord)

    def list(self) -> tuple[RepositoryRecord, ...]:
        return self.list_command().run()

    def add_command(
        self, urls: tuple[str, ...], *, description: str | None = None
    ) -> Command[RepositoryMutationResult]:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        if description is not None and len(urls) != 1:
            raise ValueError("description requires exactly one URL")
        args = ["repo", "add", *urls]
        if description is not None:
            args.extend(["--description", description])
        return self._decoded_command(tuple(args), RepositoryMutationResult)

    def add(
        self, urls: tuple[str, ...], *, description: str | None = None
    ) -> RepositoryMutationResult:
        return self.add_command(urls, description=description).run()

    def remove_command(self, urls: tuple[str, ...]) -> Command[RepositoryMutationResult]:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        return self._decoded_command(("repo", "remove", *urls), RepositoryMutationResult)

    def remove(self, urls: tuple[str, ...]) -> RepositoryMutationResult:
        return self.remove_command(urls).run()

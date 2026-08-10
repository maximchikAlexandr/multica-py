from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.system import RepositoryMutationResult, RepositoryRecord
from multica_py.resources._base import BaseResource


class RepositoryResource(BaseResource):
    def list_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[Page[RepositoryRecord]]:
        return self._decoded_page_command(("repo", "list"), RepositoryRecord, options=options)

    def list(self, *, options: OperationOptions | None = None) -> Page[RepositoryRecord]:
        return self.list_command(options=options).run()

    def add_command(
        self,
        urls: tuple[str, ...],
        *,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[RepositoryMutationResult]]:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        if description is not None and len(urls) != 1:
            raise ValueError("description requires exactly one URL")
        args = ["repo", "add", *urls]
        if description is not None:
            args.extend(["--description", description])
        return self._action_decoded_command(tuple(args), RepositoryMutationResult, options=options)

    def add(
        self,
        urls: tuple[str, ...],
        *,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> ActionResult[RepositoryMutationResult]:
        return self.add_command(urls, description=description, options=options).run()

    def remove_command(
        self, urls: tuple[str, ...], *, options: OperationOptions | None = None
    ) -> Command[ActionResult[RepositoryMutationResult]]:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        return self._action_decoded_command(
            ("repo", "remove", *urls), RepositoryMutationResult, options=options
        )

    def remove(
        self, urls: tuple[str, ...], *, options: OperationOptions | None = None
    ) -> ActionResult[RepositoryMutationResult]:
        return self.remove_command(urls, options=options).run()

from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py.models.system import RepositoryMutationResult, RepositoryRecord
from multica_py.resources._base import BaseResource


class RepositoryResource(BaseResource):
    def list_command(self) -> Command[tuple[RepositoryRecord, ...]]:
        args, decode = self._plan_decode_list(("repo", "list"), RepositoryRecord)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[RepositoryRecord, ...]", results[0]),
        )

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
        plan_args, decode = self._plan_decode(tuple(args), RepositoryMutationResult)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("RepositoryMutationResult", results[0]),
        )

    def add(
        self, urls: tuple[str, ...], *, description: str | None = None
    ) -> RepositoryMutationResult:
        return self.add_command(urls, description=description).run()

    def remove_command(self, urls: tuple[str, ...]) -> Command[RepositoryMutationResult]:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        plan_args, decode = self._plan_decode(("repo", "remove", *urls), RepositoryMutationResult)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("RepositoryMutationResult", results[0]),
        )

    def remove(self, urls: tuple[str, ...]) -> RepositoryMutationResult:
        return self.remove_command(urls).run()

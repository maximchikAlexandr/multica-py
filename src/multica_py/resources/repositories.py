from __future__ import annotations

from multica_py.models.system import RepositoryMutationResult, RepositoryRecord
from multica_py.resources._base import BaseResource


class RepositoryResource(BaseResource):
    def list(self) -> tuple[RepositoryRecord, ...]:
        return self._run_json_decode_list(("repo", "list"), RepositoryRecord)

    def add(
        self, urls: tuple[str, ...], *, description: str | None = None
    ) -> RepositoryMutationResult:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        if description is not None and len(urls) != 1:
            raise ValueError("description requires exactly one URL")
        args = ["repo", "add", *urls]
        if description is not None:
            args.extend(["--description", description])
        return self._run_json_decode(tuple(args), RepositoryMutationResult)

    def remove(self, urls: tuple[str, ...]) -> RepositoryMutationResult:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain nonblank values")
        return self._run_json_decode(("repo", "remove", *urls), RepositoryMutationResult)

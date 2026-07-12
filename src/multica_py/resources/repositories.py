from __future__ import annotations

from multica_py.models.system import Repository, RepositoryCheckoutResult
from multica_py.resources._base import BaseResource


class RepositoryResource(BaseResource):
    def list(self) -> tuple[Repository, ...]:
        return self._run_json_decode_list(("repo", "list"), Repository)

    def get(self, repo_id: str) -> Repository:
        return self._run_json_decode(("repo", "get", repo_id), Repository)

    def checkout(self, repo_id: str, branch: str) -> RepositoryCheckoutResult:
        args = ("repo", "checkout", repo_id, "--branch", branch)
        return self._run_json_decode((args), RepositoryCheckoutResult)

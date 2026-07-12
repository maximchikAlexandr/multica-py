from __future__ import annotations

from multica_py.models.system import User
from multica_py.resources._base import BaseResource


class UserResource(BaseResource):
    def list(self) -> tuple[User, ...]:
        return self._run_json_decode_list(("user", "list"), User)

    def get(self, user_id: str) -> User:
        return self._run_json_decode(("user", "get", user_id), User)

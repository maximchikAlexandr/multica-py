from __future__ import annotations

from multica_py.models.system import UserProfile, UserProfileUpdate
from multica_py.resources._base import BaseResource
from multica_py.sentinels import Unset


class UserResource(BaseResource):
    def profile_get(self) -> UserProfile:
        return self._run_json_decode(("user", "profile", "get"), UserProfile)

    def profile_update(self, request: UserProfileUpdate) -> UserProfile:
        if request.description is Unset:
            raise ValueError("description must be provided")
        return self._run_json_decode(
            ("user", "profile", "update", "--description", request.description), UserProfile
        )

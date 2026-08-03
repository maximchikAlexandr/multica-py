from __future__ import annotations

from typing import overload

import msgspec

from multica_py.models.system import UserProfile, UserProfileUpdate
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.sentinels import Unset


class UserResource(BaseResource):
    def profile_get(self) -> UserProfile:
        return self._run_json_decode(("user", "profile", "get"), UserProfile)

    @overload
    def profile_update(self, request: UserProfileUpdate, /) -> UserProfile: ...
    @overload
    def profile_update(
        self, *, description: str | msgspec.UnsetType = msgspec.UNSET
    ) -> UserProfile: ...

    def profile_update(  # type: ignore[misc]
        self, request: UserProfileUpdate | None = None, /, **kwargs: object
    ) -> UserProfile:
        req = _resolve_request(request, kwargs, UserProfileUpdate)
        if req.description is Unset:
            raise ValueError("description must be provided")
        return self._run_json_decode(
            ("user", "profile", "update", "--description", req.description), UserProfile
        )

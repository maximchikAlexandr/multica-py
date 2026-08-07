from __future__ import annotations

from typing import cast, overload

import msgspec

from multica_py._internal.commands import Command
from multica_py.models.system import UserProfile, UserProfileUpdate
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.sentinels import Unset


class UserResource(BaseResource):
    def profile_get_command(self) -> Command[UserProfile]:
        return self._decoded_command(("user", "profile", "get"), UserProfile)

    def profile_get(self) -> UserProfile:
        return self.profile_get_command().run()

    @overload
    def profile_update_command(self, request: UserProfileUpdate, /) -> Command[UserProfile]: ...
    @overload
    def profile_update_command(
        self, *, description: str | None | msgspec.UnsetType = msgspec.UNSET
    ) -> Command[UserProfile]: ...

    def profile_update_command(  # type: ignore[misc]
        self, request: UserProfileUpdate | None = None, /, **kwargs: object
    ) -> Command[UserProfile]:
        req = _resolve_request(request, kwargs, UserProfileUpdate, allow_empty=True)
        if req.description is Unset:
            raise ValueError("description must be provided")
        if req.description is None:
            return self._decoded_command(("user", "profile", "update", "--clear"), UserProfile)
        args = ("user", "profile", "update", "--description", req.description)
        return self._decoded_command(args, UserProfile)

    @overload
    def profile_update(self, request: UserProfileUpdate, /) -> UserProfile: ...
    @overload
    def profile_update(
        self, *, description: str | None | msgspec.UnsetType = msgspec.UNSET
    ) -> UserProfile: ...

    def profile_update(  # type: ignore[misc]
        self, request: UserProfileUpdate | None = None, /, **kwargs: object
    ) -> UserProfile:
        return self.profile_update_command(cast("UserProfileUpdate", request), **kwargs).run()

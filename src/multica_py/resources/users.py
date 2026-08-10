from __future__ import annotations

import msgspec

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.system import UserProfile
from multica_py.resources._base import BaseResource
from multica_py.sentinels import Unset


class UserResource(BaseResource):
    def profile_get_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[UserProfile]:
        return self._decoded_command(("user", "profile", "get"), UserProfile, options=options)

    def profile_get(self, *, options: OperationOptions | None = None) -> UserProfile:
        return self.profile_get_command(options=options).run()

    def profile_update_command(
        self,
        *,
        description: str | None | msgspec.UnsetType = msgspec.UNSET,
        options: OperationOptions | None = None,
    ) -> Command[UserProfile]:
        if description is Unset:
            return self._decoded_command(("user", "profile", "get"), UserProfile, options=options)
        if description is None:
            return self._decoded_command(
                ("user", "profile", "update", "--clear"), UserProfile, options=options
            )
        args = ("user", "profile", "update", "--description", description)
        return self._decoded_command(args, UserProfile, options=options)

    def profile_update(
        self,
        *,
        description: str | None | msgspec.UnsetType = msgspec.UNSET,
        options: OperationOptions | None = None,
    ) -> UserProfile:
        return self.profile_update_command(description=description, options=options).run()

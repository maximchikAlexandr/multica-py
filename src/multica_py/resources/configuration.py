from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.models.common import ActionResult
from multica_py.resources._base import BaseResource


class ConfigurationResource(BaseResource):
    def show_command(self) -> Command[str]:
        return self._text_command(("config", "show"))

    def show(self) -> str:
        return self.show_command().run()

    def get_command(self, key: str) -> Command[str]:
        return self._text_command(("config", "get", key))

    def get(self, key: str) -> str:
        return self.get_command(key).run()

    def set_command(self, key: str, value: str) -> Command[ActionResult[None]]:
        return self._action_command(("config", "set", key, value))

    def set(self, key: str, value: str) -> ActionResult[None]:
        return self.set_command(key, value).run()

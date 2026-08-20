from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult
from multica_py.resources._base import BaseResource


class ConfigurationResource(BaseResource):
    def show_command(self, *, options: OperationOptions | None = None) -> Command[str]:
        return self._text_command(("config", "show"), options=options)

    def show(self, *, options: OperationOptions | None = None) -> str:
        return self.show_command(options=options).run()

    def get_command(self, *, options: OperationOptions | None = None) -> Command[str]:
        """Compatibility alias for :meth:`show_command`.

        Multica CLI v0.4.28 has no ``config get <key>`` command; configuration
        is exposed as the complete human-readable ``config show`` output.
        """
        return self.show_command(options=options)

    def get(self, *, options: OperationOptions | None = None) -> str:
        """Compatibility alias for :meth:`show`."""
        return self.get_command(options=options).run()

    def set_command(
        self, key: str, value: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("config", "set", key, value), options=options)

    def set(
        self, key: str, value: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.set_command(key, value, options=options).run()

from __future__ import annotations

from multica_py.resources._base import BaseResource


class ConfigurationResource(BaseResource):
    def show(self) -> str:
        return self._transport.run_text(("config", "show")).text

    def get(self, key: str) -> str:
        return self._transport.run_text(("config", "get", key)).text

    def set(self, key: str, value: str) -> None:
        self._transport.run_text(("config", "set", key, value))

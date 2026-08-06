from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import TextResult
from multica_py.resources._base import BaseResource


class ConfigurationResource(BaseResource):
    def show_command(self) -> Command[str]:
        return self._plan(
            steps=(_Step(("config", "show"), "run_text"),),
            finalize=lambda results: cast("TextResult", results[0]).text,
        )

    def show(self) -> str:
        return self.show_command().run()

    def get_command(self, key: str) -> Command[str]:
        return self._plan(
            steps=(_Step(("config", "get", key), "run_text"),),
            finalize=lambda results: cast("TextResult", results[0]).text,
        )

    def get(self, key: str) -> str:
        return self.get_command(key).run()

    def set_command(self, key: str, value: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("config", "set", key, value), "run_text"),),
            finalize=lambda results: None,
        )

    def set(self, key: str, value: str) -> None:
        self.set_command(key, value).run()

from __future__ import annotations

from unittest.mock import MagicMock

from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.resources.configuration import ConfigurationResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


class TestConfigCommands:
    def test_show_sends_config_show(self):
        t = _t()
        t.run_text.return_value = TextResult(text="val", stderr="", exit_code=0)
        ConfigurationResource(t, ClientConfig()).show()
        t.run_text.assert_called_once_with(("config", "show"))

    def test_get_sends_config_get(self):
        t = _t()
        t.run_text.return_value = TextResult(text="val", stderr="", exit_code=0)
        ConfigurationResource(t, ClientConfig()).get("key")
        t.run_text.assert_called_once_with(("config", "get", "key"))

    def test_set_sends_config_set(self):
        t = _t()
        ConfigurationResource(t, ClientConfig()).set("key", "val")
        t.run_text.assert_called_once_with(("config", "set", "key", "val"))

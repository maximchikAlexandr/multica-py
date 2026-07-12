from __future__ import annotations

from multica_py._internal.compat import check_version_from_config, parse_cli_version
from multica_py._internal.decoders import decode_json, decode_text
from multica_py.models.system import MaintenanceVersion
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class MaintenanceResource(BaseResource):
    def version(self) -> MaintenanceVersion:
        result = self._transport.run_bytes(("version", "--output", "json"))
        ver = decode_json(result.stdout, MaintenanceVersion)
        raw = decode_text(result.stdout, command=" ".join(result.argv))
        parsed = parse_cli_version(raw)
        check_version_from_config(parsed, self._config)
        return ver

    def update(self) -> ManagedProcess:
        return self._transport.spawn(("update",))

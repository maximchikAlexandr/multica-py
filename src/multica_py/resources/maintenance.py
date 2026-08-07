from __future__ import annotations

from typing import cast

import msgspec

from multica_py._internal.commands import Command, _Step
from multica_py._internal.compat import check_version_from_config, parse_cli_version
from multica_py._internal.decoders import decode_json, decode_text
from multica_py._internal.specs import RawCommandResult
from multica_py.models.system import MaintenanceVersion
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class MaintenanceResource(BaseResource):
    def version_command(self) -> Command[MaintenanceVersion]:
        config_snapshot = msgspec.structs.replace(self._config)

        def finalize(results: tuple[object, ...]) -> MaintenanceVersion:
            result = cast("RawCommandResult", results[0])
            ver = decode_json(result.stdout, MaintenanceVersion)
            raw = decode_text(result.stdout, command=" ".join(result.argv))
            parsed = parse_cli_version(raw)
            check_version_from_config(parsed, config_snapshot)
            return ver

        return self._plan(
            steps=(_Step(("version", "--output", "json"), "run_bytes"),),
            finalize=finalize,
        )

    def version(self) -> MaintenanceVersion:
        return self.version_command().run()

    def update_command(self) -> Command[ManagedProcess]:
        return self._spawn_command(("update",))

    def update(self) -> ManagedProcess:
        return self.update_command().run()

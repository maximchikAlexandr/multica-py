from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py._internal.compat import check_version_from_config, parse_cli_version
from multica_py._internal.decoders import decode_json, decode_text
from multica_py._internal.specs import RawCommandResult
from multica_py.config import OperationOptions
from multica_py.models.system import MaintenanceVersion
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class MaintenanceResource(BaseResource):
    def version_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[MaintenanceVersion]:
        config_snapshot = self._effective_config(options)

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
            options=options,
        )

    def version(self, *, options: OperationOptions | None = None) -> MaintenanceVersion:
        return self.version_command(options=options).run()

    def update_command(self, *, options: OperationOptions | None = None) -> Command[ManagedProcess]:
        return self._spawn_command(("update",), options=options)

    def update(self, *, options: OperationOptions | None = None) -> ManagedProcess:
        return self.update_command(options=options).run()

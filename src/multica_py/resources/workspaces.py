from __future__ import annotations

from multica_py.models.workspaces import Workspace, WorkspaceMember
from multica_py.resources._base import BaseResource


class WorkspaceResource(BaseResource):
    def list(self) -> tuple[Workspace, ...]:
        return self._run_json_decode_list(("workspace", "list"), Workspace)

    def get(self, workspace_id: str) -> Workspace:
        return self._run_json_decode(("workspace", "get", workspace_id), Workspace)

    def members(self, workspace_id: str) -> tuple[WorkspaceMember, ...]:
        return self._run_json_decode_list(
            ("workspace", "member", "list", workspace_id),
            WorkspaceMember,
        )

    def switch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "switch", workspace_id))

    def watch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "watch", workspace_id))

    def unwatch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "unwatch", workspace_id))

from __future__ import annotations

from multica_py._internal.argv import build_global_args
from multica_py.config import ClientConfig
from multica_py.enums import OutputMode
from multica_py.models.workspaces import Workspace, WorkspaceMember


class TestWorkspaceModels:
    def test_workspace_defaults(self):
        ws = Workspace(id="ws_1", name="test")
        assert ws.description is None

    def test_workspace_member_defaults(self):
        m = WorkspaceMember(id="u1", name="Alice")
        assert m.role is None


class TestWorkspaceArgs:
    def test_global_flags(self):
        args = build_global_args(ClientConfig(workspace_id="ws_001", server_url="https://x.com"))
        assert "--workspace-id" in args
        assert "--server-url" in args

    def test_output_mode_enum(self):
        assert OutputMode.json.value == "json"
        assert OutputMode.table.value == "table"

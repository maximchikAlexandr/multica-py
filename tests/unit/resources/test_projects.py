from __future__ import annotations

from multica_py.enums import ProjectStatus


class TestProjectModels:
    def test_project_status_enum(self):
        assert ProjectStatus.planned.value == "planned"

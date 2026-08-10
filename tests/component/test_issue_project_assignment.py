from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py.config import ClientConfig
from multica_py.resources.issues import IssueResource


@dataclass(frozen=True)
class EmptyProjectIdCase:
    method: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...]


EMPTY_PROJECT_ID_CASES = (
    EmptyProjectIdCase("create_command", (), (("title", "New issue"), ("project_id", ""))),
    EmptyProjectIdCase("update_command", ("iss_1",), (("project_id", ""),)),
)


@pytest.mark.parametrize("case", EMPTY_PROJECT_ID_CASES, ids=lambda case: case.method)
def test_issue_project_id_validation_is_consistent(case: EmptyProjectIdCase) -> None:
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        getattr(IssueResource(MagicMock(), ClientConfig()), case.method)(
            *case.args, **dict(case.kwargs)
        )

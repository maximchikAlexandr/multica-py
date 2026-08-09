from __future__ import annotations

import json
import pathlib
from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from multica_py.models.common import Page
from tests.fixtures.fake_multica import FakeMultica

pytestmark = pytest.mark.component


def test_fake_cli_direct_collection_preserves_page_contract(
    client_factory: Callable[..., MulticaClient], tmp_path: pathlib.Path
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    response = FakeMultica(responses_dir=responses_dir).build_response(
        stdout='[{"id":"agent-1","name":"Agent"}]',
        argv=("fake_multica", "agent", "list", "--output", "json"),
    )
    (responses_dir / "agent.json").write_text(json.dumps(response.to_dict()), encoding="utf-8")

    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))
    page = client.agents.list()

    assert type(page) is Page
    assert page.items[0].id == "agent-1"
    assert page.total == 1
    assert tuple(page) == page.items
    assert len(page) == 1
    assert page[0] is page.items[0]
    assert page[:] == page.items

from __future__ import annotations

import json

from multica_py.models.skills import SkillSearchResult
from multica_py.resources.skills import SkillResource


def test_search_decodes_skill_search_results() -> None:
    stdout = json.dumps(
        [
            {
                "name": "pytest",
                "url": "https://example.com/pytest",
                "source": "clawhub",
                "install_count": 42,
                "description": "testing",
            }
        ]
    ).encode()
    page = SkillResource._decode_skill_search_results(stdout, "skill search pytest --output json")
    assert len(page.items) == 1
    item = page.items[0]
    assert isinstance(item, SkillSearchResult)
    assert item.name == "pytest"
    assert item.install_count == 42

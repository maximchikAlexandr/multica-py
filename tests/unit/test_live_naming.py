from __future__ import annotations

import re

from tests.live.settings import MAX_LABEL_NAME_LEN, label_name, resource_prefix, workspace_slug


def test_workspace_slug_truncates_with_hash_suffix() -> None:
    slug = workspace_slug("x" * 80, "a")
    assert len(slug) <= 48
    assert re.search(r"-[0-9a-f]{8}$", slug)


def test_resource_prefix_truncates_with_hash_suffix() -> None:
    prefix = resource_prefix("y" * 80, "test-name")
    assert len(prefix) <= 64
    assert prefix.startswith("mpy-live-")
    assert re.search(r"-[0-9a-f]{8}$", prefix)


def test_label_name_respects_upstream_max_length() -> None:
    name = label_name("mpy-live-" + ("z" * 80), "crud")
    assert len(name) <= MAX_LABEL_NAME_LEN
    assert name.endswith("-crud")

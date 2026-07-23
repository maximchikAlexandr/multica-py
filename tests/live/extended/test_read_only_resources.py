from __future__ import annotations

import pytest

from tests.live.session import LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]


@pytest.mark.parametrize(
    ("client_attr",),
    (
        ("agents",),
        ("skills",),
        ("autopilots",),
    ),
)
def test_read_only_resource_list_decodes(
    live_session: LiveSession,
    client_attr: str,
) -> None:
    """Decode read-only list responses for extended compatibility resources."""
    items = getattr(live_session.client, client_attr).list()
    assert isinstance(items, tuple)

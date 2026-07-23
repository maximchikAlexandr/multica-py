from __future__ import annotations

from typing import Any

import pytest

from tests.live.api import LiveApiClient
from tests.live.crud_descriptors import CRUD_CASES, CrudDescriptor
from tests.live.session import LiveCase, LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]


@pytest.mark.parametrize("descriptor", CRUD_CASES, ids=[d.id for d in CRUD_CASES])
def test_crud_round_trip(
    descriptor: CrudDescriptor[Any],
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Generic 11-step CRUD round trip; resource name is always live_case.unique_name."""
    created = descriptor.create(live_session, live_case.unique_name)
    live_case.defer_cleanup(descriptor.delete, live_session, created)
    descriptor.assert_created(created)
    fetched = descriptor.get(live_session, created)
    descriptor.assert_fetched(created, fetched)
    updated = descriptor.update(live_session, fetched)
    descriptor.assert_updated(fetched, updated)
    assert live_session.api is not None
    api: LiveApiClient = live_session.api
    descriptor.assert_oracle(api, updated)
    descriptor.delete(live_session, updated)
    descriptor.assert_deleted(api, updated)

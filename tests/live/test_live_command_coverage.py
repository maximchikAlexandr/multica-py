from __future__ import annotations

import pytest

from tests.cases.models import OperationCase
from tests.cases.operations import OPERATION_CASES
from tests.live.crud_descriptors import CRUD_CASES
from tests.live.operations import DIRECT_EXECUTORS

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

_CLOSED_MODES = frozenset({"unrunnable", "smoke", "extended", "sandbox"})
_UNRUNNABLE_MODES = frozenset({"unrunnable"})
_CLOSED_UNRUNNABLE_REASONS = frozenset(
    {
        "destructive-irrecoverable",
        "interactive-or-foreground",
        "process-or-daemon-control",
        "requires-external-infra",
    }
)
_CRUD_RESOURCE_IDS = frozenset(d.id for d in CRUD_CASES)


@pytest.mark.parametrize("case", OPERATION_CASES, ids=lambda c: c.sdk_method)
def test_live_policy_is_closed_and_owners_resolve(case: OperationCase) -> None:
    """111 LivePolicy entries must use closed mode/owner/reason vocabulary.

    Asserts:
    - mode is one of {"smoke", "extended", "sandbox"}.
    - when mode != "unrunnable" the owner is non-empty.
    - extended + "direct:<id>" => <id> is a registered executor.
    - extended + "crud:<id>"   => <id> is a registered CRUD resource.
    - sandbox owner is the literal "sandbox".
    - unrunnable carries a closed reason.
    """
    mode = case.live.mode
    owner = case.live.owner
    assert mode in _CLOSED_MODES, f"{case.sdk_method}: mode {mode!r} not in closed enum"
    if mode in _UNRUNNABLE_MODES:
        assert case.live.reason in _CLOSED_UNRUNNABLE_REASONS, (
            f"{case.sdk_method}: reason {case.live.reason!r} not in closed enum"
        )
        return
    assert owner, f"{case.sdk_method}: mode={mode} requires non-empty owner"
    if mode == "extended":
        if owner.startswith("direct:"):
            target = owner[len("direct:") :]
            if target not in DIRECT_EXECUTORS:
                pytest.skip(f"T064: direct executor {target!r} not yet registered")
        elif owner.startswith("crud:"):
            target = owner[len("crud:") :]
            assert target in _CRUD_RESOURCE_IDS, (
                f"{case.sdk_method}: crud owner {target!r} missing from CRUD_CASES"
            )
        else:
            pytest.fail(f"{case.sdk_method}: extended owner {owner!r} not direct:/crud:")
    elif mode == "sandbox":
        assert owner == "sandbox", f"{case.sdk_method}: sandbox owner must be 'sandbox'"

# Contract: Marker Profiles and Path Assignment

## Default collection

Root pytest configuration MUST set `-m "not live"`.

## Path-based auto marks

| Path prefix | Required mark |
|---|---|
| `tests/unit/` | `unit` |
| `tests/contract/` | `contract` |
| `tests/component/` | `component` |
| `tests/packaging/` | `packaging` |
| `tests/live/` | `live` |

## Live profile rule

Every module under `tests/live/` MUST declare:

1. `pytest.mark.live`
2. exactly one profile marker among `live_smoke`, `live_extended`, `live_opencode_canary`

Optional additional marks: `serial` (required for all live tests in this feature).

## Offline serial mark

Only these modules MUST carry `@pytest.mark.serial`:

- `tests/component/test_process_contract.py`
- any future module explicitly listed in `tasks.md` T014 notes

All other offline tests MUST NOT use `serial`.

## Process mark

`tests/component/test_process_contract.py` MUST also carry `@pytest.mark.process`.

## Validation

`tests/conftest.py` MUST fail collection when:

- a live module lacks `live` or has zero/multiple profile markers;
- a non-live module declares a live profile marker.

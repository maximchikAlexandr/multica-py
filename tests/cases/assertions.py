from __future__ import annotations


def assert_result(result: object, expected: object) -> None:
    if expected is None and result is None:
        return
    assert result is not None
    if expected is not None:
        assert result == expected

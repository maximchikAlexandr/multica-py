from __future__ import annotations

from multica_py.enums import CompatibilityPolicy


class TestSetupEnums:
    def test_compat_policy(self):
        assert CompatibilityPolicy.strict.value == "strict"

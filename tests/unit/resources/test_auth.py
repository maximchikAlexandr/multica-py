from __future__ import annotations

from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy


class TestAuth:
    def test_compat_policy_default(self):
        config = ClientConfig()
        assert config.compatibility == CompatibilityPolicy.ignore

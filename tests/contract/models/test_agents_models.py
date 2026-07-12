from __future__ import annotations

import msgspec

import multica_py.models.agents as mod


class TestAgentsModels:
    def test_module_importable(self):
        assert mod is not None

    def test_models_are_frozen_msgspec(self):
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, msgspec.Struct):
                assert obj.__struct_config__.frozen, f"{name} in agents is not frozen"

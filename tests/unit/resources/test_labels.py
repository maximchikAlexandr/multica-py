from __future__ import annotations

from multica_py.models.labels import Label


class TestLabelModels:
    def test_label_defaults(self):
        lbl = Label(id="lbl_1", name="bug")
        assert lbl.color is None

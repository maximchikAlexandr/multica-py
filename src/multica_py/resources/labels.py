from __future__ import annotations

from multica_py.models.labels import Label
from multica_py.resources._base import BaseResource


class LabelResource(BaseResource):
    def list(self) -> tuple[Label, ...]:
        return self._run_json_decode_list(("label", "list"), Label)

    def get(self, label_id: str) -> Label:
        return self._run_json_decode(("label", "get", label_id), Label)

    def create(self, name: str, color: str | None = None) -> Label:
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        return self._run_json_decode(tuple(args), Label)

    def update(self, label_id: str, name: str | None = None, color: str | None = None) -> Label:
        args = ["label", "update", label_id]
        if name is not None:
            args.extend(["--name", name])
        if color is not None:
            args.extend(["--color", color])
        return self._run_json_decode(tuple(args), Label)

    def delete(self, label_id: str) -> None:
        self._transport.run_text(("label", "delete", label_id))

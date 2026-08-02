from __future__ import annotations

from typing import TYPE_CHECKING

from multica_py.models import ResourceEntity
from multica_py.models.labels import LabelData
from multica_py.resources._base import BaseResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


class Label(ResourceEntity[LabelData]):
    def __init__(self, data: LabelData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def color(self) -> str | None:
        return self._data.color


class LabelResource(BaseResource):
    def _bind(self, label: LabelData) -> Label:
        return Label(label, client=self._client)

    def list(self) -> tuple[Label, ...]:
        return tuple(
            self._bind(item) for item in self._run_json_decode_list(("label", "list"), LabelData)
        )

    def get(self, label_id: str) -> Label:
        return self._bind(self._run_json_decode(("label", "get", label_id), LabelData))

    def create(self, name: str, color: str | None = None) -> Label:
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        return self._bind(self._run_json_decode(tuple(args), LabelData))

    def update(self, label_id: str, name: str | None = None, color: str | None = None) -> Label:
        args = ["label", "update", label_id]
        if name is not None:
            args.extend(["--name", name])
        if color is not None:
            args.extend(["--color", color])
        return self._bind(self._run_json_decode(tuple(args), LabelData))

    def delete(self, label_id: str) -> None:
        self._transport.run_text(("label", "delete", label_id))

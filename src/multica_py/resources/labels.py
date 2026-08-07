from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.models._bound import _BoundEntity
from multica_py.resources._base import BaseResource


class Label(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    color: str | None = None

    _PUBLIC_FIELDS = ("id", "name", "color")


class LabelResource(BaseResource):
    def list_command(self) -> Command[tuple[Label, ...]]:
        return self._decoded_list_command(("label", "list"), Label)._map(
            lambda items: tuple(item._with_client(self._client) for item in items)
        )

    def list(self) -> tuple[Label, ...]:
        return self.list_command().run()

    def get_command(self, label_id: str) -> Command[Label]:
        return self._decoded_command(("label", "get", label_id), Label)._map(
            lambda label: label._with_client(self._client)
        )

    def get(self, label_id: str) -> Label:
        return self.get_command(label_id).run()

    def create_command(self, name: str, color: str | None = None) -> Command[Label]:
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        return self._decoded_command(tuple(args), Label)._map(
            lambda label: label._with_client(self._client)
        )

    def create(self, name: str, color: str | None = None) -> Label:
        return self.create_command(name, color).run()

    def update_command(
        self, label_id: str, name: str | None = None, color: str | None = None
    ) -> Command[Label]:
        args = ["label", "update", label_id]
        if name is not None:
            args.extend(["--name", name])
        if color is not None:
            args.extend(["--color", color])
        return self._decoded_command(tuple(args), Label)._map(
            lambda label: label._with_client(self._client)
        )

    def update(self, label_id: str, name: str | None = None, color: str | None = None) -> Label:
        return self.update_command(label_id, name, color).run()

    def delete_command(self, label_id: str) -> Command[None]:
        return self._none_command(("label", "delete", label_id))

    def delete(self, label_id: str) -> None:
        self.delete_command(label_id).run()

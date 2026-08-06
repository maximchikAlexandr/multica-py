from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py.models._bound import _BoundEntity
from multica_py.resources._base import BaseResource


class Label(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    color: str | None = None

    _PUBLIC_FIELDS = ("id", "name", "color")


class LabelResource(BaseResource):
    def list_command(self) -> Command[tuple[Label, ...]]:
        args, decode = self._plan_decode_list(("label", "list"), Label)

        def finalize(results: tuple[object, ...]) -> tuple[Label, ...]:
            items = cast("tuple[Label, ...]", results[0])
            return tuple(item._with_client(self._client) for item in items)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self) -> tuple[Label, ...]:
        return self.list_command().run()

    def get_command(self, label_id: str) -> Command[Label]:
        args, decode = self._plan_decode(("label", "get", label_id), Label)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Label", results[0])._with_client(self._client),
        )

    def get(self, label_id: str) -> Label:
        return self.get_command(label_id).run()

    def create_command(self, name: str, color: str | None = None) -> Command[Label]:
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        plan_args, decode = self._plan_decode(tuple(args), Label)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Label", results[0])._with_client(self._client),
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
        plan_args, decode = self._plan_decode(tuple(args), Label)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Label", results[0])._with_client(self._client),
        )

    def update(self, label_id: str, name: str | None = None, color: str | None = None) -> Label:
        return self.update_command(label_id, name, color).run()

    def delete_command(self, label_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("label", "delete", label_id), "run_text"),),
            finalize=lambda results: None,
        )

    def delete(self, label_id: str) -> None:
        self.delete_command(label_id).run()

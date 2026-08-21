from __future__ import annotations

import copy
import threading
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, cast

from multica_py._internal.commands import (
    Command,
    _cached_result_command,
    _coalesced_command,
    _result_field_argument,
    _sequential_command,
)
from multica_py.entities._base import _BoundEntity
from multica_py.exceptions import UnloadedReferenceError
from multica_py.models.issue_activity import CommentCursor
from multica_py.models.issues import IssueChildStageGroup

if TYPE_CHECKING:
    from multica_py.client import MulticaClient
    from multica_py.entities.issues import Issue

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


class _GenerationUnset:
    __slots__ = ()


_GENERATION_UNSET = _GenerationUnset()

_MAX_RELATION_PAGES = 1_000
_MAX_RELATION_ITEMS = 100_000

__all__ = (
    "CursorLazyCollection",
    "CursorPage",
    "LazyCollection",
    "LazyMapping",
    "LazyRef",
    "OffsetLazyCollection",
    "OffsetPage",
    "RelationMetadata",
)


@dataclass(frozen=True, slots=True)
class RelationMetadata:
    total: int | None = None
    child_stages: tuple[IssueChildStageGroup, ...] = ()
    unstaged: tuple[Issue, ...] = ()


@dataclass(frozen=True, slots=True)
class _RelationLoad(Generic[T]):
    items: tuple[T, ...]
    metadata: RelationMetadata


@dataclass(frozen=True, slots=True)
class OffsetPage(Generic[T]):
    items: tuple[T, ...]
    total: int
    limit: int
    offset: int
    has_more: bool

    @property
    def next_offset(self) -> int | None:
        if not self.has_more:
            return None
        return self.offset + len(self.items)


@dataclass(frozen=True, slots=True)
class CursorPage(Generic[T]):
    items: tuple[T, ...]
    next_cursor: CommentCursor | None = None


class LazyLoadable(Protocol[T_co]):
    @property
    def loaded(self) -> bool: ...

    def all(self) -> T_co: ...


@dataclass(slots=True)
class _GenerationSuccess(Generic[R]):
    value: R
    waiters: int


@dataclass(slots=True)
class _GenerationFailure:
    error: BaseException
    waiters: int


def _clone_exception(error: BaseException) -> BaseException:
    clone = copy.copy(error)
    clone.__cause__ = error.__cause__
    clone.__context__ = error.__context__
    return clone


class _GenerationState(Generic[R]):
    """Private synchronization state shared by lazy relation containers."""

    _UNLOADED = 0
    _LOADING = 1
    _LOADED = 2

    def __init__(self, empty: R, *, initial: R | _GenerationUnset = _GENERATION_UNSET) -> None:
        self._condition = threading.Condition()
        has_initial = initial is not _GENERATION_UNSET
        self._state = self._LOADED if has_initial else self._UNLOADED
        self._value = empty if not has_initial else cast("R", initial)
        self._empty = empty
        self._generation = 0
        self._outcomes: dict[int, _GenerationSuccess[R] | _GenerationFailure] = {}
        self._waiters: dict[int, int] = {}

    @property
    def loaded(self) -> bool:
        with self._condition:
            return self._state == self._LOADED

    @property
    def value(self) -> R:
        with self._condition:
            return self._value

    @property
    def condition(self) -> threading.Condition:
        return self._condition

    @property
    def waiters(self) -> Mapping[int, int]:
        return self._waiters

    @property
    def outcomes(self) -> Mapping[int, object]:
        return self._outcomes

    def run(self, *, force: bool, load: Callable[[], R]) -> R:
        with self._condition:
            if not force and self._state == self._LOADED:
                return self._value
            if self._state == self._LOADING:
                waited_generation = self._generation
                self._waiters[waited_generation] = self._waiters.get(waited_generation, 0) + 1
                while self._state == self._LOADING and self._generation == waited_generation:
                    self._condition.wait()
                return self._consume_outcome(waited_generation)

            previous_value = self._value
            previous_loaded = self._state == self._LOADED
            self._state = self._LOADING
            self._generation += 1
            generation = self._generation
            self._waiters[generation] = 0

        try:
            loaded = load()
        except BaseException as error:
            with self._condition:
                waiters = self._waiters.pop(generation)
                if waiters:
                    self._outcomes[generation] = _GenerationFailure(error=error, waiters=waiters)
                self._value = previous_value
                self._state = self._LOADED if previous_loaded else self._UNLOADED
                self._condition.notify_all()
            raise

        with self._condition:
            self._value = loaded
            self._state = self._LOADED
            waiters = self._waiters.pop(generation)
            if waiters:
                self._outcomes[generation] = _GenerationSuccess(value=loaded, waiters=waiters)
            self._condition.notify_all()
            return loaded

    def reserve(self) -> int | None:
        """Reserve an unloaded generation for a singular prefetch fan-out.

        A pre-existing load owns its generation and is deliberately not
        replaced: the fan-out must never publish over a destination operation
        that won the race.  An unloaded state gets an exclusive token that
        concurrent readers can join through :meth:`run`.
        """
        with self._condition:
            if self._state != self._UNLOADED:
                return None
            self._state = self._LOADING
            self._generation += 1
            generation = self._generation
            self._waiters[generation] = 0
            return generation

    def run_reserved(self, generation: int, load: Callable[[], R]) -> R:
        """Execute the owner operation for a previously reserved generation."""
        with self._condition:
            if self._state != self._LOADING or self._generation != generation:
                return self._value

        return load()

    def publish_reserved(self, generation: int, value: R) -> bool:
        """Publish only while the exact reserved destination generation lives."""
        with self._condition:
            if self._state != self._LOADING or self._generation != generation:
                return False
            self._value = value
            self._state = self._LOADED
            waiters = self._waiters.pop(generation)
            if waiters:
                self._outcomes[generation] = _GenerationSuccess(value=value, waiters=waiters)
            self._condition.notify_all()
            return True

    def fail_reserved(self, generation: int, error: Exception) -> bool:
        with self._condition:
            if self._state != self._LOADING or self._generation != generation:
                return False
            waiters = self._waiters.pop(generation)
            if waiters:
                self._outcomes[generation] = _GenerationFailure(error=error, waiters=waiters)
            self._value = self._empty
            self._state = self._UNLOADED
            self._condition.notify_all()
            return True

    def _consume_outcome(self, generation: int) -> R:
        outcome = self._outcomes[generation]
        outcome.waiters -= 1
        if outcome.waiters == 0:
            del self._outcomes[generation]
        if isinstance(outcome, _GenerationFailure):
            raise _clone_exception(outcome.error)
        return outcome.value

    def invalidate(self) -> None:
        with self._condition:
            while self._state == self._LOADING:
                self._condition.wait()
            self._state = self._UNLOADED
            self._value = self._empty
            self._condition.notify_all()


class _OffsetLoader(Protocol[T]):
    def __call__(self, *, limit: int | None, offset: int) -> OffsetPage[T]: ...


class _CursorLoader(Protocol[T]):
    def __call__(self, *, cursor: CommentCursor | None) -> CursorPage[T]: ...


class LazyRef(Generic[T_co]):
    """A passive, explicitly loaded singular relation."""

    def __init__(
        self,
        *,
        command_loader: Callable[[], Command[T_co]],
        initial: T_co | _GenerationUnset = _GENERATION_UNSET,
        entity_type: str = "Reference",
        entity_id: str = "unknown",
        relation_name: str = "reference",
        _prefetch_target: Callable[[], tuple[str, str | None] | None] | None = None,
        _origin_client: object | None = None,
    ) -> None:
        if not callable(command_loader):
            raise TypeError("command_loader is required for LazyRef")
        self._command_loader = command_loader
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._relation_name = relation_name
        self._prefetch_target = _prefetch_target
        self._origin_client = _origin_client
        self._generation_state: _GenerationState[T_co] = _GenerationState(
            cast("T_co", None), initial=initial
        )

    @property
    def loaded(self) -> bool:
        return self._generation_state.loaded

    @property
    def value(self) -> T_co:
        if not self.loaded:
            raise UnloadedReferenceError(self._entity_type, self._entity_id, self._relation_name)
        return self._generation_state.value

    def _run_command(self, command: Command[T_co], *, force: bool) -> T_co:
        return self._generation_state.run(force=force, load=command.run)

    def _command(self) -> Command[T_co]:
        return self._command_loader()

    def get(self) -> T_co:
        if self.loaded:
            return self._generation_state.value
        return self.get_command().run()

    def get_command(self) -> Command[T_co]:
        command = self._command()
        if self.loaded:
            return _cached_result_command(command, lambda: self._generation_state.value)
        return _coalesced_command(
            command,
            lambda: self._run_command(command, force=False),
        )

    def refresh(self) -> T_co:
        if self.loaded and self._generation_state.value is None:
            return self._generation_state.value
        return self.refresh_command().run()

    def refresh_command(self) -> Command[T_co]:
        command = self._command()
        if self.loaded and self._generation_state.value is None:
            return _cached_result_command(command, lambda: self._generation_state.value)
        return _coalesced_command(
            command,
            lambda: self._run_command(command, force=True),
        )

    def invalidate(self) -> None:
        self._generation_state.invalidate()

    def _prefetch_key(self) -> tuple[object, ...]:
        prefetch_target = self._prefetch_target
        if prefetch_target is None:
            return ("lazy-ref-error", id(self))
        try:
            target = prefetch_target()
        except Exception:
            return ("lazy-ref-error", id(self))
        if target is None:
            return ("lazy-ref-error", id(self))
        target_type, target_id = target
        if not target_id:
            return ("lazy-ref-error", id(self))
        client = self._origin_client
        if client is None:
            return ("lazy-ref-error", id(self))
        scope_key = cast(
            "Callable[[str, str], tuple[object, ...]]",
            getattr(client, "_singular_scope_key"),
        )
        return scope_key(target_type, target_id)

    def _prefetch_reserve(self) -> int | None:
        return self._generation_state.reserve()

    def _prefetch_load(self, generation: int | None) -> T_co:
        if generation is None:
            return self.get()
        return self._generation_state.run_reserved(generation, self._command().run)

    def _prefetch_publish(self, generation: int, value: object) -> bool:
        published = value
        if isinstance(value, _BoundEntity):
            client = cast("MulticaClient | None", self._origin_client)
            published = value._clone_for_client(client)
        return self._generation_state.publish_reserved(generation, cast("T_co", published))

    def _prefetch_fail(self, generation: int, error: Exception) -> bool:
        return self._generation_state.fail_reserved(generation, error)


def _pagination_error(relation_name: str, reason: str) -> Exception:
    from multica_py.exceptions import RelationPaginationError

    return RelationPaginationError(relation_name, reason)


class LazyCollection(Collection[T], Generic[T]):
    """A per-entity lazy relation with a retryable, coalesced load attempt."""

    def __init__(
        self,
        loader: Callable[[], Iterable[T] | _RelationLoad[T]],
        *,
        metadata: RelationMetadata | None = None,
        initial: Iterable[T] | None = None,
        command_loader: Callable[[], Command[tuple[T, ...] | _RelationLoad[T]]] | None = None,
    ) -> None:
        self._loader = loader
        self._command_loader = command_loader
        relation_metadata = metadata if metadata is not None else RelationMetadata()
        empty: _RelationLoad[T] = _RelationLoad((), relation_metadata)
        snapshot: _RelationLoad[T] | None = (
            None if initial is None else _RelationLoad(tuple(initial), relation_metadata)
        )
        self._generation_state: _GenerationState[_RelationLoad[T]] = (
            _GenerationState(empty)
            if snapshot is None
            else _GenerationState(empty, initial=snapshot)
        )

    @property
    def loaded(self) -> bool:
        return self._generation_state.loaded

    @property
    def metadata(self) -> RelationMetadata:
        return self._generation_state.value.metadata

    def _load_complete(self) -> _RelationLoad[T]:
        loaded = self._loader()
        if isinstance(loaded, _RelationLoad):
            return loaded
        return _RelationLoad(tuple(loaded), self.metadata)

    def _run_load(self, *, force: bool) -> tuple[T, ...]:
        return self._generation_state.run(force=force, load=self._load_complete).items

    def _run_command(
        self,
        command: Command[tuple[T, ...] | _RelationLoad[T]],
        *,
        force: bool,
    ) -> tuple[T, ...]:
        def load() -> _RelationLoad[T]:
            result = command.run()
            if isinstance(result, _RelationLoad):
                return result
            return _RelationLoad(result, self.metadata)

        return self._generation_state.run(force=force, load=load).items

    def all(self) -> tuple[T, ...]:
        if self._command_loader is not None:
            return self.all_command().run()
        return self._run_load(force=False)

    def refresh(self) -> tuple[T, ...]:
        if self._command_loader is not None:
            return self.refresh_command().run()
        return self._run_load(force=True)

    def all_command(self) -> Command[tuple[T, ...]]:
        if self._command_loader is None:
            raise RuntimeError("relation has no command loader")
        command = self._command_loader()
        if self.loaded:
            return _cached_result_command(command, self._cached_value)
        return _coalesced_command(
            command,
            lambda: self._run_command(command, force=False),
            finalize=lambda value: value.items if isinstance(value, _RelationLoad) else value,
        )

    def refresh_command(self) -> Command[tuple[T, ...]]:
        if self._command_loader is None:
            raise RuntimeError("relation has no command loader")
        command = self._command_loader()
        return _coalesced_command(
            command,
            lambda: self._run_command(command, force=True),
            finalize=lambda value: value.items if isinstance(value, _RelationLoad) else value,
        )

    def _cached_value(self) -> tuple[T, ...]:
        return self._generation_state.value.items

    def invalidate(self) -> None:
        self._generation_state.invalidate()

    def __iter__(self) -> Iterator[T]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self.all())

    def __contains__(self, item: object) -> bool:
        return item in self.all()


class OffsetLazyCollection(LazyCollection[T], Generic[T]):
    def __init__(
        self,
        loader: _OffsetLoader[T],
        *,
        default_limit: int = 50,
        command_loader: Callable[[], Command[tuple[T, ...] | _RelationLoad[T]]] | None = None,
        page_command_loader: Callable[[int | None, int], Command[OffsetPage[T]]] | None = None,
    ) -> None:
        self._page_loader = loader
        self._default_limit = default_limit
        self._page_command_loader = page_command_loader
        super().__init__(self._load_pages, command_loader=command_loader)

    def page(self, *, limit: int | None = None, offset: int = 0) -> OffsetPage[T]:
        return self._page_loader(limit=limit, offset=offset)

    def page_command(self, *, limit: int | None = None, offset: int = 0) -> Command[OffsetPage[T]]:
        if self._page_command_loader is None:
            raise RuntimeError("relation has no page command loader")
        return self._page_command_loader(limit, offset)

    def all(self) -> tuple[T, ...]:
        if self._command_loader is not None or self._page_command_loader is not None:
            return self.all_command().run()
        return self._run_load(force=False)

    def refresh(self) -> tuple[T, ...]:
        if self._command_loader is not None or self._page_command_loader is not None:
            return self.refresh_command().run()
        return self._run_load(force=True)

    def all_command(self) -> Command[tuple[T, ...]]:
        if self._command_loader is not None:
            return super().all_command()
        return self._pagination_command(force=False)

    def refresh_command(self) -> Command[tuple[T, ...]]:
        if self._command_loader is not None:
            return super().refresh_command()
        return self._pagination_command(force=True)

    def _pagination_command(self, *, force: bool) -> Command[tuple[T, ...]]:
        if self._page_command_loader is None:
            raise RuntimeError("relation has no page command loader")
        first_command = self.page_command(limit=self._default_limit, offset=0)
        if self.loaded and not force:
            return _cached_result_command(first_command, self._cached_value)
        if not first_command.commands:
            return _coalesced_command(
                first_command,
                lambda: self._run_load(force=force),
            )
        try:
            template = _result_field_argument(
                first_command,
                flag="--offset",
                field="next_offset",
                alias="page",
                require_existing=True,
            )
        except ValueError as error:
            raise RuntimeError("offset page command has no --offset argument") from error

        def gate(index: int, results: tuple[object, ...]) -> bool:
            if index == 0 or not results:
                return True
            pages = tuple(cast("OffsetPage[T]", result) for result in results)
            if len(pages) >= _MAX_RELATION_PAGES or len({page.offset for page in pages}) != len(
                pages
            ):
                raise _pagination_error("OffsetLazyCollection", "repeated_offset")
            if sum(len(page.items) for page in pages) > _MAX_RELATION_ITEMS:
                raise _pagination_error("OffsetLazyCollection", "repeated_offset")
            page = pages[-1]
            if page.has_more and not page.items:
                raise _pagination_error("OffsetLazyCollection", "empty_page")
            return page.has_more

        def continuation(index: int, results: tuple[object, ...]) -> bool:
            if index == 0 or not results:
                return False
            return cast("OffsetPage[T]", results[-1]).has_more

        def finalize(results: tuple[object, ...]) -> _RelationLoad[T]:
            pages = tuple(cast("OffsetPage[T]", result) for result in results)
            return _RelationLoad(
                tuple(item for page in pages for item in page.items),
                RelationMetadata(total=pages[-1].total if pages else None),
            )

        composite = _sequential_command(
            first_command,
            template,
            gate=gate,
            continuation=continuation,
            finalize=finalize,
        )
        return _coalesced_command(
            composite,
            lambda: self._run_command(composite, force=force),
            finalize=lambda value: value.items if isinstance(value, _RelationLoad) else value,
        )

    def _load_pages(self) -> _RelationLoad[T]:
        from multica_py.exceptions import RelationPaginationError

        items: list[T] = []
        offset = 0
        seen_offsets: set[int] = set()
        total: int | None = None
        while True:
            if len(seen_offsets) >= _MAX_RELATION_PAGES:
                raise RelationPaginationError(type(self).__name__, "repeated_offset")
            if offset in seen_offsets:
                raise RelationPaginationError(type(self).__name__, "repeated_offset")
            seen_offsets.add(offset)
            page = self._page_loader(limit=self._default_limit, offset=offset)
            total = page.total
            items.extend(page.items)
            if len(items) > _MAX_RELATION_ITEMS:
                raise RelationPaginationError(type(self).__name__, "repeated_offset")
            if not page.has_more:
                break
            if not page.items:
                raise RelationPaginationError(type(self).__name__, "empty_page")
            offset += len(page.items)
        return _RelationLoad(tuple(items), RelationMetadata(total=total))


class CursorLazyCollection(LazyCollection[T], Generic[T]):
    def __init__(
        self,
        loader: _CursorLoader[T],
        *,
        initial_cursor: CommentCursor | None = None,
        page_command_loader: Callable[[CommentCursor | None], Command[CursorPage[T]]] | None = None,
    ) -> None:
        self._page_loader = loader
        self._initial_cursor = initial_cursor
        self._page_command_loader = page_command_loader
        super().__init__(self._load_pages)

    def page(self, *, cursor: CommentCursor | None = None) -> CursorPage[T]:
        return self._page_loader(cursor=self._initial_cursor if cursor is None else cursor)

    def page_command(self, *, cursor: CommentCursor | None = None) -> Command[CursorPage[T]]:
        if self._page_command_loader is None:
            raise RuntimeError("relation has no page command loader")
        effective_cursor = self._initial_cursor if cursor is None else cursor
        return self._page_command_loader(effective_cursor)

    def all(self) -> tuple[T, ...]:
        if self._page_command_loader is not None:
            return self.all_command().run()
        return self._run_load(force=False)

    def refresh(self) -> tuple[T, ...]:
        if self._page_command_loader is not None:
            return self.refresh_command().run()
        return self._run_load(force=True)

    def all_command(self) -> Command[tuple[T, ...]]:
        return self._cursor_command(force=False)

    def refresh_command(self) -> Command[tuple[T, ...]]:
        return self._cursor_command(force=True)

    def _cursor_command(self, *, force: bool) -> Command[tuple[T, ...]]:
        if self._page_command_loader is None:
            raise RuntimeError("relation has no page command loader")
        first_command = self.page_command(cursor=self._initial_cursor)
        if self.loaded and not force:
            return _cached_result_command(first_command, self._cached_value)
        if not first_command.commands:
            return _coalesced_command(
                first_command,
                lambda: self._run_load(force=force),
            )
        template = _result_field_argument(
            first_command,
            flag="--before",
            field="next_cursor.before",
            alias="page",
        )
        template = _result_field_argument(
            template,
            flag="--before-id",
            field="next_cursor.before_id",
            alias="page",
        )

        def gate(index: int, results: tuple[object, ...]) -> bool:
            if index == 0 or not results:
                return True
            pages = tuple(cast("CursorPage[T]", result) for result in results)
            if len(pages) >= _MAX_RELATION_PAGES:
                raise _pagination_error("CursorLazyCollection", "repeated_cursor")
            if sum(len(page.items) for page in pages) > _MAX_RELATION_ITEMS:
                raise _pagination_error("CursorLazyCollection", "repeated_cursor")
            used_cursors: set[CommentCursor | None] = {self._initial_cursor}
            for page in pages[:-1]:
                if page.next_cursor is not None:
                    used_cursors.add(page.next_cursor)
            page = pages[-1]
            if page.next_cursor is None:
                return False
            if not page.items:
                raise _pagination_error("CursorLazyCollection", "empty_page")
            if page.next_cursor in used_cursors:
                raise _pagination_error("CursorLazyCollection", "repeated_cursor")
            return True

        def continuation(index: int, results: tuple[object, ...]) -> bool:
            if index == 0 or not results:
                return False
            return cast("CursorPage[T]", results[-1]).next_cursor is not None

        def finalize(results: tuple[object, ...]) -> _RelationLoad[T]:
            pages = tuple(cast("CursorPage[T]", result) for result in results)
            return _RelationLoad(
                tuple(item for page in pages for item in page.items), RelationMetadata()
            )

        composite = _sequential_command(
            first_command,
            template,
            gate=gate,
            continuation=continuation,
            finalize=finalize,
        )
        return _coalesced_command(
            composite,
            lambda: self._run_command(composite, force=force),
            finalize=lambda value: value.items if isinstance(value, _RelationLoad) else value,
        )

    def _load_pages(self) -> tuple[T, ...]:
        from multica_py.exceptions import RelationPaginationError

        items: list[T] = []
        cursor = self._initial_cursor
        seen: set[CommentCursor] = set()
        while True:
            if len(seen) >= _MAX_RELATION_PAGES:
                raise RelationPaginationError(type(self).__name__, "repeated_cursor")
            page = self._page_loader(cursor=cursor)
            items.extend(page.items)
            if len(items) > _MAX_RELATION_ITEMS:
                raise RelationPaginationError(type(self).__name__, "repeated_cursor")
            next_cursor = page.next_cursor
            if next_cursor is None:
                return tuple(items)
            if not page.items:
                raise RelationPaginationError(type(self).__name__, "empty_page")
            if next_cursor == cursor or next_cursor in seen:
                raise RelationPaginationError(type(self).__name__, "repeated_cursor")
            seen.add(next_cursor)
            cursor = next_cursor


class LazyMapping(Mapping[K, V], Generic[K, V]):
    def __init__(
        self,
        loader: Callable[[], Mapping[K, V]],
        *,
        command_loader: Callable[[], Command[Mapping[K, V]]] | None = None,
    ) -> None:
        self._loader = loader
        self._command_loader = command_loader
        empty_values: dict[K, V] = {}
        empty: Mapping[K, V] = MappingProxyType(empty_values)
        self._generation_state: _GenerationState[Mapping[K, V]] = _GenerationState(empty)

    @property
    def loaded(self) -> bool:
        return self._generation_state.loaded

    def _run_load(self, *, force: bool) -> Mapping[K, V]:
        def load() -> Mapping[K, V]:
            values: dict[K, V] = dict(self._loader())
            return MappingProxyType(values)

        return self._generation_state.run(
            force=force,
            load=load,
        )

    def all(self) -> Mapping[K, V]:
        if self._command_loader is not None:
            return self.all_command().run()
        return self._run_load(force=False)

    def refresh(self) -> Mapping[K, V]:
        if self._command_loader is not None:
            return self.refresh_command().run()
        return self._run_load(force=True)

    def _run_command(self, command: Command[Mapping[K, V]], *, force: bool) -> Mapping[K, V]:
        def load() -> Mapping[K, V]:
            values: dict[K, V] = dict(command.run())
            return MappingProxyType(values)

        return self._generation_state.run(
            force=force,
            load=load,
        )

    def all_command(self) -> Command[Mapping[K, V]]:
        if self._command_loader is None:
            raise RuntimeError("mapping has no command loader")
        command = self._command_loader()
        if self.loaded:
            return _cached_result_command(command, self._cached_value)
        return _coalesced_command(
            command,
            lambda: self._run_command(command, force=False),
        )

    def refresh_command(self) -> Command[Mapping[K, V]]:
        if self._command_loader is None:
            raise RuntimeError("mapping has no command loader")
        command = self._command_loader()
        return _coalesced_command(command, lambda: self._run_command(command, force=True))

    def _cached_value(self) -> Mapping[K, V]:
        return self._generation_state.value

    def invalidate(self) -> None:
        self._generation_state.invalidate()

    def __getitem__(self, key: K) -> V:
        return self.all()[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self.all())

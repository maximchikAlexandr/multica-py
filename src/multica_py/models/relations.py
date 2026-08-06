from __future__ import annotations

import threading
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

from multica_py.models.issue_activity import CommentCursor
from multica_py.models.issues import IssueChildStageGroup

if TYPE_CHECKING:
    from multica_py.resources.issues import Issue

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")

_MAX_RELATION_PAGES = 1_000
_MAX_RELATION_ITEMS = 100_000

__all__ = (
    "CursorLazyCollection",
    "CursorPage",
    "LazyCollection",
    "LazyMapping",
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
    error: Exception
    waiters: int


class _OffsetLoader(Protocol[T]):
    def __call__(self, *, limit: int | None, offset: int) -> OffsetPage[T]: ...


class _CursorLoader(Protocol[T]):
    def __call__(self, *, cursor: CommentCursor | None) -> CursorPage[T]: ...


class LazyCollection(Collection[T], Generic[T]):
    """A per-entity lazy relation with a retryable, coalesced load attempt."""

    _UNLOADED = 0
    _LOADING = 1
    _LOADED = 2

    def __init__(
        self,
        loader: Callable[[], Iterable[T] | _RelationLoad[T]],
        *,
        metadata: RelationMetadata | None = None,
        initial: Iterable[T] | None = None,
    ) -> None:
        self._loader = loader
        self._condition = threading.Condition()
        self._state = self._LOADED if initial is not None else self._UNLOADED
        self._value = tuple(initial) if initial is not None else ()
        self._metadata = metadata or RelationMetadata()
        self._generation = 0
        self._outcomes: dict[int, _GenerationSuccess[tuple[T, ...]] | _GenerationFailure] = {}
        self._waiters: dict[int, int] = {}

    @property
    def loaded(self) -> bool:
        with self._condition:
            return self._state == self._LOADED

    @property
    def metadata(self) -> RelationMetadata:
        with self._condition:
            return self._metadata

    def _load_complete(self) -> _RelationLoad[T]:
        loaded = self._loader()
        if isinstance(loaded, _RelationLoad):
            return loaded
        return _RelationLoad(tuple(loaded), self._metadata)

    def _run_load(self, *, force: bool) -> tuple[T, ...]:
        with self._condition:
            if not force and self._state == self._LOADED:
                return self._value
            if self._state == self._LOADING:
                waited_generation = self._generation
                # Register before releasing the condition.  This lets an older
                # waiter retrieve its exact generation outcome after a later
                # caller has already started another generation.
                self._waiters[waited_generation] = self._waiters.get(waited_generation, 0) + 1
                while self._state == self._LOADING and self._generation == waited_generation:
                    self._condition.wait()
                return self._consume_outcome(waited_generation)
            previous_state = self._state
            previous_value = self._value
            previous_metadata = self._metadata
            self._state = self._LOADING
            self._generation += 1
            generation = self._generation
            self._waiters[generation] = 0
        try:
            loaded = self._load_complete()
        except Exception as error:
            with self._condition:
                waiters = self._waiters.pop(generation)
                if waiters:
                    self._outcomes[generation] = _GenerationFailure(error=error, waiters=waiters)
                if previous_state == self._LOADED:
                    self._state = self._LOADED
                    self._value = previous_value
                    self._metadata = previous_metadata
                else:
                    self._state = self._UNLOADED
                self._condition.notify_all()
            raise
        with self._condition:
            self._value = loaded.items
            self._metadata = loaded.metadata
            self._state = self._LOADED
            waiters = self._waiters.pop(generation)
            if waiters:
                self._outcomes[generation] = _GenerationSuccess(value=self._value, waiters=waiters)
            self._condition.notify_all()
            return self._value

    def _consume_outcome(self, generation: int) -> tuple[T, ...]:
        outcome = self._outcomes[generation]
        outcome.waiters -= 1
        if outcome.waiters == 0:
            del self._outcomes[generation]
        if isinstance(outcome, _GenerationFailure):
            raise outcome.error
        return outcome.value

    def all(self) -> tuple[T, ...]:
        return self._run_load(force=False)

    def refresh(self) -> tuple[T, ...]:
        return self._run_load(force=True)

    def invalidate(self) -> None:
        with self._condition:
            while self._state == self._LOADING:
                self._condition.wait()
            self._state = self._UNLOADED
            self._value = ()
            self._metadata = RelationMetadata()

    def __iter__(self) -> Iterator[T]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self.all())

    def __contains__(self, item: object) -> bool:
        return item in self.all()


class OffsetLazyCollection(LazyCollection[T], Generic[T]):
    def __init__(self, loader: _OffsetLoader[T], *, default_limit: int = 50) -> None:
        self._page_loader = loader
        self._default_limit = default_limit
        super().__init__(self._load_pages)

    def page(self, *, limit: int | None = None, offset: int = 0) -> OffsetPage[T]:
        return self._page_loader(limit=limit, offset=offset)

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
    ) -> None:
        self._page_loader = loader
        self._initial_cursor = initial_cursor
        super().__init__(self._load_pages)

    def page(self, *, cursor: CommentCursor | None = None) -> CursorPage[T]:
        return self._page_loader(cursor=self._initial_cursor if cursor is None else cursor)

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
    _UNLOADED = 0
    _LOADING = 1
    _LOADED = 2

    def __init__(self, loader: Callable[[], Mapping[K, V]]) -> None:
        self._loader = loader
        self._condition = threading.Condition()
        self._state = self._UNLOADED
        self._value: Mapping[K, V] = MappingProxyType({})
        self._generation = 0
        self._outcomes: dict[int, _GenerationSuccess[Mapping[K, V]] | _GenerationFailure] = {}
        self._waiters: dict[int, int] = {}

    @property
    def loaded(self) -> bool:
        with self._condition:
            return self._state == self._LOADED

    def _run_load(self, *, force: bool) -> Mapping[K, V]:
        with self._condition:
            if not force and self._state == self._LOADED:
                return self._value
            if self._state == self._LOADING:
                waited_generation = self._generation
                self._waiters[waited_generation] = self._waiters.get(waited_generation, 0) + 1
                while self._state == self._LOADING and self._generation == waited_generation:
                    self._condition.wait()
                return self._consume_outcome(waited_generation)
            previous_state = self._state
            previous_value = self._value
            self._state = self._LOADING
            self._generation += 1
            generation = self._generation
            self._waiters[generation] = 0
        try:
            loaded = MappingProxyType(dict(self._loader()))
        except Exception as error:
            with self._condition:
                waiters = self._waiters.pop(generation)
                if waiters:
                    self._outcomes[generation] = _GenerationFailure(error=error, waiters=waiters)
                self._state = self._LOADED if previous_state == self._LOADED else self._UNLOADED
                if previous_state == self._LOADED:
                    self._value = previous_value
                self._condition.notify_all()
            raise
        with self._condition:
            self._value = loaded
            self._state = self._LOADED
            waiters = self._waiters.pop(generation)
            if waiters:
                self._outcomes[generation] = _GenerationSuccess(value=self._value, waiters=waiters)
            self._condition.notify_all()
            return self._value

    def _consume_outcome(self, generation: int) -> Mapping[K, V]:
        outcome = self._outcomes[generation]
        outcome.waiters -= 1
        if outcome.waiters == 0:
            del self._outcomes[generation]
        if isinstance(outcome, _GenerationFailure):
            raise outcome.error
        return outcome.value

    def all(self) -> Mapping[K, V]:
        return self._run_load(force=False)

    def refresh(self) -> Mapping[K, V]:
        return self._run_load(force=True)

    def invalidate(self) -> None:
        with self._condition:
            while self._state == self._LOADING:
                self._condition.wait()
            self._state = self._UNLOADED
            self._value = MappingProxyType({})

    def __getitem__(self, key: K) -> V:
        return self.all()[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self.all())

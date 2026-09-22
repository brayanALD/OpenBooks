from typing import Generic

from app.repositories.base import Repository, T


class InMemoryRepository(Repository[T], Generic[T]):
    """Para tests: mismo contrato que el repositorio JSON, sin tocar el disco."""

    def __init__(self, items: list[T] | None = None) -> None:
        self._items: dict[str, T] = {i.id: i for i in items or []}

    def list(self) -> list[T]:
        return list(self._items.values())

    def get(self, id: str) -> T | None:
        return self._items.get(id)

    def add(self, item: T) -> T:
        if item.id in self._items:
            raise ValueError(f"Ya existe un registro con id {item.id!r}")
        self._items[item.id] = item
        return item

    def update(self, item: T) -> T:
        if item.id not in self._items:
            raise KeyError(item.id)
        self._items[item.id] = item
        return item

    def delete(self, id: str) -> bool:
        return self._items.pop(id, None) is not None

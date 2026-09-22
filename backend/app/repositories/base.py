from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.domain.models import Entity

T = TypeVar("T", bound=Entity)


class Repository(ABC, Generic[T]):
    """Puerto de persistencia. Los servicios dependen de esta interfaz, nunca de JSON."""

    @abstractmethod
    def list(self) -> list[T]: ...

    @abstractmethod
    def get(self, id: str) -> T | None: ...

    @abstractmethod
    def add(self, item: T) -> T:
        """Inserta. Lanza `ValueError` si el id ya existe."""

    @abstractmethod
    def update(self, item: T) -> T:
        """Reemplaza por id. Lanza `KeyError` si no existe."""

    @abstractmethod
    def delete(self, id: str) -> bool:
        """True si existía y se borró."""

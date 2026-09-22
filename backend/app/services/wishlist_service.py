import threading
from datetime import datetime, timezone

from app.domain.models import Wishlist
from app.repositories.base import Repository
from app.schemas.catalog import BookSummary
from app.services.catalog_service import CatalogService

MAX_FAVORITES = 200


class WishlistError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


class WishlistService:
    """Favoritos de cada usuario con sesión.

    Se guardan solo ids. Lo que se devuelve se filtra contra el catálogo visible: un libro que el administrador oculta
    deja de aparecer (y de contar) sin borrarlo de la lista, así que reaparece si se vuelve a activar.
    """

    def __init__(self, catalog: CatalogService, wishlists: Repository[Wishlist]) -> None:
        self._catalog = catalog
        self._wishlists = wishlists
        self._lock = threading.Lock()  # leer-modificar-escribir de la lista de un usuario

    def _stored(self, user_id: str) -> list[str]:
        wishlist = self._wishlists.get(user_id)
        return list(wishlist.book_ids) if wishlist else []

    def _save(self, user_id: str, book_ids: list[str]) -> None:
        wishlist = Wishlist(id=user_id, book_ids=book_ids, updated_at=datetime.now(timezone.utc))
        if self._wishlists.get(user_id) is None:
            self._wishlists.add(wishlist)
        else:
            self._wishlists.update(wishlist)

    def books(self, user_id: str) -> list[BookSummary]:
        """Tarjetas de los favoritos disponibles, del más reciente al más antiguo."""
        stored = self._stored(user_id)
        summaries = self._catalog.summaries_by_id(stored)
        return [summaries[book_id] for book_id in stored if book_id in summaries]

    def ids(self, user_id: str) -> list[str]:
        return [book.id for book in self.books(user_id)]

    def add(self, user_id: str, book_id: str) -> list[str]:
        with self._lock:
            if not self._catalog.summaries_by_id([book_id]):
                raise WishlistError("not_found", "Ese libro no existe o ya no está disponible.")
            stored = self._stored(user_id)
            if book_id not in stored:
                if len(stored) >= MAX_FAVORITES:
                    raise WishlistError("full", f"Puedes guardar hasta {MAX_FAVORITES} favoritos.")
                self._save(user_id, [book_id, *stored])
        return self.ids(user_id)

    def remove(self, user_id: str, book_id: str) -> list[str]:
        """Quitar algo que no está no es un error: la operación es idempotente."""
        with self._lock:
            stored = self._stored(user_id)
            if book_id in stored:
                self._save(user_id, [b for b in stored if b != book_id])
        return self.ids(user_id)

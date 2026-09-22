import threading
from datetime import datetime, timezone

from app.domain.models import Cart, CartItem
from app.domain.rules import MAX_QUANTITY_PER_BOOK
from app.repositories.base import Repository
from app.services.catalog_service import CatalogService


class CartStorage:
    """Carrito guardado de cada usuario con sesión, para que lo vea desde cualquier navegador.

    Guarda solo ids y cantidades (igual que el navegador). El stock NO se aplica aquí: lo aplica
    `CartService.validate` al mostrar el carrito y, más adelante, el checkout.
    """

    def __init__(self, catalog: CatalogService, carts: Repository[Cart]) -> None:
        self._catalog = catalog
        self._carts = carts
        self._lock = threading.Lock()  # leer-modificar-escribir del carrito de un usuario

    def _clean(self, pairs: list[tuple[str, int]]) -> list[CartItem]:
        """Une repetidos (respetando el orden), descarta libros que no existen y acota a 10 por libro."""
        merged: dict[str, int] = {}
        for book_id, quantity in pairs:
            merged[book_id] = merged.get(book_id, 0) + quantity
        known = self._catalog.summaries_by_id(merged)
        return [
            CartItem(book_id=book_id, quantity=min(quantity, MAX_QUANTITY_PER_BOOK))
            for book_id, quantity in merged.items()
            if book_id in known and quantity >= 1
        ]

    def _save(self, user_id: str, items: list[CartItem]) -> list[CartItem]:
        cart = Cart(id=user_id, items=items, updated_at=datetime.now(timezone.utc))
        if self._carts.get(user_id) is None:
            self._carts.add(cart)
        else:
            self._carts.update(cart)
        return items

    def get(self, user_id: str) -> list[CartItem]:
        return self.get_with_removed(user_id)[0]

    def get_with_removed(self, user_id: str) -> tuple[list[CartItem], list[str]]:
        """Carrito guardado y los ids de libros que se quitaron por dejar de estar disponibles (ocultos o borrados).

        Si se quitó alguno, el carrito limpio se guarda: así el aviso al usuario se da una sola vez y no en cada carga.
        """
        with self._lock:
            cart = self._carts.get(user_id)
            if cart is None:
                return [], []
            stored = [(i.book_id, i.quantity) for i in cart.items]
            clean = self._clean(stored)
            kept = {i.book_id for i in clean}
            removed = [book_id for book_id, _ in stored if book_id not in kept]
            if removed:
                self._save(user_id, clean)
            return clean, removed

    def replace(self, user_id: str, items: list[tuple[str, int]]) -> list[CartItem]:
        with self._lock:
            return self._save(user_id, self._clean(items))

    def merge(self, user_id: str, guest_items: list[tuple[str, int]]) -> list[CartItem]:
        """Suma el carrito de invitado al guardado: los libros que están en ambos suman cantidades."""
        with self._lock:
            cart = self._carts.get(user_id)
            stored = [(i.book_id, i.quantity) for i in cart.items] if cart else []
            return self._save(user_id, self._clean([*stored, *guest_items]))

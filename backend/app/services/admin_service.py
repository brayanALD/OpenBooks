import math
import re
from collections import Counter
from datetime import datetime, timezone

from app.core.locks import inventory_lock
from app.core.text import slugify
from app.domain.models import Author, Book, Category, Order, User
from app.repositories.base import Repository
from app.schemas.admin import BookCreateIn, BookUpdateIn
from app.services.catalog_service import final_price, fold

LOW_STOCK_LIMIT = 5

# Estados de un pedido y a cuáles se puede pasar. Los demás son finales.
# «Enviado» ya no se cancela: habría que gestionar una devolución física.
TRANSITIONS: dict[str, set[str]] = {
    "paid": {"shipped", "cancelled"},
    "shipped": {"delivered"},
}


class AdminError(Exception):
    """Operación de administración no válida. `code` lo traduce la API a un código HTTP."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AdminService:
    """Gestión de libros y pedidos. Toda escritura sobre libros/pedidos toma el candado de inventario, el mismo
    que usan las compras: así una edición no pisa el stock que acaba de descontar una venta."""

    def __init__(
        self,
        books: Repository[Book],
        authors: Repository[Author],
        categories: Repository[Category],
        orders: Repository[Order],
        users: Repository[User],
    ) -> None:
        self._books = books
        self._authors = authors
        self._categories = categories
        self._orders = orders
        self._users = users
        self._lock = inventory_lock

    # -- libros ----------------------------------------------------------------------------------

    def list_books(
        self,
        q: str | None = None,
        active: bool | None = None,
        low_stock: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Book], int, dict[str, str]]:
        """Devuelve (libros de la página, total, {author_id: nombre}). Incluye los ocultos."""
        authors = {a.id: a.name for a in self._authors.list()}
        needle = fold(q.strip()) if q and q.strip() else None

        def matches(book: Book) -> bool:
            if active is not None and book.active != active:
                return False
            if low_stock and not (book.active and book.stock <= LOW_STOCK_LIMIT):
                return False
            if needle and needle not in fold(f"{book.title} {authors.get(book.author_id, '')} {book.slug}"):
                return False
            return True

        found = sorted((b for b in self._books.list() if matches(b)), key=lambda b: fold(b.title))
        start = (page - 1) * page_size
        return found[start : start + page_size], len(found), authors

    def get_book(self, book_id: str) -> Book | None:
        return self._books.get(book_id)

    def author_names(self) -> list[str]:
        return sorted((a.name for a in self._authors.list()), key=fold)

    def author_name_of(self, book: Book) -> str:
        author = self._authors.get(book.author_id)
        return author.name if author else "—"

    def create_book(self, data: BookCreateIn) -> Book:
        with self._lock:
            self._check_categories(data.category_ids)
            fields = data.model_dump(exclude={"author_name"})
            book = Book(
                id=self._next_id(self._books.list(), "bk_"),
                slug=self._unique_slug(data.title),
                author_id=self._author_id_for(data.author_name),
                incomplete=not (data.publisher and data.pages and data.description),
                created_at=datetime.now(timezone.utc),
                **fields,
            )
            return self._books.add(book)

    def update_book(self, book_id: str, data: BookUpdateIn) -> Book:
        with self._lock:
            book = self._books.get(book_id)
            if book is None:
                raise AdminError("not_found", "Libro no encontrado")

            changes = data.model_dump(exclude_unset=True)
            # `None` explícito solo tiene sentido en los campos opcionales; en el resto se ignora.
            optional = {"publisher", "pages", "language", "cover_blur"}
            changes = {k: v for k, v in changes.items() if v is not None or k in optional}

            if "category_ids" in changes:
                self._check_categories(changes["category_ids"])
            if "author_name" in changes:
                changes["author_id"] = self._author_id_for(changes.pop("author_name"))
            # El slug NO cambia al editar el título: las URLs publicadas y los enlaces guardados deben seguir valiendo.

            merged = {**book.model_dump(), **changes}
            merged["incomplete"] = not (merged["publisher"] and merged["pages"] and merged["description"])
            return self._books.update(Book.model_validate(merged))  # model_validate: vuelve a comprobar los límites

    def final_price_of(self, book: Book) -> int:
        return final_price(book.price_cop, book.discount_pct)

    # -- pedidos ---------------------------------------------------------------------------------

    def list_orders(
        self, status: str | None = None, q: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[tuple[Order, User | None]], int]:
        users = {u.id: u for u in self._users.list()}
        needle = fold(q.strip()) if q and q.strip() else None

        def matches(order: Order) -> bool:
            if status and order.status != status:
                return False
            if needle:
                user = users.get(order.user_id)
                haystack = fold(f"{order.number} {user.email if user else ''} {user.first_name if user else ''} {user.last_name if user else ''} {order.shipping.recipient_name}")
                return needle in haystack
            return True

        found = sorted(
            (o for o in self._orders.list() if matches(o)),
            key=lambda o: (o.created_at, int(o.number.removeprefix("OB-"))),
            reverse=True,
        )
        start = (page - 1) * page_size
        return [(o, users.get(o.user_id)) for o in found[start : start + page_size]], len(found)

    def get_order(self, order_id: str) -> tuple[Order, User | None] | None:
        order = self._orders.get(order_id)
        return (order, self._users.get(order.user_id)) if order else None

    def change_order_status(self, order_id: str, new_status: str) -> Order:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                raise AdminError("not_found", "Pedido no encontrado")
            if new_status not in TRANSITIONS.get(order.status, set()):
                raise AdminError(
                    "invalid_transition",
                    f"Un pedido «{order.status}» no puede pasar a «{new_status}».",
                )
            if new_status == "cancelled":
                self._restock(order)  # las unidades reservadas por la compra vuelven al inventario
            return self._orders.update(order.model_copy(update={"status": new_status}))

    def _restock(self, order: Order) -> None:
        for item in order.items:
            book = self._books.get(item.book_id)
            if book is not None:  # si el libro se borrara del catálogo no hay nada que devolver
                self._books.update(book.model_copy(update={"stock": book.stock + item.quantity}))

    # -- resumen ---------------------------------------------------------------------------------

    def summary(self) -> dict:
        books = self._books.list()
        active = [b for b in books if b.active]
        orders = self._orders.list()
        return {
            "books": {
                "total": len(books),
                "active": len(active),
                "hidden": len(books) - len(active),
                "out_of_stock": sum(b.stock == 0 for b in active),
                "low_stock": sum(0 < b.stock <= LOW_STOCK_LIMIT for b in active),
            },
            "orders": {
                "by_status": dict(Counter(o.status for o in orders)),
                "revenue_cop": sum(o.total_cop for o in orders if o.status in {"paid", "shipped", "delivered"}),
            },
        }

    # -- utilidades (con el candado tomado) ---------------------------------------------------------------

    def _check_categories(self, category_ids: list[str]) -> None:
        known = {c.id for c in self._categories.list()}
        unknown = [c for c in category_ids if c not in known]
        if unknown:
            raise AdminError("invalid_category", f"Categoría desconocida: {', '.join(unknown)}")

    def _author_id_for(self, name: str) -> str:
        """Reutiliza el autor si ya existe (sin distinguir mayúsculas ni tildes); si no, lo crea."""
        name = " ".join(name.split())  # "Ana  Nueva " y "Ana Nueva" son la misma persona
        wanted = fold(name)
        existing = next((a for a in self._authors.list() if " ".join(fold(a.name).split()) == wanted), None)
        if existing:
            return existing.id
        slug = slugify(name)
        taken = {a.slug for a in self._authors.list()}
        candidate, n = slug, 2
        while candidate in taken:
            candidate, n = f"{slug}-{n}", n + 1
        author = Author(id=self._next_id(self._authors.list(), "aut_"), name=name, slug=candidate)
        return self._authors.add(author).id

    def _unique_slug(self, title: str) -> str:
        base = slugify(title) or "libro"
        taken = {b.slug for b in self._books.list()}
        candidate, n = base, 2
        while candidate in taken:
            candidate, n = f"{base}-{n}", n + 1
        return candidate

    @staticmethod
    def _next_id(items: list, prefix: str) -> str:
        numbers = [int(m.group(1)) for i in items if (m := re.fullmatch(rf"{re.escape(prefix)}(\d+)", i.id))]
        return f"{prefix}{max(numbers, default=0) + 1:03d}"

    @staticmethod
    def pages(total: int, page_size: int) -> int:
        return max(1, math.ceil(total / page_size))

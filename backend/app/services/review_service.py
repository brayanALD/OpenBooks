import threading
from datetime import datetime, timezone

from app.domain.models import Book, Order, Review, User
from app.repositories.base import Repository
from app.schemas.catalog import ReviewOut
from app.schemas.reviews import ReviewIn

# Un pedido cuenta como compra si el pago se aprobó y no se canceló.
PURCHASED = {"paid", "shipped", "delivered"}


class ReviewError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def to_out(review: Review) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        author_name=review.author_name,
        rating=review.rating,
        comment=review.comment,
        is_demo=review.is_demo,
        verified=not review.is_demo and review.user_id is not None,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


class ReviewService:
    """Reseñas de compradores verificados: solo reseña quien compró el libro, una por libro y persona.

    Quien escribe puede editar y borrar la suya. Las reseñas de muestra solo las puede quitar un administrador.
    """

    def __init__(self, reviews: Repository[Review], books: Repository[Book], orders: Repository[Order]) -> None:
        self._reviews = reviews
        self._books = books
        self._orders = orders
        self._lock = threading.RLock()  # comprobar «ya reseñó» y guardar debe ser una sola operación

    # -- consulta --------------------------------------------------------------------------------

    def _visible_book(self, slug: str) -> Book:
        book = next((b for b in self._books.list() if b.slug == slug and b.active), None)
        if book is None:
            raise ReviewError("not_found", "Libro no encontrado")
        return book

    def has_purchased(self, user_id: str, book_id: str) -> bool:
        return any(
            o.user_id == user_id and o.status in PURCHASED and any(i.book_id == book_id for i in o.items)
            for o in self._orders.list()
        )

    def _mine(self, user_id: str, book_id: str) -> Review | None:
        return next((r for r in self._reviews.list() if r.user_id == user_id and r.book_id == book_id), None)

    def status(self, user: User, slug: str) -> tuple[bool, bool, Review | None]:
        """(puede reseñar, ha comprado, su reseña)."""
        book = self._visible_book(slug)
        mine = self._mine(user.id, book.id)
        purchased = self.has_purchased(user.id, book.id)
        return purchased and mine is None, purchased, mine

    # -- escritura ------------------------------------------------------------------------------

    def create(self, user: User, slug: str, data: ReviewIn) -> Review:
        book = self._visible_book(slug)
        with self._lock:
            if not self.has_purchased(user.id, book.id):
                raise ReviewError("not_eligible", "Solo pueden reseñar quienes compraron este libro.")
            if self._mine(user.id, book.id) is not None:
                raise ReviewError("already_reviewed", "Ya reseñaste este libro. Puedes editar tu reseña.")
            review = Review(
                id=self._next_id(),
                book_id=book.id,
                user_id=user.id,
                author_name=self._display_name(user),
                rating=data.rating,
                comment=data.comment,
                is_demo=False,
                created_at=datetime.now(timezone.utc),
            )
            return self._reviews.add(review)

    def update(self, user: User, slug: str, data: ReviewIn) -> Review:
        book = self._visible_book(slug)
        with self._lock:
            mine = self._mine(user.id, book.id)
            if mine is None:
                raise ReviewError("not_found", "Todavía no has reseñado este libro.")
            edited = mine.model_copy(
                update={"rating": data.rating, "comment": data.comment, "updated_at": datetime.now(timezone.utc)}
            )
            return self._reviews.update(edited)

    def delete_mine(self, user: User, slug: str) -> None:
        book = self._visible_book(slug)
        with self._lock:
            mine = self._mine(user.id, book.id)
            if mine is None:
                raise ReviewError("not_found", "Todavía no has reseñado este libro.")
            self._reviews.delete(mine.id)

    # -- moderación (solo administradores; la API lo exige) ---------------------------------------------

    def admin_list(self, book_id: str) -> list[Review]:
        return sorted((r for r in self._reviews.list() if r.book_id == book_id), key=lambda r: r.created_at, reverse=True)

    def admin_delete(self, review_id: str) -> None:
        with self._lock:
            if not self._reviews.delete(review_id):
                raise ReviewError("not_found", "Reseña no encontrada")

    # -- utilidades -------------------------------------------------------------------------------------

    @staticmethod
    def _display_name(user: User) -> str:
        """«Ana P.»: el nombre y la inicial del apellido; nunca el correo ni el apellido completo."""
        initial = user.last_name.strip()[:1].upper()
        return f"{user.first_name.strip()} {initial}." if initial else user.first_name.strip()

    def _next_id(self) -> str:
        numbers = [int(r.id[3:]) for r in self._reviews.list() if r.id.startswith("rv_") and r.id[3:].isdigit()]
        return f"rv_{max(numbers, default=0) + 1:03d}"

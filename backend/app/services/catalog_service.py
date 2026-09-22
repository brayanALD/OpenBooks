import math
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.models import Author, Book, Category, Review
from app.repositories.base import Repository
from app.schemas.catalog import (
    AuthorOut,
    BookDetail,
    BookSort,
    BookSummary,
    CategoryOut,
    CategoryRef,
    Page,
    ReviewOut,
)


def fold(text: str) -> str:
    """Minúsculas y sin tildes: 'García' == 'garcia'."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def final_price(price_cop: int, discount_pct: int) -> int:
    """Precio por unidad con descuento, en pesos enteros (se redondea hacia abajo)."""
    return price_cop * (100 - discount_pct) // 100


@dataclass(frozen=True)
class BookQuery:
    q: str | None = None
    category: str | None = None  # slug
    author: str | None = None  # slug
    min_price: int | None = None  # sobre el precio final
    max_price: int | None = None
    free_shipping: bool | None = None
    on_sale: bool | None = None
    in_stock: bool | None = None
    featured: bool | None = None
    bestseller: bool | None = None
    sort: BookSort = BookSort.relevance
    page: int = 1
    page_size: int = 12


class CatalogService:
    def __init__(
        self,
        books: Repository[Book],
        authors: Repository[Author],
        categories: Repository[Category],
        reviews: Repository[Review],
    ) -> None:
        self._books = books
        self._authors = authors
        self._categories = categories
        self._reviews = reviews

    # -- lectura de apoyo ------------------------------------------------------------------

    def _visible_books(self) -> list[Book]:
        """Libros de la tienda pública: los ocultos por el administrador no existen para el cliente
        (ni en listados, ni en su ficha, ni en el carrito ni en la compra)."""
        return [b for b in self._books.list() if b.active]

    def _context(self):
        """Índices para armar las respuestas sin consultar por cada libro."""
        authors = {a.id: a for a in self._authors.list()}
        categories = {c.id: c for c in self._categories.list()}
        ratings: dict[str, list[int]] = defaultdict(list)
        for review in self._reviews.list():
            ratings[review.book_id].append(review.rating)
        return authors, categories, ratings

    @staticmethod
    def _summary(book: Book, authors, categories, ratings) -> BookSummary:
        author = authors[book.author_id]
        scores = ratings.get(book.id, [])
        final = final_price(book.price_cop, book.discount_pct)
        return BookSummary(
            id=book.id,
            slug=book.slug,
            title=book.title,
            author=AuthorOut(id=author.id, name=author.name, slug=author.slug),
            categories=[
                CategoryRef(id=c.id, name=c.name, slug=c.slug)
                for cid in book.category_ids
                if (c := categories.get(cid))
            ],
            price_cop=book.price_cop,
            discount_pct=book.discount_pct,
            final_price_cop=final,
            shipping_cost_cop=book.shipping_cost_cop,
            free_shipping=book.shipping_cost_cop == 0,
            stock=book.stock,
            in_stock=book.stock > 0,
            cover=book.cover,
            cover_width=book.cover_width,
            cover_height=book.cover_height,
            cover_blur=book.cover_blur,
            featured=book.featured,
            bestseller=book.bestseller,
            rating_avg=round(sum(scores) / len(scores), 1) if scores else None,
            rating_count=len(scores),
        )

    # -- libros ----------------------------------------------------------------------------

    def list_books(self, query: BookQuery) -> Page[BookSummary]:
        authors, categories, ratings = self._context()
        slug_to_category = {c.slug: c.id for c in categories.values()}
        author_slug_to_id = {a.slug: a.id for a in authors.values()}
        needle = fold(query.q.strip()) if query.q and query.q.strip() else None

        def matches(book: Book) -> bool:
            final = final_price(book.price_cop, book.discount_pct)
            if query.category is not None:
                cid = slug_to_category.get(query.category)
                if cid is None or cid not in book.category_ids:
                    return False
            if query.author is not None and author_slug_to_id.get(query.author) != book.author_id:
                return False
            if query.min_price is not None and final < query.min_price:
                return False
            if query.max_price is not None and final > query.max_price:
                return False
            if query.free_shipping is not None and (book.shipping_cost_cop == 0) != query.free_shipping:
                return False
            if query.on_sale is not None and (book.discount_pct > 0) != query.on_sale:
                return False
            if query.in_stock is not None and (book.stock > 0) != query.in_stock:
                return False
            if query.featured is not None and book.featured != query.featured:
                return False
            if query.bestseller is not None and book.bestseller != query.bestseller:
                return False
            if needle is not None and self._score(book, authors[book.author_id], needle) == 0:
                return False
            return True

        found = [b for b in self._visible_books() if matches(b)]

        def rating_of(book: Book) -> float:
            scores = ratings.get(book.id, [])
            return sum(scores) / len(scores) if scores else 0.0

        sort = query.sort
        if sort is BookSort.price_asc:
            found.sort(key=lambda b: (final_price(b.price_cop, b.discount_pct), b.title))
        elif sort is BookSort.price_desc:
            found.sort(key=lambda b: (-final_price(b.price_cop, b.discount_pct), b.title))
        elif sort is BookSort.rating:
            found.sort(key=lambda b: (-rating_of(b), b.title))
        elif sort is BookSort.title:
            found.sort(key=lambda b: fold(b.title))
        elif sort is BookSort.newest:
            found.sort(key=lambda b: (b.created_at, b.id), reverse=True)
        elif needle is not None:  # relevance con búsqueda
            found.sort(key=lambda b: (-self._score(b, authors[b.author_id], needle), fold(b.title)))
        else:  # relevance sin búsqueda: destacados y más vendidos primero
            found.sort(key=lambda b: (not b.featured, not b.bestseller, fold(b.title)))

        total = len(found)
        pages = max(1, math.ceil(total / query.page_size))
        start = (query.page - 1) * query.page_size
        window = found[start : start + query.page_size]
        return Page[BookSummary](
            items=[self._summary(b, authors, categories, ratings) for b in window],
            total=total,
            page=query.page,
            page_size=query.page_size,
            pages=pages,
        )

    @staticmethod
    def _score(book: Book, author: Author, needle: str) -> int:
        """Todas las palabras deben aparecer; el título pesa más que el autor y el resto."""
        title, by, extra = fold(book.title), fold(author.name), fold(f"{book.publisher or ''} {book.description}")
        words = needle.split()
        if not all(w in title or w in by or w in extra for w in words):
            return 0
        return sum(3 * (w in title) + 2 * (w in by) + (w in extra) for w in words)

    def summaries_by_id(self, ids: Iterable[str]) -> dict[str, BookSummary]:
        """Tarjetas de los libros pedidos. Los ids que no existen simplemente no aparecen."""
        wanted = set(ids)
        authors, categories, ratings = self._context()
        return {
            b.id: self._summary(b, authors, categories, ratings)
            for b in self._visible_books()
            if b.id in wanted
        }

    def get_book(self, slug: str) -> BookDetail | None:
        book = next((b for b in self._visible_books() if b.slug == slug), None)
        if book is None:
            return None
        authors, categories, ratings = self._context()
        summary = self._summary(book, authors, categories, ratings)
        return BookDetail(
            **summary.model_dump(),
            publisher=book.publisher,
            pages=book.pages,
            language=book.language,
            description=book.description,
            incomplete=book.incomplete,
        )

    def related_books(self, slug: str, limit: int = 6) -> list[BookSummary] | None:
        """Mismo autor primero, luego misma categoría. None si el libro no existe."""
        book = next((b for b in self._visible_books() if b.slug == slug), None)
        if book is None:
            return None
        authors, categories, ratings = self._context()
        others = [b for b in self._visible_books() if b.id != book.id]

        def affinity(other: Book) -> tuple[int, int]:
            same_author = other.author_id == book.author_id
            shared = len(set(other.category_ids) & set(book.category_ids))
            return (int(same_author), shared)

        ranked = sorted(
            (b for b in others if affinity(b) != (0, 0)),
            key=lambda b: (affinity(b), b.bestseller, b.featured),
            reverse=True,
        )
        return [self._summary(b, authors, categories, ratings) for b in ranked[:limit]]

    def recommended_books(self, purchased_ids: Iterable[str] | None = None, limit: int = 8) -> list[BookSummary]:
        """Portada, dos modos:

        - Sin compras pagadas (`purchased_ids` vacío): destacados y más vendidos primero, desempatando por
          valoración media, igual que a un cliente nuevo.
        - Con compras pagadas: libros afines a lo ya comprado (mismo autor pesa más que categoría compartida),
          sin repetir lo comprado. Si el historial da pocos afines, se completa con los mismos genéricos.
        """
        authors, categories, ratings = self._context()
        visible = self._visible_books()
        purchased = set(purchased_ids or ())

        def rating_of(book: Book) -> float:
            scores = ratings.get(book.id, [])
            return sum(scores) / len(scores) if scores else 0.0

        def generic_key(book: Book) -> tuple[bool, bool, float, str]:
            return (not book.featured, not book.bestseller, -rating_of(book), fold(book.title))

        candidates = [b for b in visible if b.id not in purchased]

        if not purchased:
            ranked = sorted(candidates, key=generic_key)
            return [self._summary(b, authors, categories, ratings) for b in ranked[:limit]]

        bought = [b for b in visible if b.id in purchased]
        author_counts = Counter(b.author_id for b in bought)
        category_counts = Counter(cid for b in bought for cid in b.category_ids)

        def affinity_score(book: Book) -> int:
            return 3 * author_counts.get(book.author_id, 0) + sum(
                category_counts.get(cid, 0) for cid in book.category_ids
            )

        scored = sorted(
            (b for b in candidates if affinity_score(b) > 0),
            key=lambda b: (-affinity_score(b), generic_key(b)),
        )
        chosen = scored[:limit]

        if len(chosen) < limit:  # historial muy acotado: se completa con los mismos genéricos que a un cliente nuevo
            chosen_ids = {b.id for b in chosen}
            filler = sorted((b for b in candidates if b.id not in chosen_ids), key=generic_key)
            chosen += filler[: limit - len(chosen)]

        return [self._summary(b, authors, categories, ratings) for b in chosen]

    def book_reviews(self, slug: str) -> list[ReviewOut] | None:
        book = next((b for b in self._visible_books() if b.slug == slug), None)
        if book is None:
            return None
        mine = sorted(
            (r for r in self._reviews.list() if r.book_id == book.id),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return [
            ReviewOut(
                id=r.id,
                author_name=r.author_name,
                rating=r.rating,
                comment=r.comment,
                is_demo=r.is_demo,
                verified=not r.is_demo and r.user_id is not None,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in mine
        ]

    # -- categorías ------------------------------------------------------------------------

    def list_categories(self) -> list[CategoryOut]:
        counts: dict[str, int] = defaultdict(int)
        for book in self._visible_books():
            for cid in book.category_ids:
                counts[cid] += 1
        ordered = sorted(self._categories.list(), key=lambda c: (c.position, c.name))
        return [
            CategoryOut(
                id=c.id, name=c.name, slug=c.slug, description=c.description, book_count=counts[c.id]
            )
            for c in ordered
        ]

    def get_category(self, slug: str) -> CategoryOut | None:
        return next((c for c in self.list_categories() if c.slug == slug), None)

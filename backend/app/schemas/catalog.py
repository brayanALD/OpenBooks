from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class AuthorOut(BaseModel):
    id: str
    name: str
    slug: str


class CategoryRef(BaseModel):
    id: str
    name: str
    slug: str


class CategoryOut(CategoryRef):
    description: str
    book_count: int


class BookSummary(BaseModel):
    """Lo necesario para una tarjeta de libro. No incluye la descripción larga."""

    id: str
    slug: str
    title: str
    author: AuthorOut
    categories: list[CategoryRef]

    price_cop: int  # precio de lista
    discount_pct: int
    final_price_cop: int  # precio a pagar por unidad, ya con descuento
    shipping_cost_cop: int
    free_shipping: bool

    stock: int
    in_stock: bool

    cover: str
    cover_width: int
    cover_height: int
    cover_blur: str | None

    featured: bool
    bestseller: bool
    rating_avg: float | None  # None si aún no hay reseñas
    rating_count: int


class BookDetail(BookSummary):
    publisher: str | None
    pages: int | None
    language: str | None
    description: str
    incomplete: bool


class ReviewOut(BaseModel):
    id: str
    author_name: str
    rating: int
    comment: str
    is_demo: bool
    verified: bool  # reseña de una cuenta que compró el libro (las de muestra nunca lo son)
    created_at: datetime
    updated_at: datetime | None = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class BookSort(str, Enum):
    relevance = "relevance"
    price_asc = "price_asc"
    price_desc = "price_desc"
    rating = "rating"
    title = "title"
    newest = "newest"

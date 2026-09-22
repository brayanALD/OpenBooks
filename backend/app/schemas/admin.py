import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.schemas.catalog import Page
from app.schemas.orders import OrderOut

Text = Annotated[str, StringConstraints(strip_whitespace=True)]

# Una portada solo puede ser un archivo del propio sitio: importada (/covers/…) o subida (/media/covers/…).
COVER_PATTERN = re.compile(r"^/(covers|media/covers)/[A-Za-z0-9._-]+\.webp$")

PLACEHOLDER_COVER = "/covers/sin-portada.webp"


class BookFields(BaseModel):
    """Campos editables de un libro, con sus límites. Común a crear y a editar."""

    title: Annotated[Text, Field(min_length=1, max_length=200)]
    author_name: Annotated[Text, Field(min_length=2, max_length=100)]
    category_ids: Annotated[list[str], Field(min_length=1, max_length=6)]
    isbn: Annotated[Text, Field(min_length=10, max_length=20)]
    publisher: Annotated[Text, Field(max_length=100)] | None = None
    pages: Annotated[int, Field(ge=1, le=20_000)] | None = None
    language: Annotated[Text, Field(max_length=40)] | None = None
    description: Annotated[Text, Field(max_length=20_000)] = ""
    price_cop: Annotated[int, Field(ge=0, le=100_000_000)]
    discount_pct: Annotated[int, Field(ge=0, le=90)] = 0
    shipping_cost_cop: Annotated[int, Field(ge=0, le=1_000_000)] = 0
    stock: Annotated[int, Field(ge=0, le=100_000)] = 0
    featured: bool = False
    bestseller: bool = False
    active: bool = True
    cover: str = PLACEHOLDER_COVER
    cover_width: Annotated[int, Field(gt=0, le=10_000)] = 300
    cover_height: Annotated[int, Field(gt=0, le=10_000)] = 450
    cover_blur: Annotated[str, Field(max_length=2_000)] | None = None

    @field_validator("publisher", "language")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("cover")
    @classmethod
    def _cover_is_ours(cls, value: str) -> str:
        if not COVER_PATTERN.match(value):
            raise ValueError("La portada debe ser un archivo del sitio (/covers/… o /media/covers/…)")
        return value

    @field_validator("cover_blur")
    @classmethod
    def _blur_is_a_data_uri(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("data:image/webp;base64,"):
            raise ValueError("cover_blur debe ser un data URI webp")
        return value


class BookCreateIn(BookFields):
    pass


class BookUpdateIn(BaseModel):
    """Edición parcial: solo se cambia lo que venga en la petición (`model_dump(exclude_unset=True)`)."""

    title: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    author_name: Annotated[Text, Field(min_length=2, max_length=100)] | None = None
    category_ids: Annotated[list[str], Field(min_length=1, max_length=6)] | None = None
    isbn: Annotated[Text, Field(min_length=10, max_length=20)] | None = None
    publisher: Annotated[Text, Field(max_length=100)] | None = None
    pages: Annotated[int, Field(ge=1, le=20_000)] | None = None
    language: Annotated[Text, Field(max_length=40)] | None = None
    description: Annotated[Text, Field(max_length=20_000)] | None = None
    price_cop: Annotated[int, Field(ge=0, le=100_000_000)] | None = None
    discount_pct: Annotated[int, Field(ge=0, le=90)] | None = None
    shipping_cost_cop: Annotated[int, Field(ge=0, le=1_000_000)] | None = None
    stock: Annotated[int, Field(ge=0, le=100_000)] | None = None
    featured: bool | None = None
    bestseller: bool | None = None
    active: bool | None = None
    cover: str | None = None
    cover_width: Annotated[int, Field(gt=0, le=10_000)] | None = None
    cover_height: Annotated[int, Field(gt=0, le=10_000)] | None = None
    cover_blur: Annotated[str, Field(max_length=2_000)] | None = None

    @field_validator("cover")
    @classmethod
    def _cover_is_ours(cls, value: str | None) -> str | None:
        if value is not None and not COVER_PATTERN.match(value):
            raise ValueError("La portada debe ser un archivo del sitio (/covers/… o /media/covers/…)")
        return value


class AdminBookOut(BaseModel):
    id: str
    slug: str
    title: str
    author_name: str
    category_ids: list[str]
    isbn: str
    publisher: str | None
    pages: int | None
    language: str | None
    description: str
    price_cop: int
    discount_pct: int
    final_price_cop: int
    shipping_cost_cop: int
    stock: int
    cover: str
    cover_width: int
    cover_height: int
    featured: bool
    bestseller: bool
    active: bool
    incomplete: bool
    created_at: datetime


class AdminBookPage(Page[AdminBookOut]):
    authors: list[str]  # nombres de autor existentes, para autocompletar en el formulario


class CoverUploadOut(BaseModel):
    cover: str
    cover_width: int
    cover_height: int
    cover_blur: str


class CustomerOut(BaseModel):
    name: str
    email: str


class AdminOrderOut(OrderOut):
    customer: CustomerOut | None  # None si la cuenta ya no existe


class StatusChangeIn(BaseModel):
    status: Literal["shipped", "delivered", "cancelled"]


class BooksSummary(BaseModel):
    total: int
    active: int
    hidden: int
    out_of_stock: int  # activos sin unidades
    low_stock: int  # activos con 1 a 5 unidades


class OrdersSummary(BaseModel):
    by_status: dict[str, int]
    revenue_cop: int  # pagados, enviados y entregados (no fallidos ni cancelados)


class SummaryOut(BaseModel):
    books: BooksSummary
    orders: OrdersSummary

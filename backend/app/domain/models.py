"""Entidades del catálogo. Inmutables: para cambiar una se usa `model_copy(update=...)`.

Diseñadas como tablas relacionales (ids + claves foráneas) para poder migrar a una base de datos
sin cambiar el resto de la aplicación.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str


class Author(Entity):
    name: str
    slug: str


class Category(Entity):
    name: str
    slug: str
    description: str = ""
    position: int = 0  # orden en la navegación


class Book(Entity):
    slug: str
    title: str
    author_id: str
    category_ids: list[str] = Field(default_factory=list)
    publisher: str | None = None
    pages: int | None = Field(default=None, ge=1)
    language: str | None = None
    description: str = ""

    # Dinero: pesos colombianos enteros. `price_cop` es el precio de lista; el final se calcula.
    price_cop: int = Field(ge=0)
    discount_pct: int = Field(default=0, ge=0, le=90)
    shipping_cost_cop: int = Field(default=0, ge=0)  # 0 = envío gratis

    stock: int = Field(ge=0)

    cover: str  # ruta pública, p. ej. "/covers/1984.webp"
    cover_width: int = Field(gt=0)
    cover_height: int = Field(gt=0)
    cover_blur: str | None = None  # data URI diminuto para `placeholder="blur"`

    featured: bool = False
    bestseller: bool = False
    # False = oculto: no se ve en la tienda, ni se puede comprar, pero sigue en el sistema (pedidos antiguos, reactivar).
    active: bool = True
    # True si el sitio original no tenía ficha de detalle (faltan editorial, páginas, descripción…).
    incomplete: bool = False
    created_at: datetime


class Address(BaseModel):
    model_config = ConfigDict(frozen=True)

    line: str  # calle, número, apartamento…
    city: str
    notes: str | None = None  # indicaciones de entrega


class User(Entity):
    first_name: str
    last_name: str
    email: str  # siempre en minúsculas: es la clave de inicio de sesión
    phone: str | None = None  # celular colombiano, 10 dígitos, opcional
    address: Address
    password_hash: str  # argon2; nunca se devuelve por la API
    role: Literal["customer", "admin"] = "customer"
    created_at: datetime


class CartItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    book_id: str
    quantity: int = Field(ge=1)


class Cart(Entity):
    """Carrito guardado de un usuario con sesión. Su `id` es el id del usuario."""

    items: list[CartItem] = Field(default_factory=list)
    updated_at: datetime


class Wishlist(Entity):
    """Favoritos de un usuario con sesión. Su `id` es el id del usuario; `book_ids` va del más reciente al más antiguo."""

    book_ids: list[str] = Field(default_factory=list)
    updated_at: datetime


class OrderItem(BaseModel):
    """Copia del libro en el momento de la compra: el pedido no cambia si luego cambia el catálogo."""

    model_config = ConfigDict(frozen=True)

    book_id: str
    title: str
    author_name: str
    cover: str
    unit_price_cop: int = Field(ge=0)
    quantity: int = Field(ge=1)
    line_total_cop: int = Field(ge=0)


class ShippingInfo(BaseModel):
    """Destinatario y dirección de ESTE pedido (puede diferir de la dirección de la cuenta)."""

    model_config = ConfigDict(frozen=True)

    recipient_name: str
    phone: str | None = None
    line: str
    city: str
    notes: str | None = None


class PaymentRecord(BaseModel):
    """Resultado del pago. Nunca contiene el número completo de la tarjeta ni el CVC."""

    model_config = ConfigDict(frozen=True)

    provider: str
    status: Literal["pending", "approved", "declined"]
    reference: str | None = None
    method: str | None = None  # p. ej. "Visa •••• 4242"
    failure_reason: str | None = None


OrderStatus = Literal["pending", "paid", "failed", "shipped", "delivered", "cancelled"]


class Order(Entity):
    number: str  # legible: OB-000001
    user_id: str
    idempotency_key: str  # mismo intento de pago = mismo pedido (evita cobrar dos veces)
    items: list[OrderItem]
    subtotal_cop: int = Field(ge=0)
    shipping_cop: int = Field(ge=0)
    total_cop: int = Field(ge=0)
    shipping: ShippingInfo
    payment: PaymentRecord
    status: OrderStatus
    created_at: datetime


class Review(Entity):
    book_id: str
    user_id: str | None = None  # None en reseñas de muestra
    author_name: str
    rating: int = Field(ge=1, le=5)
    comment: str
    is_demo: bool = False  # reseña de muestra, no de un comprador real
    created_at: datetime
    updated_at: datetime | None = None  # solo si el autor la editó

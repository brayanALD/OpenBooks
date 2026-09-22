from enum import Enum

from pydantic import BaseModel, Field

from app.domain.rules import MAX_CART_LINES
from app.schemas.catalog import BookSummary


class CartItemIn(BaseModel):
    book_id: str = Field(min_length=1, max_length=40)
    # Se admite más de lo permitido a propósito: el servidor lo recorta e informa, en vez de responder 422.
    quantity: int = Field(ge=1, le=999)


class CartItemsIn(BaseModel):
    items: list[CartItemIn] = Field(max_length=MAX_CART_LINES)


CartValidateIn = CartItemsIn  # validar y guardar reciben la misma lista


class CartItemOut(BaseModel):
    book_id: str
    quantity: int


class CartItemsOut(BaseModel):
    items: list[CartItemOut]
    removed: list[str] = []  # libros que se quitaron del carrito guardado por dejar de estar disponibles


class CartIssue(str, Enum):
    out_of_stock = "out_of_stock"  # sin unidades: no cuenta en los totales
    limited_stock = "limited_stock"  # hay menos unidades de las pedidas
    quantity_capped = "quantity_capped"  # se pidió más del máximo por pedido


class CartLineOut(BaseModel):
    book: BookSummary
    requested_quantity: int
    quantity: int  # la que el servidor acepta (0 si está agotado)
    max_quantity: int  # tope real: mínimo entre stock y máximo por pedido
    unit_price_cop: int  # ya con descuento
    line_total_cop: int
    issue: CartIssue | None = None


class CartOut(BaseModel):
    lines: list[CartLineOut]
    unavailable_ids: list[str]  # ids que ya no existen en el catálogo
    item_count: int
    subtotal_cop: int
    shipping_cop: int
    total_cop: int
    has_issues: bool

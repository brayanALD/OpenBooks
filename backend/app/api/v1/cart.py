from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_cart_service, get_cart_storage, get_current_user
from app.domain.models import CartItem, User
from app.schemas.cart import CartItemOut, CartItemsIn, CartItemsOut, CartOut, CartValidateIn
from app.services.cart_service import CartService
from app.services.cart_storage import CartStorage

router = APIRouter(prefix="/cart", tags=["carrito"])

Storage = Annotated[CartStorage, Depends(get_cart_storage)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _out(items: list[CartItem], removed: list[str] | None = None) -> CartItemsOut:
    return CartItemsOut(items=[CartItemOut(book_id=i.book_id, quantity=i.quantity) for i in items], removed=removed or [])


def _pairs(body: CartItemsIn) -> list[tuple[str, int]]:
    return [(i.book_id, i.quantity) for i in body.items]


@router.post("/validate", response_model=CartOut)
def validate_cart(body: CartValidateIn, cart: Annotated[CartService, Depends(get_cart_service)]) -> CartOut:
    """Precios, stock y totales actuales de un carrito. Público: el carrito del invitado vive en su navegador."""
    return cart.validate(body.items)


@router.get("", response_model=CartItemsOut)
def get_cart(user: CurrentUser, storage: Storage) -> CartItemsOut:
    """Carrito guardado del usuario con sesión, sin los libros que ya no están disponibles (en `removed`)."""
    return _out(*storage.get_with_removed(user.id))


@router.put("", response_model=CartItemsOut)
def replace_cart(body: CartItemsIn, user: CurrentUser, storage: Storage) -> CartItemsOut:
    """Sustituye el carrito guardado por el enviado (el cliente lo sincroniza al cambiarlo)."""
    return _out(storage.replace(user.id, _pairs(body)))


@router.post("/merge", response_model=CartItemsOut)
def merge_cart(body: CartItemsIn, user: CurrentUser, storage: Storage) -> CartItemsOut:
    """Al iniciar sesión: suma el carrito de invitado al guardado. Devuelve el resultado."""
    return _out(storage.merge(user.id, _pairs(body)))

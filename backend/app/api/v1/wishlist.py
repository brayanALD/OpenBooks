from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user, get_wishlist_service
from app.domain.models import User
from app.schemas.catalog import BookSummary
from app.services.wishlist_service import WishlistError, WishlistService

router = APIRouter(prefix="/wishlist", tags=["favoritos"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Wishlists = Annotated[WishlistService, Depends(get_wishlist_service)]


class WishlistIdsOut(BaseModel):
    book_ids: list[str]


class WishlistOut(BaseModel):
    items: list[BookSummary]


@router.get("", response_model=WishlistOut)
def list_favorites(user: CurrentUser, wishlists: Wishlists) -> WishlistOut:
    """Libros favoritos con sus tarjetas, del más reciente al más antiguo."""
    return WishlistOut(items=wishlists.books(user.id))


@router.get("/ids", response_model=WishlistIdsOut)
def favorite_ids(user: CurrentUser, wishlists: Wishlists) -> WishlistIdsOut:
    """Solo los ids: es lo que necesita la tienda para pintar los corazones."""
    return WishlistIdsOut(book_ids=wishlists.ids(user.id))


@router.put("/{book_id}", response_model=WishlistIdsOut)
def add_favorite(book_id: str, user: CurrentUser, wishlists: Wishlists) -> WishlistIdsOut:
    try:
        return WishlistIdsOut(book_ids=wishlists.add(user.id, book_id))
    except WishlistError as error:
        raise HTTPException(404 if error.code == "not_found" else 409, {"code": error.code, "message": error.message})


@router.delete("/{book_id}", response_model=WishlistIdsOut)
def remove_favorite(book_id: str, user: CurrentUser, wishlists: Wishlists) -> WishlistIdsOut:
    return WishlistIdsOut(book_ids=wishlists.remove(user.id, book_id))

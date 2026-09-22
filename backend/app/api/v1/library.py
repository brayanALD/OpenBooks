from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_catalog_service, get_current_user, get_order_service
from app.domain.models import User
from app.schemas.catalog import BookSummary
from app.services.catalog_service import CatalogService
from app.services.order_service import OrderService

router = APIRouter(prefix="/library", tags=["librero"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Orders = Annotated[OrderService, Depends(get_order_service)]
Catalog = Annotated[CatalogService, Depends(get_catalog_service)]


class LibraryUnavailableOut(BaseModel):
    book_id: str
    title: str
    author_name: str
    cover: str


class LibraryOut(BaseModel):
    items: list[BookSummary]  # libros comprados que siguen activos en la tienda
    unavailable: list[LibraryUnavailableOut]  # comprados pero el admin los ocultó después


@router.get("", response_model=LibraryOut)
def my_library(user: CurrentUser, orders: Orders, catalog: Catalog) -> LibraryOut:
    """El librero: lo comprado, sin duplicados. Lo que sigue en la tienda trae tarjeta completa
    (precio, valoración, slug); lo que el admin ocultó después se lista aparte con los datos
    congelados del pedido (no tiene ficha a la que enlazar)."""
    owned = orders.owned_book_items(user.id)
    summaries = catalog.summaries_by_id([item.book_id for item in owned])
    items = [summaries[item.book_id] for item in owned if item.book_id in summaries]
    unavailable = [
        LibraryUnavailableOut(book_id=i.book_id, title=i.title, author_name=i.author_name, cover=i.cover)
        for i in owned
        if i.book_id not in summaries
    ]
    return LibraryOut(items=items, unavailable=unavailable)

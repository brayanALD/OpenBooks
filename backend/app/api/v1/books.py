from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_catalog_service, get_current_user_optional, get_order_service
from app.domain.models import User
from app.schemas.catalog import BookDetail, BookSort, BookSummary, Page, ReviewOut
from app.services.catalog_service import BookQuery, CatalogService
from app.services.order_service import OrderService

router = APIRouter(prefix="/books", tags=["libros"])

Catalog = Annotated[CatalogService, Depends(get_catalog_service)]
Orders = Annotated[OrderService, Depends(get_order_service)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


@router.get("", response_model=Page[BookSummary])
def list_books(
    catalog: Catalog,
    q: Annotated[str | None, Query(max_length=100, description="Busca en título, autor y descripción")] = None,
    category: Annotated[str | None, Query(description="Slug de la categoría")] = None,
    author: Annotated[str | None, Query(description="Slug del autor")] = None,
    min_price: Annotated[int | None, Query(ge=0, description="Sobre el precio final, en COP")] = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
    free_shipping: bool | None = None,
    on_sale: bool | None = None,
    in_stock: bool | None = None,
    featured: bool | None = None,
    bestseller: bool | None = None,
    sort: BookSort = BookSort.relevance,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 12,
) -> Page[BookSummary]:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, "min_price no puede ser mayor que max_price")
    return catalog.list_books(
        BookQuery(
            q=q,
            category=category,
            author=author,
            min_price=min_price,
            max_price=max_price,
            free_shipping=free_shipping,
            on_sale=on_sale,
            in_stock=in_stock,
            featured=featured,
            bestseller=bestseller,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/recommended", response_model=list[BookSummary])
def recommended_books(
    catalog: Catalog,
    orders: Orders,
    user: OptionalUser,
    limit: Annotated[int, Query(ge=1, le=24)] = 8,
) -> list[BookSummary]:
    """Portada: sin sesión, o con sesión pero sin compras pagadas, da lo mismo que a un cliente nuevo.
    Con compras pagadas, se recomienda por afinidad a ellas. Va antes de `/{slug}` para no chocar con esa ruta."""
    purchased_ids = {item.book_id for item in orders.owned_book_items(user.id)} if user is not None else set()
    return catalog.recommended_books(purchased_ids, limit)


@router.get("/{slug}", response_model=BookDetail)
def get_book(slug: str, catalog: Catalog) -> BookDetail:
    book = catalog.get_book(slug)
    if book is None:
        raise HTTPException(404, "Libro no encontrado")
    return book


@router.get("/{slug}/related", response_model=list[BookSummary])
def related_books(
    slug: str, catalog: Catalog, limit: Annotated[int, Query(ge=1, le=24)] = 6
) -> list[BookSummary]:
    related = catalog.related_books(slug, limit)
    if related is None:
        raise HTTPException(404, "Libro no encontrado")
    return related


@router.get("/{slug}/reviews", response_model=list[ReviewOut])
def book_reviews(slug: str, catalog: Catalog) -> list[ReviewOut]:
    reviews = catalog.book_reviews(slug)
    if reviews is None:
        raise HTTPException(404, "Libro no encontrado")
    return reviews

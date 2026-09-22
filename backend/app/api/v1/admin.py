import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status

from app.api.v1.orders import to_order_out
from app.config import settings
from app.core.deps import get_admin_service, get_review_service, require_admin
from app.core.images import MAX_UPLOAD_BYTES, InvalidImage, open_upload, save_cover
from app.domain.models import Book, Order, User
from app.schemas.admin import (
    AdminBookOut,
    AdminBookPage,
    AdminOrderOut,
    BookCreateIn,
    BookUpdateIn,
    CoverUploadOut,
    CustomerOut,
    StatusChangeIn,
    SummaryOut,
)
from app.schemas.catalog import ReviewOut
from app.services.admin_service import AdminError, AdminService
from app.services.review_service import ReviewError, ReviewService
from app.services.review_service import to_out as to_review_out

# Todo lo de este router exige rol administrador (401 sin sesión, 403 para clientes).
router = APIRouter(prefix="/admin", tags=["administración"], dependencies=[Depends(require_admin)])

Admin = Annotated[AdminService, Depends(get_admin_service)]

_ERROR_STATUS = {"not_found": 404, "invalid_category": 422, "invalid_transition": 409}


def _fail(error: AdminError) -> HTTPException:
    return HTTPException(_ERROR_STATUS.get(error.code, 400), {"code": error.code, "message": error.message})


def to_book_out(book: Book, admin: AdminService, author_name: str | None = None) -> AdminBookOut:
    return AdminBookOut(
        id=book.id,
        slug=book.slug,
        title=book.title,
        author_name=author_name if author_name is not None else admin.author_name_of(book),
        category_ids=book.category_ids,
        isbn=book.isbn,
        publisher=book.publisher,
        pages=book.pages,
        language=book.language,
        description=book.description,
        price_cop=book.price_cop,
        discount_pct=book.discount_pct,
        final_price_cop=admin.final_price_of(book),
        shipping_cost_cop=book.shipping_cost_cop,
        stock=book.stock,
        cover=book.cover,
        cover_width=book.cover_width,
        cover_height=book.cover_height,
        featured=book.featured,
        bestseller=book.bestseller,
        active=book.active,
        incomplete=book.incomplete,
        created_at=book.created_at,
    )


def to_admin_order_out(order: Order, customer: User | None) -> AdminOrderOut:
    base = to_order_out(order).model_dump()
    who = CustomerOut(name=f"{customer.first_name} {customer.last_name}", email=customer.email) if customer else None
    return AdminOrderOut(**base, customer=who)


# -- resumen -------------------------------------------------------------------------------------------


@router.get("/summary", response_model=SummaryOut)
def summary(admin: Admin) -> SummaryOut:
    return SummaryOut(**admin.summary())


# -- libros --------------------------------------------------------------------------------------------


@router.get("/books", response_model=AdminBookPage)
def list_books(
    admin: Admin,
    q: Annotated[str | None, Query(max_length=100)] = None,
    active: bool | None = None,
    low_stock: bool = False,
    sort: Annotated[str | None, Query(pattern="^(stock_asc|stock_desc)$")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AdminBookPage:
    books, total, authors = admin.list_books(q, active, low_stock, sort, page, page_size)
    return AdminBookPage(
        items=[to_book_out(b, admin, authors.get(b.author_id, "—")) for b in books],
        total=total,
        page=page,
        page_size=page_size,
        pages=admin.pages(total, page_size),
        authors=admin.author_names(),
    )


@router.get("/books/{book_id}", response_model=AdminBookOut)
def get_book(book_id: str, admin: Admin) -> AdminBookOut:
    book = admin.get_book(book_id)
    if book is None:
        raise HTTPException(404, {"code": "not_found", "message": "Libro no encontrado"})
    return to_book_out(book, admin)


@router.post("/books", response_model=AdminBookOut, status_code=status.HTTP_201_CREATED)
def create_book(body: BookCreateIn, admin: Admin) -> AdminBookOut:
    try:
        return to_book_out(admin.create_book(body), admin)
    except AdminError as error:
        raise _fail(error) from None


@router.patch("/books/{book_id}", response_model=AdminBookOut)
def update_book(book_id: str, body: BookUpdateIn, admin: Admin) -> AdminBookOut:
    try:
        return to_book_out(admin.update_book(book_id, body), admin)
    except AdminError as error:
        raise _fail(error) from None


@router.post("/uploads/cover", response_model=CoverUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_cover(file: Annotated[UploadFile, File()]) -> CoverUploadOut:
    """Valida una imagen, la convierte a webp y la guarda con un nombre aleatorio (nunca el del archivo subido)."""
    # Se lee un byte de más para saber si se pasa del límite sin cargar archivos enormes enteros en memoria.
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    try:
        image = open_upload(data)
    except InvalidImage as error:
        raise HTTPException(422, {"code": "invalid_image", "message": str(error)}) from None

    name = f"{uuid.uuid4().hex}.webp"
    width, height, blur = save_cover(image, settings.media_dir / "covers" / name)
    return CoverUploadOut(cover=f"/media/covers/{name}", cover_width=width, cover_height=height, cover_blur=blur)


# -- moderación de reseñas -------------------------------------------------------------------------------


@router.get("/books/{book_id}/reviews", response_model=list[ReviewOut])
def book_reviews(book_id: str, reviews: Annotated[ReviewService, Depends(get_review_service)]) -> list[ReviewOut]:
    """Todas las reseñas de un libro (también las de muestra), para poder retirar una."""
    return [to_review_out(r) for r in reviews.admin_list(book_id)]


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: str, reviews: Annotated[ReviewService, Depends(get_review_service)]) -> Response:
    try:
        reviews.admin_delete(review_id)
    except ReviewError as error:
        raise HTTPException(404, {"code": error.code, "message": error.message}) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- pedidos -------------------------------------------------------------------------------------------


@router.get("/orders")
def list_orders(
    admin: Admin,
    status_filter: Annotated[str | None, Query(alias="status", pattern="^(pending|paid|failed|shipped|delivered|cancelled)$")] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    rows, total = admin.list_orders(status_filter, q, page, page_size)
    return {
        "items": [to_admin_order_out(order, customer).model_dump(mode="json") for order, customer in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": admin.pages(total, page_size),
    }


@router.get("/orders/{order_id}", response_model=AdminOrderOut)
def get_order(order_id: str, admin: Admin) -> AdminOrderOut:
    found = admin.get_order(order_id)
    if found is None:
        raise HTTPException(404, {"code": "not_found", "message": "Pedido no encontrado"})
    return to_admin_order_out(*found)


@router.post("/orders/{order_id}/status", response_model=AdminOrderOut)
def change_status(order_id: str, body: StatusChangeIn, admin: Admin) -> AdminOrderOut:
    try:
        admin.change_order_status(order_id, body.status)
    except AdminError as error:
        raise _fail(error) from None
    return to_admin_order_out(*admin.get_order(order_id))  # type: ignore[misc]

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.domain.models import Author, Book, Cart, Category, Order, Review, User, Wishlist
from app.payments.mock_provider import MockPaymentProvider
from app.repositories.json_repo import JsonRepository
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.cart_service import CartService
from app.services.cart_storage import CartStorage
from app.services.wishlist_service import WishlistService
from app.services.catalog_service import CatalogService
from app.services.order_service import OrderService
from app.services.review_service import ReviewService


@lru_cache
def get_catalog_service() -> CatalogService:
    """Una sola instancia por proceso. En tests se sustituye con `app.dependency_overrides`."""
    data = settings.data_dir
    return CatalogService(
        books=JsonRepository(data / "books.json", Book),
        authors=JsonRepository(data / "authors.json", Author),
        categories=JsonRepository(data / "categories.json", Category),
        reviews=JsonRepository(data / "reviews.json", Review),
    )


def get_cart_service() -> CartService:
    return CartService(get_catalog_service())


@lru_cache
def get_auth_service() -> AuthService:
    # Una sola instancia: el limitador de intentos vive en ella.
    return AuthService(
        users=JsonRepository(settings.data_dir / "users.json", User),
        secret=settings.jwt_secret,
        expires_minutes=settings.jwt_expire_minutes,
    )


@lru_cache
def get_cart_storage() -> CartStorage:
    return CartStorage(get_catalog_service(), JsonRepository(settings.data_dir / "carts.json", Cart))


@lru_cache
def get_order_service() -> OrderService:
    """Una sola instancia: su candado es lo que evita vender de más y cobrar dos veces."""
    data = settings.data_dir
    return OrderService(
        orders=JsonRepository(data / "orders.json", Order),
        books=JsonRepository(data / "books.json", Book),
        cart=get_cart_service(),
        cart_storage=get_cart_storage(),
        payments=MockPaymentProvider(delay_seconds=settings.payment_delay_seconds),
    )


@lru_cache
def get_admin_service() -> AdminService:
    data = settings.data_dir
    return AdminService(
        books=JsonRepository(data / "books.json", Book),
        authors=JsonRepository(data / "authors.json", Author),
        categories=JsonRepository(data / "categories.json", Category),
        orders=JsonRepository(data / "orders.json", Order),
        users=JsonRepository(data / "users.json", User),
    )


@lru_cache
def get_wishlist_service() -> WishlistService:
    return WishlistService(get_catalog_service(), JsonRepository(settings.data_dir / "wishlists.json", Wishlist))


@lru_cache
def get_review_service() -> ReviewService:
    data = settings.data_dir
    return ReviewService(
        reviews=JsonRepository(data / "reviews.json", Review),
        books=JsonRepository(data / "books.json", Book),
        orders=JsonRepository(data / "orders.json", Order),
    )


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Usuario de la sesión, o 401. El token llega como `Authorization: Bearer …`."""
    user = auth.user_from_token(credentials.credentials) if credentials else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Sesión no válida o caducada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    """Como `get_current_user` pero sin exigir sesión: para endpoints públicos que se personalizan si hay token."""
    return auth.user_from_token(credentials.credentials) if credentials else None


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere permisos de administrador")
    return user

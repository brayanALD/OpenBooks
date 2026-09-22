"""Entorno de pruebas para pedidos: catálogo pequeño, repositorios en memoria y una pasarela que cuenta cobros."""

import time
from dataclasses import dataclass, field

from app.domain.models import Author, Book, Cart, Category, Order, User
from app.payments.base import CardDetails, PaymentProvider, PaymentResult
from app.payments.mock_provider import MockPaymentProvider
from app.repositories.memory_repo import InMemoryRepository
from app.schemas.auth import AddressIn, RegisterIn
from app.schemas.cart import CartItemIn
from app.schemas.orders import CardIn, CheckoutIn, ShippingIn
from app.services.auth_service import AuthService
from app.services.cart_service import CartService
from app.services.cart_storage import CartStorage
from app.services.catalog_service import CatalogService
from app.services.order_service import OrderService
from tests.conftest import make_book

GOOD_CARD = "4242 4242 4242 4242"
DECLINED_CARD = "4000 0000 0000 0002"
NO_FUNDS_CARD = "4000 0000 0000 9995"


class CountingProvider(PaymentProvider):
    """Envuelve otra pasarela y cuenta los cobros; `delay` alarga el cobro para probar peticiones simultáneas."""

    name = "mock"

    def __init__(self, inner: PaymentProvider | None = None, delay: float = 0.0, fail_with: Exception | None = None):
        self.inner = inner or MockPaymentProvider()
        self.delay = delay
        self.fail_with = fail_with
        self.charges: list[tuple[int, str]] = []

    def charge(self, amount_cop: int, card: CardDetails, order_ref: str) -> PaymentResult:
        self.charges.append((amount_cop, order_ref))
        if self.delay:
            time.sleep(self.delay)
        if self.fail_with:
            raise self.fail_with
        return self.inner.charge(amount_cop, card, order_ref)


@dataclass
class Env:
    orders: InMemoryRepository
    books: InMemoryRepository
    storage: CartStorage
    service: OrderService
    provider: CountingProvider
    auth: AuthService
    catalog: CatalogService
    users: list[User] = field(default_factory=list)

    def stock(self, book_id: str) -> int:
        return self.books.get(book_id).stock

    def new_user(self, email: str = "ana@correo.com") -> User:
        user = self.auth.register(
            RegisterIn(
                first_name="Ana",
                last_name="Pérez",
                email=email,
                address=AddressIn(line="Calle 10 # 5-20", city="Bogotá"),
                password="clave-segura-1",
            )
        )
        self.users.append(user)
        return user


def build_env(provider: CountingProvider | None = None) -> Env:
    books = InMemoryRepository[Book](
        [
            make_book("b1", "Barato", "a1", ["c1"], price_cop=10_000, stock=20),  # envío gratis
            make_book("b2", "Con descuento", "a1", ["c1"], price_cop=100_000, discount_pct=20, shipping_cost_cop=5_000, stock=20),
            make_book("b3", "Ultima unidad", "a1", ["c1"], price_cop=30_000, stock=1),
            make_book("b4", "Agotado", "a1", ["c1"], price_cop=50_000, stock=0),
        ]
    )
    catalog = CatalogService(
        books,
        InMemoryRepository([Author(id="a1", name="Autora Uno", slug="autora-uno")]),
        InMemoryRepository([Category(id="c1", name="Novela", slug="novela")]),
        InMemoryRepository([]),
    )
    storage = CartStorage(catalog, InMemoryRepository[Cart]([]))
    provider = provider or CountingProvider()
    orders = InMemoryRepository[Order]([])
    service = OrderService(orders, books, CartService(catalog), storage, provider)
    auth = AuthService(InMemoryRepository[User]([]), "un-secreto-de-prueba-suficientemente-largo-123", 60)
    return Env(orders, books, storage, service, provider, auth, catalog)


def checkout_data(items, *, card: str = GOOD_CARD, key: str = "clave-unica-0001", total: int | None = None, cvc: str = "123") -> CheckoutIn:
    """`total=None` calcula el total esperado a partir de los precios del catálogo de pruebas."""
    if total is None:
        prices = {"b1": (10_000, 0), "b2": (80_000, 5_000), "b3": (30_000, 0), "b4": (50_000, 0)}
        subtotal = sum(prices[b][0] * q for b, q in items)
        shipping = max((prices[b][1] for b, _ in items), default=0)
        total = subtotal + shipping
    return CheckoutIn(
        items=[CartItemIn(book_id=b, quantity=q) for b, q in items],
        shipping=ShippingIn(recipient_name="Ana Pérez", phone="300 123 4567", line="Calle 10 # 5-20", city="Bogotá", notes="Torre 2"),
        card=CardIn(number=card, cvc=cvc, holder="ANA PEREZ", exp_month=12, exp_year=2035),
        idempotency_key=key,
        expected_total_cop=total,
    )

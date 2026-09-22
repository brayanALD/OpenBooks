import logging
from contextlib import AbstractContextManager
from datetime import datetime, timezone

from app.core.locks import inventory_lock
from app.domain.models import Book, Order, OrderItem, PaymentRecord, ShippingInfo, User
from app.payments.base import CardDetails, PaymentProvider
from app.repositories.base import Repository
from app.schemas.cart import CartOut
from app.schemas.orders import CheckoutIn
from app.services.cart_service import CartService
from app.services.cart_storage import CartStorage

log = logging.getLogger(__name__)

PAYMENT_ERROR = "No se pudo procesar el pago. Inténtalo de nuevo."


class CheckoutError(Exception):
    """El pedido no se puede crear tal como llegó. `code` lo traduce la API a un mensaje para el usuario."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class OrderService:
    """Convierte un carrito en un pedido pagado, sin vender más de lo que hay ni cobrar dos veces.

    Secuencia (el candado protege los pasos que tocan stock y pedidos, no el cobro):
      1. Bajo candado: idempotencia, validación contra el catálogo, reserva de stock y pedido «pending».
      2. Sin candado: cobro (puede tardar; no bloquea a otros compradores).
      3. Bajo candado: si se aprobó -> «paid» y carrito vaciado; si no -> se devuelve el stock y «failed».

    Límite conocido: si el proceso muere entre 1 y 3, el pedido queda «pending» con stock reservado.
    Y el candado solo vale para un proceso (un único worker), igual que el almacenamiento JSON.
    """

    def __init__(
        self,
        orders: Repository[Order],
        books: Repository[Book],
        cart: CartService,
        cart_storage: CartStorage,
        payments: PaymentProvider,
        lock: AbstractContextManager | None = None,
    ) -> None:
        self._orders = orders
        self._books = books
        self._cart = cart
        self._cart_storage = cart_storage
        self._payments = payments
        # Compartido con el panel de administración: ver app/core/locks.py.
        self._lock = lock or inventory_lock

    # -- consulta --------------------------------------------------------------------------------

    def list_for_user(self, user_id: str) -> list[Order]:
        mine = [o for o in self._orders.list() if o.user_id == user_id]
        # El número de pedido desempata: dos pedidos pueden compartir el mismo instante de reloj.
        return sorted(mine, key=lambda o: (o.created_at, int(o.number.removeprefix("OB-"))), reverse=True)

    def get_for_user(self, order_id: str, user_id: str) -> Order | None:
        """Solo devuelve pedidos propios: para cualquier otro es como si no existiera."""
        order = self._orders.get(order_id)
        return order if order and order.user_id == user_id else None

    # -- compra ----------------------------------------------------------------------------------

    def checkout(self, user: User, data: CheckoutIn) -> tuple[Order, bool]:
        """Devuelve (pedido, creado). `creado` es False si la clave de idempotencia ya existía."""
        order, created = self._reserve(user, data)
        if not created:
            # Repetición de una petición anterior (doble clic, recarga): se devuelve el pedido tal como esté,
            # incluso si el primer intento todavía está cobrando. Nunca se cobra dos veces.
            return order, False
        return self._charge_and_settle(user, order, data), True

    def _reserve(self, user: User, data: CheckoutIn) -> tuple[Order, bool]:
        with self._lock:
            existing = next(
                (o for o in self._orders.list() if o.user_id == user.id and o.idempotency_key == data.idempotency_key),
                None,
            )
            if existing is not None:
                return existing, False

            cart = self._cart.validate(data.items)
            self._ensure_buyable(cart, data.expected_total_cop)

            lines = [line for line in cart.lines if line.quantity > 0]
            reserved: list[tuple[Book, int]] = []
            for line in lines:
                book = self._books.get(line.book.id)
                if book is None or book.stock < line.quantity:  # ya validado; defensa ante carreras
                    self._release(reserved)
                    raise CheckoutError("cart_issues", "Algún libro ya no tiene unidades suficientes.")
                self._books.update(book.model_copy(update={"stock": book.stock - line.quantity}))
                reserved.append((book, line.quantity))

            sequence = self._next_number()
            order = Order(
                id=f"ord_{sequence:06d}",
                number=f"OB-{sequence:06d}",
                user_id=user.id,
                idempotency_key=data.idempotency_key,
                items=[
                    OrderItem(
                        book_id=line.book.id,
                        title=line.book.title,
                        author_name=line.book.author.name,
                        cover=line.book.cover,
                        unit_price_cop=line.unit_price_cop,
                        quantity=line.quantity,
                        line_total_cop=line.line_total_cop,
                    )
                    for line in lines
                ],
                subtotal_cop=cart.subtotal_cop,
                shipping_cop=cart.shipping_cop,
                total_cop=cart.total_cop,
                shipping=ShippingInfo(**data.shipping.model_dump()),
                payment=PaymentRecord(provider=self._payments.name, status="pending"),
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            return self._orders.add(order), True

    @staticmethod
    def _ensure_buyable(cart: CartOut, expected_total: int) -> None:
        if cart.unavailable_ids or any(line.issue for line in cart.lines):
            raise CheckoutError(
                "cart_issues",
                "Algunos libros de tu carrito ya no están disponibles en la cantidad pedida. Revisa tu carrito.",
            )
        if not any(line.quantity > 0 for line in cart.lines):
            raise CheckoutError("empty_cart", "Tu carrito está vacío.")
        if cart.total_cop != expected_total:
            raise CheckoutError("total_changed", "Los precios cambiaron mientras comprabas. Revisa el nuevo total.")

    def _charge_and_settle(self, user: User, order: Order, data: CheckoutIn) -> Order:
        card = CardDetails(
            number=data.card.number.get_secret_value(),
            cvc=data.card.cvc.get_secret_value(),
            exp_month=data.card.exp_month,
            exp_year=data.card.exp_year,
            holder=data.card.holder,
        )
        try:
            result = self._payments.charge(order.total_cop, card, order.number)
        except Exception:  # noqa: BLE001 - cualquier fallo de la pasarela cuenta como pago no realizado
            log.exception("Fallo de la pasarela al cobrar el pedido %s", order.number)
            return self._settle_failed(order, None, None, PAYMENT_ERROR)

        method = f"{result.brand} •••• {result.last4}"
        if not result.approved:
            return self._settle_failed(order, result.reference, method, result.failure_reason or PAYMENT_ERROR)

        with self._lock:
            paid = order.model_copy(
                update={
                    "status": "paid",
                    "payment": PaymentRecord(
                        provider=self._payments.name, status="approved", reference=result.reference, method=method
                    ),
                }
            )
            self._orders.update(paid)
            self._cart_storage.replace(user.id, [])  # el carrito guardado ya se convirtió en pedido
            return paid

    def _settle_failed(self, order: Order, reference: str | None, method: str | None, reason: str) -> Order:
        with self._lock:
            self._release([(self._books.get(i.book_id), i.quantity) for i in order.items])
            failed = order.model_copy(
                update={
                    "status": "failed",
                    "payment": PaymentRecord(
                        provider=self._payments.name,
                        status="declined",
                        reference=reference,
                        method=method,
                        failure_reason=reason,
                    ),
                }
            )
            return self._orders.update(failed)

    # -- utilidades (llamar con el candado tomado) ----------------------------------------------------

    def _release(self, reserved: list[tuple[Book | None, int]]) -> None:
        """Devuelve al inventario lo reservado. Relee cada libro: el stock pudo cambiar desde la reserva."""
        for book, quantity in reserved:
            if book is None:
                continue
            current = self._books.get(book.id)
            if current is not None:
                self._books.update(current.model_copy(update={"stock": current.stock + quantity}))

    def _next_number(self) -> int:
        numbers = [int(o.number.removeprefix("OB-")) for o in self._orders.list()]
        return max(numbers, default=0) + 1

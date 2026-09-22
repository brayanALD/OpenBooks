import time
import uuid

from app.payments.base import CardDetails, PaymentProvider, PaymentResult

# Tarjetas de prueba (mismas ideas que las de Stripe). Cualquier otra se rechaza a propósito.
APPROVED_CARDS = {
    "4242424242424242": "Visa",
    "5555555555554444": "Mastercard",
}
DECLINED_CARDS = {
    "4000000000000002": "La tarjeta fue rechazada por el banco.",
    "4000000000009995": "Fondos insuficientes.",
    "4000000000000069": "La tarjeta está vencida.",
    "4000000000000127": "El código de seguridad (CVC) es incorrecto.",
}
UNKNOWN_CARD = "Tarjeta no reconocida en el modo de prueba. Usa una de las tarjetas de prueba indicadas."


def brand_of(number: str) -> str:
    if number.startswith("4"):
        return "Visa"
    if number[:2] in {"51", "52", "53", "54", "55"} or number.startswith("2"):
        return "Mastercard"
    return "Tarjeta"


class MockPaymentProvider(PaymentProvider):
    """Pasarela simulada: no mueve dinero. La tarjeta decide el resultado; hay una espera para que se sienta real."""

    name = "mock"

    def __init__(self, delay_seconds: float = 0.0) -> None:
        self._delay = delay_seconds

    def charge(self, amount_cop: int, card: CardDetails, order_ref: str) -> PaymentResult:
        if self._delay > 0:
            time.sleep(self._delay)

        number = card.number
        reference = f"mock_{uuid.uuid4().hex[:12]}"
        brand = APPROVED_CARDS.get(number) or brand_of(number)
        last4 = number[-4:]

        if number in APPROVED_CARDS:
            return PaymentResult(True, reference, brand, last4)
        reason = DECLINED_CARDS.get(number, UNKNOWN_CARD)
        return PaymentResult(False, reference, brand, last4, failure_reason=reason)

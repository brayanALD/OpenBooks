from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CardDetails:
    # `repr=False`: si algún día se imprime o se registra este objeto, el número y el CVC no salen.
    number: str = field(repr=False)
    cvc: str = field(repr=False)
    exp_month: int
    exp_year: int
    holder: str


@dataclass(frozen=True)
class PaymentResult:
    approved: bool
    reference: str
    brand: str
    last4: str
    failure_reason: str | None = None


class PaymentProvider(ABC):
    """Puerto de pagos. El servicio de pedidos solo conoce esta interfaz.

    Una pasarela real (Mercado Pago, Wompi, Stripe) será otro adaptador. Ojo: con una pasarela real la
    tarjeta NO debe pasar por este servidor; se tokeniza en el navegador y aquí solo llega el token.
    """

    name: str

    @abstractmethod
    def charge(self, amount_cop: int, card: CardDetails, order_ref: str) -> PaymentResult: ...

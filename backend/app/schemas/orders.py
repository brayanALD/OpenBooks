import re
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, SecretStr, StringConstraints, field_validator, model_validator

from app.domain.rules import MAX_CART_LINES
from app.schemas.auth import normalize_phone
from app.schemas.cart import CartItemIn

Text = Annotated[str, StringConstraints(strip_whitespace=True)]


def luhn_valid(digits: str) -> bool:
    """Suma de verificación de las tarjetas: descarta números mal escritos antes de cobrar."""
    total = 0
    for index, char in enumerate(reversed(digits)):
        n = int(char)
        if index % 2 == 1:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
    return total % 10 == 0


class CardIn(BaseModel):
    # SecretStr: al imprimir o registrar este objeto salen asteriscos, no el número ni el CVC.
    number: SecretStr
    cvc: SecretStr
    holder: Annotated[Text, Field(min_length=2, max_length=80)]
    exp_month: Annotated[int, Field(ge=1, le=12)]
    exp_year: int

    @field_validator("number", mode="before")
    @classmethod
    def _clean_number(cls, value: object) -> object:
        return re.sub(r"[\s-]", "", value) if isinstance(value, str) else value

    @field_validator("number")
    @classmethod
    def _check_number(cls, value: SecretStr) -> SecretStr:
        digits = value.get_secret_value()
        if not digits.isdigit() or not 13 <= len(digits) <= 19 or not luhn_valid(digits):
            raise ValueError("Número de tarjeta inválido")
        return value

    @field_validator("cvc")
    @classmethod
    def _check_cvc(cls, value: SecretStr) -> SecretStr:
        if not re.fullmatch(r"\d{3,4}", value.get_secret_value()):
            raise ValueError("El CVC debe tener 3 o 4 dígitos")
        return value

    @field_validator("exp_year")
    @classmethod
    def _four_digit_year(cls, year: int) -> int:
        year = 2000 + year if 0 <= year < 100 else year  # acepta "28" y "2028"
        if not 2000 <= year <= 2100:
            raise ValueError("Año de vencimiento inválido")
        return year

    @model_validator(mode="after")
    def _not_expired(self) -> "CardIn":
        today = date.today()
        if (self.exp_year, self.exp_month) < (today.year, today.month):
            raise ValueError("La tarjeta está vencida")
        return self


class ShippingIn(BaseModel):
    recipient_name: Annotated[Text, Field(min_length=2, max_length=100)]
    phone: str | None = None
    line: Annotated[Text, Field(min_length=5, max_length=120)]
    city: Annotated[Text, Field(min_length=2, max_length=60)]
    notes: Annotated[Text, Field(max_length=200)] | None = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("notes")
    @classmethod
    def _blank_notes(cls, value: str | None) -> str | None:
        return value or None


class CheckoutIn(BaseModel):
    items: Annotated[list[CartItemIn], Field(min_length=1, max_length=MAX_CART_LINES)]
    shipping: ShippingIn
    card: CardIn
    # Uno por intento de pago: si la petición se repite (doble clic, recarga), no se cobra dos veces.
    idempotency_key: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")]
    # Total que el usuario vio en pantalla: si los precios cambiaron mientras tanto, no se cobra otra cifra.
    expected_total_cop: Annotated[int, Field(ge=0)]


class OrderItemOut(BaseModel):
    book_id: str
    title: str
    author_name: str
    cover: str
    unit_price_cop: int
    quantity: int
    line_total_cop: int


class ShippingOut(BaseModel):
    recipient_name: str
    phone: str | None
    line: str
    city: str
    notes: str | None


class PaymentOut(BaseModel):
    status: str
    method: str | None
    reference: str | None
    failure_reason: str | None


class OrderOut(BaseModel):
    id: str
    number: str
    status: str
    items: list[OrderItemOut]
    subtotal_cop: int
    shipping_cop: int
    total_cop: int
    shipping: ShippingOut
    payment: PaymentOut
    created_at: datetime

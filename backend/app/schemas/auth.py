import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True)]

_PHONE_DIGITS = re.compile(r"^3\d{9}$")  # celular colombiano: 10 dígitos que empiezan por 3


def normalize_phone(value: str | None) -> str | None:
    """Acepta '300 123 4567', '+57 300-123-4567'… y devuelve 10 dígitos. Vacío -> None; inválido -> ValueError."""
    if value is None or not value.strip():
        return None
    digits = re.sub(r"[\s\-().]", "", value)
    digits = digits.removeprefix("+57").removeprefix("57") if len(digits) > 10 else digits
    if not _PHONE_DIGITS.match(digits):
        raise ValueError("El celular debe tener 10 dígitos y empezar por 3")
    return digits


class AddressIn(BaseModel):
    line: Annotated[Text, Field(min_length=5, max_length=120)]
    city: Annotated[Text, Field(min_length=2, max_length=60)]
    notes: Annotated[Text, Field(max_length=200)] | None = None

    @field_validator("notes")
    @classmethod
    def _blank_notes_to_none(cls, value: str | None) -> str | None:
        return value or None


class RegisterIn(BaseModel):
    first_name: Annotated[Text, Field(min_length=1, max_length=60)]
    last_name: Annotated[Text, Field(min_length=1, max_length=60)]
    email: EmailStr
    phone: str | None = None
    address: AddressIn
    password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class LoginIn(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


class AddressOut(BaseModel):
    line: str
    city: str
    notes: str | None


class UserOut(BaseModel):
    """Lo que se puede mostrar de un usuario. Nunca incluye el hash de la contraseña."""

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    address: AddressOut
    role: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

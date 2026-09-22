import pytest

from app.repositories.memory_repo import InMemoryRepository
from app.schemas.auth import AddressIn, RegisterIn
from app.services.auth_service import (
    AuthService,
    EmailTaken,
    InvalidCredentials,
    LoginThrottle,
    TooManyAttempts,
)

SECRET = "un-secreto-de-prueba-suficientemente-largo-123"


def register_data(**overrides) -> RegisterIn:
    fields = dict(
        first_name="Ana",
        last_name="Pérez",
        email="Ana@Correo.com",
        phone="300 123 4567",
        address=AddressIn(line="Calle 10 # 5-20", city="Bogotá", notes="Torre 2"),
        password="clave-segura-1",
    )
    fields.update(overrides)
    return RegisterIn(**fields)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def auth(clock):
    return AuthService(InMemoryRepository([]), SECRET, 60, LoginThrottle(max_attempts=3, window=60, clock=clock))


# -- registro -------------------------------------------------------------------------------------


def test_register_normalizes_and_hashes(auth):
    user = auth.register(register_data())
    assert user.email == "ana@correo.com"  # minúsculas
    assert user.phone == "3001234567"  # solo dígitos
    assert user.role == "customer"
    assert user.password_hash.startswith("$argon2") and "clave-segura-1" not in user.password_hash
    assert user.address.city == "Bogotá" and user.address.notes == "Torre 2"


def test_duplicate_email_is_rejected_ignoring_case_and_spaces(auth):
    auth.register(register_data())
    with pytest.raises(EmailTaken):
        auth.register(register_data(email="ANA@correo.COM"))


def test_admin_role_can_only_be_set_by_the_service_not_the_payload(auth):
    assert auth.register(register_data(email="a@correo.com"), role="admin").role == "admin"
    assert auth.register(register_data(email="b@correo.com")).role == "customer"


@pytest.mark.parametrize(
    "phone, expected",
    [
        ("3001234567", "3001234567"),
        ("300 123 4567", "3001234567"),
        ("+57 300-123-4567", "3001234567"),
        ("573001234567", "3001234567"),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_phone_normalization(phone, expected):
    assert register_data(phone=phone).phone == expected


@pytest.mark.parametrize("phone", ["12345", "2001234567", "30012345678901", "abc", "3001234"])
def test_invalid_phone_is_rejected(phone):
    with pytest.raises(ValueError):
        register_data(phone=phone)


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "corta"},
        {"password": "x" * 129},
        {"email": "no-es-un-correo"},
        {"first_name": "   "},
        {"last_name": ""},
        {"address": {"line": "Cll 1", "city": "B"}},
    ],
)
def test_invalid_registration_is_rejected(overrides):
    with pytest.raises(ValueError):
        register_data(**overrides)


# -- inicio de sesión ---------------------------------------------------------------------------------


def test_login_with_correct_password_ignores_email_case(auth):
    user = auth.register(register_data())
    assert auth.authenticate("ANA@correo.com ", "clave-segura-1").id == user.id


def test_wrong_password_and_unknown_email_raise_the_same_error(auth):
    auth.register(register_data())
    with pytest.raises(InvalidCredentials):
        auth.authenticate("ana@correo.com", "incorrecta")
    with pytest.raises(InvalidCredentials):
        auth.authenticate("nadie@correo.com", "clave-segura-1")


def test_throttle_blocks_after_max_failures_even_with_the_right_password(auth):
    auth.register(register_data())
    for _ in range(3):
        with pytest.raises(InvalidCredentials):
            auth.authenticate("ana@correo.com", "mala")
    with pytest.raises(TooManyAttempts) as blocked:
        auth.authenticate("ana@correo.com", "clave-segura-1")
    assert 1 <= blocked.value.retry_after <= 61


def test_throttle_expires_after_the_window(auth, clock):
    auth.register(register_data())
    for _ in range(3):
        with pytest.raises(InvalidCredentials):
            auth.authenticate("ana@correo.com", "mala")
    clock.now += 61
    assert auth.authenticate("ana@correo.com", "clave-segura-1").email == "ana@correo.com"


def test_successful_login_resets_the_counter(auth):
    auth.register(register_data())
    for _ in range(2):
        with pytest.raises(InvalidCredentials):
            auth.authenticate("ana@correo.com", "mala")
    auth.authenticate("ana@correo.com", "clave-segura-1")
    for _ in range(2):  # otra vez hasta 2 fallos sin bloqueo
        with pytest.raises(InvalidCredentials):
            auth.authenticate("ana@correo.com", "mala")


def test_throttle_is_per_email(auth):
    auth.register(register_data())
    for _ in range(3):
        with pytest.raises(InvalidCredentials):
            auth.authenticate("otro@correo.com", "mala")
    assert auth.authenticate("ana@correo.com", "clave-segura-1")  # otro correo no afectado


# -- tokens ------------------------------------------------------------------------------------------


def test_token_resolves_to_the_user_and_dies_with_the_account(auth):
    user = auth.register(register_data())
    token = auth.create_token(user)
    assert auth.user_from_token(token).id == user.id
    auth._users.delete(user.id)
    assert auth.user_from_token(token) is None

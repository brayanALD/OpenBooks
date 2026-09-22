import base64
import json

import pytest

from app.config import Settings
from app.core import security

SECRET = "un-secreto-de-prueba-suficientemente-largo-123"


def test_hash_is_salted_and_verifies():
    a, b = security.hash_password("clave-segura-1"), security.hash_password("clave-segura-1")
    assert a != b and a.startswith("$argon2")
    assert security.verify_password(a, "clave-segura-1")
    assert not security.verify_password(a, "otra-clave")


def test_verify_never_raises_on_garbage_hash():
    assert security.verify_password("no-es-un-hash", "x") is False


def test_token_roundtrip():
    token = security.create_access_token("usr_1", SECRET, 5)
    assert security.decode_access_token(token, SECRET) == "usr_1"


def test_token_with_wrong_secret_is_rejected():
    token = security.create_access_token("usr_1", SECRET, 5)
    assert security.decode_access_token(token, SECRET + "x") is None


def test_expired_token_is_rejected():
    assert security.decode_access_token(security.create_access_token("usr_1", SECRET, -1), SECRET) is None


def test_tampered_token_is_rejected():
    header, payload, signature = security.create_access_token("usr_1", SECRET, 5).split(".")
    forged = base64.urlsafe_b64encode(json.dumps({"sub": "usr_admin", "exp": 9999999999}).encode()).rstrip(b"=").decode()
    assert security.decode_access_token(f"{header}.{forged}.{signature}", SECRET) is None


def test_alg_none_token_is_rejected():
    """Ataque clásico: un token sin firma que declara `alg: none`."""
    b64 = lambda obj: base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()  # noqa: E731
    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': 'usr_1', 'exp': 9999999999})}."
    assert security.decode_access_token(token, SECRET) is None


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c", "....", "Bearer x"])
def test_garbage_tokens_are_rejected(garbage):
    assert security.decode_access_token(garbage, SECRET) is None


def test_production_refuses_the_default_or_a_short_secret():
    with pytest.raises(ValueError):
        Settings(environment="production", _env_file=None)
    with pytest.raises(ValueError):
        Settings(environment="production", jwt_secret="corto", _env_file=None)
    assert Settings(environment="production", jwt_secret="x" * 40, _env_file=None).jwt_secret == "x" * 40
    assert Settings(_env_file=None).environment == "development"  # en desarrollo vale el secreto por defecto

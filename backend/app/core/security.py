from datetime import datetime, timedelta, timezone
from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jose import JWTError, jwt

_hasher = PasswordHasher()
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


@lru_cache
def dummy_hash() -> str:
    """Hash de relleno para gastar el mismo tiempo cuando el correo no existe (evita saber por la
    duración de la respuesta qué correos tienen cuenta)."""
    return hash_password("relleno-no-es-una-contraseña-real")


def create_access_token(user_id: str, secret: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=expires_minutes)}
    return jwt.encode(claims, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> str | None:
    """Devuelve el id de usuario o None si el token es inválido, está manipulado o caducó.

    El algoritmo se fija aquí: nunca se acepta el que declare el propio token.
    """
    try:
        claims = jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except JWTError:
        return None
    sub = claims.get("sub")
    return sub if isinstance(sub, str) and sub else None

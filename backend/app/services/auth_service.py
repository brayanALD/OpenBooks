import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Literal

from app.core import security
from app.domain.models import Address, User
from app.repositories.base import Repository
from app.schemas.auth import RegisterIn


class AuthError(Exception):
    """Base de los errores de autenticación; la API los traduce a códigos HTTP."""


class EmailTaken(AuthError):
    pass


class InvalidCredentials(AuthError):
    """Correo o contraseña incorrectos. Es el mismo error para ambos casos a propósito."""


class TooManyAttempts(AuthError):
    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Demasiados intentos. Inténtalo de nuevo en {retry_after} s")
        self.retry_after = retry_after


def normalize_email(email: str) -> str:
    return email.strip().lower()


class LoginThrottle:
    """Limita los intentos fallidos por correo: `max_attempts` en `window` segundos.

    En memoria y por proceso: sirve para un único worker local. Un login correcto reinicia el contador.
    """

    def __init__(self, max_attempts: int = 5, window: int = 15 * 60, clock=time.monotonic) -> None:
        self._max = max_attempts
        self._window = window
        self._clock = clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str) -> list[float]:
        cutoff = self._clock() - self._window
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def check(self, key: str) -> None:
        with self._lock:
            recent = self._recent(key)
            if len(recent) >= self._max:
                retry_after = int(recent[0] + self._window - self._clock()) + 1
                raise TooManyAttempts(max(retry_after, 1))

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._recent(key)
            self._failures.setdefault(key, []).append(self._clock())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


class AuthService:
    def __init__(
        self,
        users: Repository[User],
        secret: str,
        expires_minutes: int,
        throttle: LoginThrottle | None = None,
    ) -> None:
        self._users = users
        self._secret = secret
        self._expires_minutes = expires_minutes
        self._throttle = throttle or LoginThrottle()
        self._register_lock = threading.Lock()  # el correo debe ser único: comprobar + insertar va junto

    def _find_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.list() if u.email == email), None)

    def register(self, data: RegisterIn, role: Literal["customer", "admin"] = "customer") -> User:
        email = normalize_email(data.email)
        with self._register_lock:
            if self._find_by_email(email) is not None:
                raise EmailTaken(email)
            user = User(
                id=f"usr_{uuid.uuid4().hex[:12]}",
                first_name=data.first_name,
                last_name=data.last_name,
                email=email,
                phone=data.phone,
                address=Address(line=data.address.line, city=data.address.city, notes=data.address.notes),
                password_hash=security.hash_password(data.password),
                role=role,
                created_at=datetime.now(timezone.utc),
            )
            return self._users.add(user)

    def authenticate(self, email: str, password: str) -> User:
        key = normalize_email(email)
        self._throttle.check(key)

        user = self._find_by_email(key)
        # Con o sin usuario se verifica un hash: así la respuesta tarda lo mismo.
        valid = security.verify_password(user.password_hash if user else security.dummy_hash(), password)
        if user is None or not valid:
            self._throttle.record_failure(key)
            raise InvalidCredentials()

        self._throttle.reset(key)
        if security.needs_rehash(user.password_hash):
            user = self._users.update(user.model_copy(update={"password_hash": security.hash_password(password)}))
        return user

    def create_token(self, user: User) -> str:
        return security.create_access_token(user.id, self._secret, self._expires_minutes)

    def user_from_token(self, token: str) -> User | None:
        user_id = security.decode_access_token(token, self._secret)
        return self._users.get(user_id) if user_id else None

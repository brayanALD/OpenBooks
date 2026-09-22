from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_auth_service, get_current_user
from app.domain.models import User
from app.schemas.auth import AddressOut, AuthOut, LoginIn, RegisterIn, UserOut
from app.services.auth_service import AuthService, EmailTaken, InvalidCredentials, TooManyAttempts

router = APIRouter(prefix="/auth", tags=["autenticación"])

Auth = Annotated[AuthService, Depends(get_auth_service)]


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        address=AddressOut(line=user.address.line, city=user.address.city, notes=user.address.notes),
        role=user.role,
    )


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, auth: Auth) -> AuthOut:
    """Crea la cuenta (siempre con rol `customer`) y abre sesión."""
    try:
        user = auth.register(body)
    except EmailTaken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo") from None
    return AuthOut(access_token=auth.create_token(user), user=to_user_out(user))


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, auth: Auth) -> AuthOut:
    try:
        user = auth.authenticate(body.email, body.password)
    except InvalidCredentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos") from None
    except TooManyAttempts as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Demasiados intentos fallidos. Inténtalo de nuevo en {max(1, round(error.retry_after / 60))} min",
            headers={"Retry-After": str(error.retry_after)},
        ) from None
    return AuthOut(access_token=auth.create_token(user), user=to_user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return to_user_out(user)

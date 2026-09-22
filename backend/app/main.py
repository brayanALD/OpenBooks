from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import settings

app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,  # necesario para la cookie httpOnly de sesión
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Errores 422 sin el valor enviado.

    Por defecto FastAPI devuelve `input` con lo que escribió el usuario: en un pago o un registro eso sería el
    número de tarjeta, el CVC o la contraseña, que acabarían en registros de proxies y herramientas de monitorización.
    """
    detail = [{"type": e["type"], "loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/api/v1/health", tags=["sistema"])
def health() -> dict[str, str]:
    return {"status": "ok"}

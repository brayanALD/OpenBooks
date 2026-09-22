from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEV_JWT_SECRET = "dev-only-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "Open Books API"
    environment: str = "development"  # "production" activa las comprobaciones de seguridad
    data_dir: Path = BACKEND_DIR / "data"
    # Origen del frontend permitido por CORS (desarrollo local).
    frontend_origin: str = "http://localhost:3000"
    jwt_secret: str = DEV_JWT_SECRET
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 días; el frontend usa el mismo plazo para su cookie
    # Espera de la pasarela simulada, para que el pago se sienta real. Las pruebas la ponen a 0.
    payment_delay_seconds: float = 0.8

    @property
    def media_dir(self) -> Path:
        """Archivos subidos desde el panel de administración (portadas). Cuelga de `data_dir`: si se aísla
        una copia de los datos con `DATA_DIR`, las subidas de esa copia quedan aisladas con ella."""
        return self.data_dir / "media"

    @model_validator(mode="after")
    def _require_real_secret_in_production(self) -> "Settings":
        if self.environment == "production" and (self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32):
            raise ValueError("En producción JWT_SECRET debe definirse y tener al menos 32 caracteres")
        return self


settings = Settings()

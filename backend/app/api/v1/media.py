import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/media", tags=["archivos"])

# Solo los nombres que genera la subida (uuid hex + .webp): nada de rutas, puntos dobles ni otras extensiones.
_NAME = re.compile(r"^[a-f0-9]{32}\.webp$")


@router.get("/covers/{name}")
def cover(name: str) -> FileResponse:
    if not _NAME.fullmatch(name):
        raise HTTPException(404, "Archivo no encontrado")
    path = settings.media_dir / "covers" / name
    if not path.is_file():
        raise HTTPException(404, "Archivo no encontrado")
    # El nombre es un uuid y el contenido nunca cambia: se puede cachear para siempre.
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000, immutable"})

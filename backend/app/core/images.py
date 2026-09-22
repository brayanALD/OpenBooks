"""Procesado de portadas: lo usan el importador del sitio original y las subidas del panel de administración."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_HEIGHT = 800  # las portadas originales miden ~360 px; solo se reduce la que sea mayor
QUALITY = 82
BLUR_SIZE = (10, 14)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 30_000_000  # una imagen pequeña en bytes puede "descomprimirse" a miles de millones de píxeles
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}  # SVG queda fuera a propósito: puede llevar scripts


class InvalidImage(ValueError):
    """La imagen subida no se puede aceptar. El mensaje está pensado para mostrarse al usuario."""


def open_upload(data: bytes) -> Image.Image:
    """Abre y valida una imagen subida. `Image.open` es perezoso: el tamaño se conoce sin decodificar."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImage("La imagen pesa más de 5 MB.")
    try:
        image = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError):
        raise InvalidImage("El archivo no es una imagen válida.") from None
    if image.format not in ALLOWED_FORMATS:
        raise InvalidImage("Formato no admitido: usa JPG, PNG o WebP.")
    if image.width * image.height > MAX_PIXELS:
        raise InvalidImage("La imagen tiene demasiados píxeles.")
    try:
        image.load()  # detecta archivos truncados o corruptos
    except (OSError, SyntaxError, Image.DecompressionBombError):
        raise InvalidImage("La imagen está dañada.") from None
    return image


def save_cover(image: Image.Image, dest: Path) -> tuple[int, int, str]:
    """Guarda `image` como webp en `dest`. Devuelve (ancho, alto, data URI de baja resolución).

    - Nunca amplía: ampliar una imagen de 360 px no añade calidad, solo peso.
    - Conserva la proporción (sin recortar la portada); el recorte visual lo hace CSS.
    - Aplana los modos raros (paleta, CMYK) a RGB para que webp los acepte.
    """
    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    img = image.convert("RGBA" if has_alpha else "RGB")

    if img.height > MAX_HEIGHT:
        width = round(img.width * MAX_HEIGHT / img.height)
        img = img.resize((width, MAX_HEIGHT), Image.Resampling.LANCZOS)

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "WEBP", quality=QUALITY, method=6)

    tiny = img.copy()
    tiny.thumbnail(BLUR_SIZE, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    tiny.save(buffer, "WEBP", quality=40)
    blur = "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return img.width, img.height, blur


def process_cover(src: Path, dest: Path) -> tuple[int, int, str]:
    """Convierte un archivo de imagen del disco (importador del sitio original)."""
    with Image.open(src) as image:
        image.load()
        return save_cover(image, dest)

"""Genera la portada por defecto (`frontend/public/covers/sin-portada.webp`) para libros creados sin imagen.

Uso (desde backend/):  .venv\\Scripts\\python.exe -m scripts.make_placeholder_cover
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEST = Path(__file__).resolve().parents[2] / "frontend" / "public" / "covers" / "sin-portada.webp"
WIDTH, HEIGHT = 300, 450
BACKGROUND, SPINE, PAPER, INK = "#754c24", "#4a2a12", "#faf5ee", "#2e1708"  # paleta de la marca


def main() -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 26, HEIGHT), fill=SPINE)  # lomo
    draw.rounded_rectangle((70, 90, 250, 250), radius=8, fill=PAPER)  # etiqueta
    for y, w in ((125, 130), (155, 100), (185, 115)):
        draw.rounded_rectangle((90, y, 90 + w, y + 10), radius=5, fill=INK)

    font = ImageFont.load_default(size=26)
    text = "Sin portada"
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((WIDTH + 26 - (box[2] - box[0])) / 2, 300), text, font=font, fill=PAPER)

    DEST.parent.mkdir(parents=True, exist_ok=True)
    img.save(DEST, "WEBP", quality=85)
    print(f"Portada por defecto: {DEST} ({DEST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

"""Importa el catálogo del sitio HTML original a backend/data/*.json y las portadas a frontend/public/covers.

Uso (desde backend/):
    .venv\\Scripts\\python.exe -m scripts.import_legacy [--force]

Sobrescribe books/authors/categories/reviews. Se niega a hacerlo si ya existe un catálogo, salvo con
--force, para no perder ediciones hechas después desde el panel de administración.
Deja un informe de lo que decidió y corrigió en backend/data/import_report.md.
"""

from __future__ import annotations

import json
import re
import sys
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings
from app.core.text import slugify
from app.domain.models import Author, Book, Category, Entity, Review
from scripts.add_catalog import extra_cover_names
from scripts.demo_reviews import DEMO_REVIEWS
from scripts.legacy_parser import LEGACY_HTML, LISTING_CATEGORY, LegacyBook, parse_legacy
from scripts.process_images import process_cover

ROOT = Path(__file__).resolve().parents[2]
LEGACY_IMAGES = ROOT / "legacy" / "imagenes"
COVERS_DIR = ROOT / "frontend" / "public" / "covers"
REPORT_PATH = settings.data_dir / "import_report.md"

# -- Decisiones tomadas con el usuario ---------------------------------------------------------

DISCOUNT_PCT_ON_SALE = 15  # libros de la sección «Libros en Descuento» de la portada
STOCK_MIN, STOCK_SPAN = 3, 28  # stock determinista por libro: 3..30
SHIPPING_ANOMALY_LIMIT = 50_000  # un envío mayor se considera dato de prueba
SHIPPING_ANOMALY_FALLBACK = 5_000  # el envío habitual del sitio

CATEGORY_DEFS = [
    ("clasicos", "Clásicos", "Obras que han resistido el paso del tiempo."),
    ("fantasia", "Fantasía", "Mundos de magia, dragones y aventura."),
    ("novela", "Novela", "Narrativa para todos los gustos: misterio, drama, memoria y más."),
    ("biografias", "Biografías", "Vidas contadas en primera persona o por sus biógrafos."),
    ("historia", "Historia", "Del pasado remoto a la historia reciente."),
    ("desarrollo-personal", "Desarrollo personal", "Ideas y hábitos para crecer personal y profesionalmente."),
]

# Libros que solo aparecían en la portada y no estaban en ningún listado de categoría.
EXTRA_CATEGORIES = {
    "saleCienAnios": ["novela", "clasicos"],
    "saleEnAgosto": ["novela"],
    "salePacienteSilenciosa": ["novela"],
    "saleVagabundos": ["novela"],
    "saleVientoNombre": ["novela"],
    "saleReglonesTrocidos": ["novela"],
    "saleBrujaVerde": ["desarrollo-personal"],
    "saleCCM": ["desarrollo-personal"],
    "saleSinLimite": ["desarrollo-personal"],
}

# -- Normalización de datos sucios del original -------------------------------------------------

TITLE_FIX = {
    "saleAppleMan": "Steve Jobs",
    "saleBrumaTrio": "Trilogía Nacidos de la Bruma",
    "saleBrujaVerde": "El Jardín de la Bruja Verde",
    "saleCCM": "Cabeza, Corazón y Manos",
    "saleDino": "Récords y curiosidades de los dinosaurios",
    "saleHarryPack": "Estuche Harry Potter (7 libros)",
    "saleHombreFeliz": "Autobiografía de un hombre feliz",
    "saleJuegoDeTrono": "Juego de Tronos (Canción de Hielo y Fuego)",
    "saleKobe": "The Mamba Mentality: Los secretos de mi éxito",
    "saleObama": "A Promised Land",
}

AUTHOR_FIX = {
    "Lev N. Tolstói (Leon Tolstói)": "León Tolstói",
    "Lev N. Tolstói": "León Tolstói",
    "Fiódor M. Dostoyevski": "Fiódor Dostoyevski",
    "Gabriel Garcia Márquez": "Gabriel García Márquez",
    "Mark Manson - Will Smith": "Mark Manson y Will Smith",
}

# El sitio original atribuía esta novela a otra persona. Es una corrección de contenido, no de formato.
AUTHOR_CORRECTION = {"list:La verdad sobre el caso Savolta": ("Manuel Rivas", "Eduardo Mendoza")}

PUBLISHER_FIX = {
    "Penguin Pg": "Penguin",
    "Plaza & Jane": "Plaza & Janés",
    "plaza janes": "Plaza & Janés",
    "TALLER DEL EXITO": "Taller del Éxito",
    "CONECTA": "Conecta",
    "PENGUIN CLÁSICOS": "Penguin Clásicos",
    "Crown Publishing Group (NY)": "Crown Publishing Group",
}


def fix_description(text: str) -> str:
    """`???frase???` era una comilla mal codificada en el original."""
    return re.sub(r"\?\?\?(.+?)\?\?\?", r"«\1»", text)


def resolve_price(b: LegacyBook) -> tuple[int, str]:
    """El precio de la página de categoría manda sobre el del detalle (decisión del usuario)."""
    for page in LISTING_CATEGORY:
        if page in b.price_by_page:
            return b.price_by_page[page], f"listado {page}.html"
    if b.price_detail is not None:
        return b.price_detail, "detalle"
    return b.price_by_page["index"], "portada"


def resolve_shipping(b: LegacyBook) -> tuple[int, str]:
    if "on_sale" in b.flags:
        return 0, "sección «con ENVÍO GRATUITO» de la portada"
    for page in LISTING_CATEGORY:
        if page in b.shipping_by_page:
            return b.shipping_by_page[page], f"listado {page}.html"
    if b.shipping_detail is not None:
        return b.shipping_detail, "detalle"
    return b.shipping_by_page.get("index", 0), "portada"


def cop(amount: int) -> str:
    """306708 -> '$306.708'."""
    return "$" + f"{amount:,}".replace(",", ".")


def conflicts(values: dict[str, int | None]) -> dict[str, int] | None:
    present = {k: v for k, v in values.items() if v is not None}
    return present if len(set(present.values())) > 1 else None


def dump(path: Path, items: list[Entity]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [i.model_dump(mode="json") for i in items]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def unreferenced_images() -> list[str]:
    html = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in LEGACY_HTML.rglob("*.html"))
    # Hay nombres con espacios y comas ("Cabeza, Corazón.webp"): se lee hasta la comilla de cierre.
    referenced = {m.split("?")[0] for m in re.findall(r"/imagenes/([^\"')>]+)", html)}
    return sorted(f.name for f in LEGACY_IMAGES.iterdir() if f.is_file() and f.name not in referenced)


def main(force: bool) -> int:
    data_dir = settings.data_dir
    if (data_dir / "books.json").exists() and not force:
        print("Ya existe backend/data/books.json. Usa --force para sobrescribir el catálogo.")
        return 1

    legacy = parse_legacy()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    notes: dict[str, list[str]] = {"prices": [], "shipping": [], "corrections": [], "anomalies": [], "incomplete": []}

    categories = [
        Category(id=f"cat_{slug}", name=name, slug=slug, description=desc, position=i)
        for i, (slug, name, desc) in enumerate(CATEGORY_DEFS)
    ]
    category_id = {c.slug: c.id for c in categories}

    # -- normalizar y agrupar ------------------------------------------------------------------
    prepared = []
    for key, b in legacy.items():
        title = TITLE_FIX.get(key, b.title)
        raw_author = b.author
        if key in AUTHOR_CORRECTION and AUTHOR_CORRECTION[key][0] == raw_author:
            wrong, right = AUTHOR_CORRECTION[key]
            notes["corrections"].append(f"**{title}**: el original decía autor «{wrong}»; corregido a «{right}».")
            raw_author = right
        author_name = AUTHOR_FIX.get(raw_author, raw_author)

        price, price_src = resolve_price(b)
        shipping, ship_src = resolve_shipping(b)
        if shipping > SHIPPING_ANOMALY_LIMIT:
            notes["anomalies"].append(
                f"**{title}**: envío de {cop(shipping)} en el original (dato de prueba probable); "
                f"normalizado a {cop(SHIPPING_ANOMALY_FALLBACK)}."
            )
            shipping = SHIPPING_ANOMALY_FALLBACK

        price_values = {"detalle": b.price_detail, **{f"{p}.html": v for p, v in b.price_by_page.items()}}
        if found := conflicts(price_values):
            shown = ", ".join(f"{k} {cop(v)}" for k, v in found.items())
            notes["prices"].append(f"**{title}**: {shown} → se usa **{cop(price)}** ({price_src}).")
        ship_values = {"detalle": b.shipping_detail, **{f"{p}.html": v for p, v in b.shipping_by_page.items()}}
        if found := conflicts(ship_values):
            shown = ", ".join(f"{k} {cop(v)}" for k, v in found.items())
            notes["shipping"].append(f"**{title}**: {shown} → se usa **{cop(shipping)}** ({ship_src}).")

        cats = list(b.categories)
        for extra in EXTRA_CATEGORIES.get(key, []):
            if extra not in cats:
                cats.append(extra)
        assert cats, f"{key}: sin categoría"

        prepared.append((key, b, title, author_name, price, shipping, cats))

    prepared.sort(key=lambda row: slugify(row[2]))

    # -- autores --------------------------------------------------------------------------------
    author_names = sorted({row[3] for row in prepared}, key=slugify)
    authors = [Author(id=f"aut_{i:03d}", name=n, slug=slugify(n)) for i, n in enumerate(author_names, 1)]
    author_id = {a.name: a.id for a in authors}

    # -- libros + portadas ----------------------------------------------------------------------
    books: list[Book] = []
    key_to_book_id: dict[str, str] = {}
    used_slugs: set[str] = set()
    image_rows: list[tuple[str, int, int]] = []
    for i, (key, b, title, author_name, price, shipping, cats) in enumerate(prepared, 1):
        slug = base = slugify(title)
        n = 2
        while slug in used_slugs:
            slug, n = f"{base}-{n}", n + 1
        used_slugs.add(slug)

        src = LEGACY_IMAGES / (b.cover_file or "")
        assert src.is_file(), f"{key}: portada no encontrada: {b.cover_file}"
        dest = COVERS_DIR / f"{slug}.webp"
        width, height, blur = process_cover(src, dest)
        image_rows.append((b.cover_file or "", src.stat().st_size, dest.stat().st_size))

        on_sale = "on_sale" in b.flags
        if not b.has_detail_page:
            notes["incomplete"].append(f"**{title}** ({author_name})")
        books.append(
            Book(
                id=f"bk_{i:03d}",
                slug=slug,
                title=title,
                author_id=author_id[author_name],
                category_ids=[category_id[c] for c in cats],
                publisher=PUBLISHER_FIX.get(b.publisher, b.publisher) if b.publisher else None,
                pages=b.pages,
                language=b.language,
                description=fix_description(b.description),
                price_cop=price,
                discount_pct=DISCOUNT_PCT_ON_SALE if on_sale else 0,
                shipping_cost_cop=shipping,
                stock=STOCK_MIN + zlib.crc32(slug.encode()) % STOCK_SPAN,
                cover=f"/covers/{slug}.webp",
                cover_width=width,
                cover_height=height,
                cover_blur=blur,
                featured="featured" in b.flags,
                bestseller="bestseller" in b.flags,
                incomplete=not b.has_detail_page,
                created_at=now,
            )
        )
        key_to_book_id[key] = f"bk_{i:03d}"

    # Con --force el catálogo se reemplaza entero: las portadas de una importación anterior que ya no
    # corresponden a ningún libro (p. ej. porque cambió un título y con él su slug) quedan huérfanas.
    # `sin-portada.webp` es la portada por defecto del panel de administración (scripts/make_placeholder_cover.py).
    # Las portadas de scripts/add_catalog.py tampoco son huérfanas: pertenecen a los libros que ese script añade.
    wanted = {Path(b.cover).name for b in books} | {"sin-portada.webp"} | extra_cover_names()
    orphans = [f for f in COVERS_DIR.glob("*.webp") if f.name not in wanted]
    for orphan in orphans:
        orphan.unlink()
    if orphans:
        print(f"Portadas huérfanas eliminadas: {', '.join(o.name for o in orphans)}")

    # -- reseñas de muestra ---------------------------------------------------------------------
    reviews: list[Review] = []
    day = datetime(2025, 2, 1, 12, tzinfo=timezone.utc)
    missing = set(DEMO_REVIEWS) - set(key_to_book_id)
    assert not missing, f"reseñas para libros que no existen: {sorted(missing)}"
    for key in sorted(DEMO_REVIEWS, key=lambda k: key_to_book_id[k]):
        for name, rating, comment in DEMO_REVIEWS[key]:
            reviews.append(
                Review(
                    id=f"rv_{len(reviews) + 1:03d}",
                    book_id=key_to_book_id[key],
                    author_name=name,
                    rating=rating,
                    comment=comment,
                    is_demo=True,
                    created_at=day,
                )
            )
            day += timedelta(days=1)

    # -- escribir -------------------------------------------------------------------------------
    dump(data_dir / "categories.json", categories)
    dump(data_dir / "authors.json", authors)
    dump(data_dir / "books.json", books)
    dump(data_dir / "reviews.json", reviews)
    REPORT_PATH.write_text(render_report(books, categories, notes, image_rows, len(reviews)), encoding="utf-8", newline="\n")

    print(f"{len(books)} libros, {len(authors)} autores, {len(categories)} categorías, {len(reviews)} reseñas de muestra")
    print(f"{len(image_rows)} portadas en {COVERS_DIR}")
    print(f"Informe: {REPORT_PATH}")
    return 0


def render_report(
    books: list[Book],
    categories: list[Category],
    notes: dict[str, list[str]],
    image_rows: list[tuple[str, int, int]],
    review_count: int,
) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "- (ninguno)"

    before = sum(r[1] for r in image_rows)
    after = sum(r[2] for r in image_rows)
    unused = unreferenced_images()
    per_category = {c.name: sum(c.id in b.category_ids for b in books) for c in categories}
    on_sale = [b.title for b in books if b.discount_pct]
    return f"""# Informe de importación del sitio original

Generado por `backend/scripts/import_legacy.py`. Revisa lo marcado como **por revisar**.

## Resumen

- **{len(books)} libros** ({sum(not b.incomplete for b in books)} con ficha completa, {sum(b.incomplete for b in books)} incompletos).
- Por categoría: {", ".join(f"{k} {v}" for k, v in per_category.items())} (un libro puede estar en varias).
- {review_count} reseñas de **muestra** (`is_demo`). Las 6 reseñas idénticas del original se descartaron.
- Stock: entre {STOCK_MIN} y {STOCK_MIN + STOCK_SPAN - 1} unidades, determinista por libro. **Es un dato inventado**: el original no tenía stock.
- Descuento del {DISCOUNT_PCT_ON_SALE} % en los libros de «Libros en Descuento»: {", ".join(on_sale)}.

## Precios en conflicto (por revisar)

Regla acordada: manda el precio de la página de categoría.

{bullets(notes["prices"])}

> Crimen y Castigo aparecía a $14.000 en la portada, dentro de «Libros en Descuento». Lo más probable es que
> $14.000 fuera su precio ya rebajado y $45.000 el de lista. Con el descuento del 15 % queda a $38.250.

## Envío en conflicto

Regla: los libros de la sección «con ENVÍO GRATUITO» tienen envío gratis; el resto, listado de categoría y luego detalle.

{bullets(notes["shipping"])}

## Correcciones de contenido (por revisar)

{bullets(notes["corrections"])}

## Datos anómalos normalizados (por revisar)

{bullets(notes["anomalies"])}

## Libros incompletos

Solo aparecían en el listado de Historia, sin página de detalle: no tienen editorial, páginas, idioma ni
descripción. Se importan con `incomplete = true` para completarlos desde el panel de administración.

{bullets(notes["incomplete"])}

## Imágenes

- {len(image_rows)} portadas convertidas a webp en `frontend/public/covers/<slug>.webp`.
- Peso: {before / 1024:.0f} KB de origen → {after / 1024:.0f} KB.
- No se amplía ninguna imagen; las portadas originales miden ~360 px de alto.
- Imágenes de `legacy/imagenes` que ningún HTML referencia (no se copian, `legacy/` no se toca): {len(unused)}.
  {", ".join(f"`{u}`" for u in unused)}

## Otras erratas del original corregidas

- Editorial «Plaza & Jane» → «Plaza & Janés»; «Penguin Pg» → «Penguin»; editoriales en MAYÚSCULAS normalizadas.
- Autor «Lev N. Tolstói (Leon Tolstói)» y «León Tolstói» unificados; «Fiódor M./Fiódor Dostoyevski» unificados.
- «Gabriel Garcia Márquez» → «Gabriel García Márquez»; «Mark Manson - Will Smith» → «Mark Manson y Will Smith».
- Títulos con tildes o mayúsculas erróneas (Steve Jobs, Autobiografía…, Récords…) y sin «(ingles)» en A Promised Land.
- `???frase???` → `«frase»` en la descripción de Sin Límites.
- Se conservan sin tocar las descripciones con faltas de tilde (p. ej. El Jardín de la Bruja Verde).
- La capitalización de los títulos es heterogénea en el original («En Agosto Nos Vemos» junto a
  «Cien años de soledad») y se respeta; unificarla es una decisión editorial.
- La portada de «The Mamba Mentality: Los secretos de mi éxito» dice «Mentalidad Mamba»; el título es el del original.
"""


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(force="--force" in sys.argv))

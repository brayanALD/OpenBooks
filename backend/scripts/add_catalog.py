"""Amplía el catálogo con libros reales de scripts/catalog_extra.txt: 9 categorías nuevas y hasta 20 libros por categoría.

Uso (desde backend/, con conexión a internet):
    .venv\\Scripts\\python.exe -m scripts.add_catalog [--dry-run]

- Título, autor y descripción salen del archivo de texto. Portada, páginas y editorial se consultan en Open Library
  (https://openlibrary.org); si un libro no tiene portada allí se omite y se avisa al final.
- Precio, envío y stock son inventados y deterministas (como en el resto del catálogo de desarrollo).
- Es idempotente: un libro cuyo slug ya existe se salta, así que se puede repetir tras un fallo de red.
- Escribe en backend/data (books/authors/categories.json) y en frontend/public/covers, igual que import_legacy.
  Si repites `import_legacy --force`, el catálogo vuelve a los 37 libros originales: ejecuta este script después.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
import zlib
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from PIL import Image

from app.config import settings
from app.core.text import slugify
from app.domain.models import Author, Book, Category, Entity
from scripts.process_images import process_cover

ROOT = Path(__file__).resolve().parents[2]
COVERS_DIR = ROOT / "frontend" / "public" / "covers"
EXTRA_FILE = Path(__file__).with_name("catalog_extra.txt")

NEW_CATEGORIES = [
    ("ciencia-ficcion", "Ciencia ficción", "Futuros posibles, otros mundos y las preguntas de la tecnología."),
    ("misterio", "Misterio", "Crímenes, detectives y giros inesperados."),
    ("poesia", "Poesía", "Versos para leer despacio, de los clásicos a las voces de hoy."),
    ("terror", "Terror", "Historias para no dormir: monstruos, casas encantadas y miedo del bueno."),
    ("romance", "Romance", "Historias de amor de todas las épocas."),
    ("ciencia", "Ciencia", "Divulgación para entender el universo, la vida y la mente."),
    ("infantil", "Infantil", "Lecturas para los más pequeños y para toda la familia."),
    ("cocina", "Cocina", "Recetas, técnicas y la ciencia de comer bien."),
    ("tecnologia", "Tecnología", "Programación, inteligencia artificial y la cultura digital."),
]
TARGET_PER_CATEGORY = 20
STOCK_MIN, STOCK_SPAN = 3, 28  # igual que import_legacy: 3..30
OPEN_LIBRARY = "https://openlibrary.org/search.json"
HEADERS = {"User-Agent": "OpenBooks-dev/1.0 (catalogo de desarrollo local)"}


# Datos que faltaban: 7 libros del sitio original que solo tenían ficha en el listado (sin descripción, páginas ni editorial)
# y páginas de libros añadidos cuya edición no las traía en Open Library. Solo rellenan huecos: nunca pisan un dato existente.
# Las páginas son las de una edición habitual del libro (pueden variar según la edición).
COMPLETIONS: dict[str, dict] = {
    "de-animales-a-dioses": dict(pages=496, publisher="Debate", description="Una breve historia de la humanidad: cómo el Homo sapiens llegó a dominar el planeta a través de las revoluciones cognitiva, agrícola y científica, y qué futuro nos espera."),
    "el-olvido-que-seremos": dict(pages=274, publisher="Planeta", description="Héctor Abad Faciolince recuerda a su padre, el médico y defensor de los derechos humanos Héctor Abad Gómez, asesinado en Medellín en 1987: un libro sobre la familia, el amor y la violencia en Colombia."),
    "la-verdad-sobre-el-caso-savolta": dict(pages=456, publisher="Seix Barral", description="Novela ambientada en la Barcelona de 1917 a 1919, con conflictos obreros, pistolerismo y corrupción empresarial, que se reconstruye a partir del caso de la empresa Savolta."),
    "las-venas-abiertas-de-america-latina-edicion-50-aniversario": dict(pages=486, publisher="Siglo XXI Editores", description="Ensayo sobre la historia de la explotación económica de América Latina, desde la conquista europea hasta el siglo XX, y sus consecuencias sobre el continente."),
    "lecciones-de-histeria-de-colombia-edicion-bicentenario": dict(pages=189, publisher="Áncora Editores", description="Un recorrido humorístico por la historia de Colombia, con ironía sobre sus personajes y episodios desde la Conquista hasta hoy."),
    "los-peligros-de-fumar-en-la-cama": dict(pages=221, publisher="Emecé", description="Libro de cuentos de terror y de lo siniestro ambientados en la Argentina de hoy: fantasías, casas embrujadas y pesadillas cotidianas."),
    "mi-lucha-lite": dict(pages=190, description="Edición resumida de «Mi lucha» (1925), el libro en que Adolf Hitler expone su autobiografía y su ideología nazi. Se ofrece como documento histórico para comprender el auge del nazismo."),
    "el-conde-de-montecristo": dict(pages=1271),
    "el-grufalo": dict(pages=32),
    "la-cuchara-de-plata": dict(pages=1264, publisher="Phaidon"),
    "patrones-de-diseno": dict(pages=395, publisher="Addison-Wesley"),
    "refactoring": dict(pages=461),
    "poeta-en-nueva-york": dict(pages=202),
    "inventario-uno": dict(pages=607),
    "narraciones-extraordinarias": dict(pages=384),
    "la-doble-helice": dict(pages=206),
    "la-metamorfosis": dict(pages=96),
    "el-tunel": dict(pages=150),
    "el-mono-desnudo": dict(pages=237),
}


def complete(books: list[Book]) -> list[Book]:
    """Aplica COMPLETIONS rellenando solo los campos vacíos; un libro deja de ser «incompleto» cuando ya tiene los tres datos."""
    out = []
    for book in books:
        fill = {k: v for k, v in COMPLETIONS.get(book.slug, {}).items() if not getattr(book, k)}
        if fill:
            book = book.model_copy(update=fill)
            if book.incomplete and book.pages and book.publisher and book.description:
                book = book.model_copy(update={"incomplete": False})
        out.append(book)
    return out


class Row:
    def __init__(self, category: str, title: str, author: str, alt: str, description: str):
        self.category, self.title, self.author = category, title, author
        self.alt, self.description = alt or title, description
        self.slug = slugify(title)


def read_rows() -> list[Row]:
    rows = []
    for line in EXTRA_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        category, title, author, alt, description = (p.strip() for p in line.split("|"))
        rows.append(Row(category, title, author, alt, description))
    return rows


def extra_cover_names() -> set[str]:
    """Portadas que pertenecen a estos libros: import_legacy no debe borrarlas como huérfanas."""
    return {f"{r.slug}.webp" for r in read_rows()}


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def first_author_surname(author: str) -> str:
    first = author.replace(" et al.", "").split(" y ")[0].split(",")[0].strip()
    return norm(first.split()[-1])


def search(client: httpx.Client, row: Row, title: str, spanish: bool, use_author: bool = True) -> list[dict]:
    params = {
        "title": title,
        "limit": 15,
        "fields": "title,author_name,cover_i,number_of_pages_median,publisher,edition_count",
    }
    if use_author and row.author != "Varios autores":
        params["author"] = row.author.replace(" et al.", "").split(" y ")[0].split(",")[0]
    if spanish:
        params["language"] = "spa"
    for attempt in range(3):
        try:
            response = client.get(OPEN_LIBRARY, params=params, timeout=30)
            if response.status_code == 200:
                docs = response.json().get("docs", [])
                break
        except httpx.HTTPError:
            pass
        time.sleep(2 * (attempt + 1))
    else:
        return []
    surname = first_author_surname(row.author)
    candidates = [
        d for d in docs
        if d.get("cover_i") and (row.author == "Varios autores" or any(surname in norm(a) for a in d.get("author_name", [])))
    ]
    # Entre las coincidencias, la edición más difundida suele tener la mejor portada.
    return sorted(candidates, key=lambda d: -d.get("edition_count", 0))


def download_cover(client: httpx.Client, cover_id: int, dest: Path) -> tuple[int, int, str] | None:
    url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    try:
        response = client.get(url, timeout=60, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if response.status_code != 200 or len(response.content) < 8_000:
        return None
    with TemporaryDirectory() as tmp:
        raw = Path(tmp) / "cover.jpg"
        raw.write_bytes(response.content)
        try:
            with Image.open(raw) as img:
                if img.width < 150 or img.height < 200:
                    return None
        except OSError:
            return None
        return process_cover(raw, dest)


def dump(path: Path, items: list[Entity]) -> None:
    payload = [i.model_dump(mode="json") for i in items]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(dry_run: bool = False) -> int:
    data = settings.data_dir
    categories = [Category(**c) for c in json.loads((data / "categories.json").read_text(encoding="utf-8"))]
    authors = [Author(**a) for a in json.loads((data / "authors.json").read_text(encoding="utf-8"))]
    books = [Book(**b) for b in json.loads((data / "books.json").read_text(encoding="utf-8"))]

    by_slug = {c.slug: c for c in categories}
    for slug, name, description in NEW_CATEGORIES:
        if slug not in by_slug:
            category = Category(id=f"cat_{slug}", name=name, slug=slug, description=description, position=len(categories))
            categories.append(category)
            by_slug[slug] = category

    rows = read_rows()
    unknown = {r.category for r in rows} - set(by_slug)
    assert not unknown, f"categorías desconocidas en catalog_extra.txt: {sorted(unknown)}"

    author_by_name = {norm(a.name): a for a in authors}
    used_slugs = {b.slug for b in books}
    now = datetime.now(timezone.utc).replace(microsecond=0)
    authors_before = len(authors)
    added: list[Book] = []
    failed: list[str] = []

    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=HEADERS) as client:
        for i, row in enumerate(rows, 1):
            if row.slug in used_slugs:
                continue
            if dry_run:
                print(f"[{i}/{len(rows)}] (simulado) {row.title}")
                continue
            dest = COVERS_DIR / f"{row.slug}.webp"
            processed, doc, seen = None, None, set()
            # Varias búsquedas, de la más específica a la más laxa; se prueban las mejores coincidencias hasta que una portada sirva.
            for title, spanish, use_author in ((row.title, True, True), (row.alt, False, True), (row.title, False, True), (row.alt, False, False)):
                for candidate in search(client, row, title, spanish, use_author)[:6]:
                    if candidate["cover_i"] in seen:
                        continue
                    seen.add(candidate["cover_i"])
                    processed = download_cover(client, candidate["cover_i"], dest)
                    time.sleep(0.3)
                    if processed:
                        doc = candidate
                        break
                time.sleep(0.3)
                if processed:
                    break
            if processed is None or doc is None:
                failed.append(f"{row.title} ({row.author}): no se encontró una portada utilizable en Open Library")
                print(f"[{i}/{len(rows)}] SIN PORTADA {row.title}")
                continue
            width, height, blur = processed

            author = author_by_name.get(norm(row.author))
            if author is None:
                author = Author(id=f"aut_{len(authors) + 1:03d}", name=row.author, slug=slugify(row.author))
                authors.append(author)
                author_by_name[norm(row.author)] = author

            h = zlib.crc32(row.slug.encode())
            pages = doc.get("number_of_pages_median")
            publishers = doc.get("publisher") or []
            book = Book(
                id=f"bk_{len(books) + len(added) + 1:03d}",
                slug=row.slug,
                title=row.title,
                author_id=author.id,
                category_ids=[by_slug[row.category].id],
                publisher=publishers[0] if publishers else None,
                pages=pages if isinstance(pages, int) and 16 <= pages <= 3000 else None,
                language="Español",
                description=row.description,
                price_cop=25_000 + (h % 71) * 1_000,
                shipping_cost_cop=0 if h % 3 == 0 else 5_000,
                stock=STOCK_MIN + h % STOCK_SPAN,
                cover=f"/covers/{row.slug}.webp",
                cover_width=width,
                cover_height=height,
                cover_blur=blur,
                created_at=now,
            )
            added.append(book)
            used_slugs.add(row.slug)
            print(f"[{i}/{len(rows)}] ok {row.title}")

    if not dry_run:
        dump(data / "categories.json", categories)
        dump(data / "authors.json", authors)
        dump(data / "books.json", complete([*books, *added]))

    print(f"\nLibros añadidos: {len(added)} · autores nuevos: {len(authors) - authors_before}")
    counts = {c.slug: sum(c.id in b.category_ids for b in [*books, *added]) for c in categories}
    for slug, n in counts.items():
        print(f"  {slug}: {n}{'' if n == TARGET_PER_CATEGORY else '  <-- no llega a 20' if n < TARGET_PER_CATEGORY else '  <-- pasa de 20'}")
    if failed:
        print("\nNo se pudieron añadir:")
        for line in failed:
            print(f"  - {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="solo lista lo que haría, sin red ni escritura")
    sys.exit(main(parser.parse_args().dry_run))

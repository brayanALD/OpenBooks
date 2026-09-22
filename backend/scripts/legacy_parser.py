"""Lectura del sitio HTML original (legacy/html). Solo parsea: no escribe nada.

Cada `LegacyBook` junta lo que el sitio original decía de un libro, con las variantes
sin normalizar. `import_legacy.py` reconcilia esas variantes y genera los JSON del catálogo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag

LEGACY_HTML = Path(__file__).resolve().parents[2] / "legacy" / "html"

# Página de listado -> slug de categoría. El original llamaba "bibliografia" a las biografías.
LISTING_CATEGORY = {
    "clasicos": "clasicos",
    "fantasia": "fantasia",
    "bibliografia": "biografias",
    "historia": "historia",
}

# Secciones de la portada (index.html) -> marca del libro.
HOME_SECTIONS = {
    "Productos Recomendados": "featured",
    "Productos Más Vendidos": "bestseller",
    "Libros en Descuento con ENVIO GRATUITO": "on_sale",
}

STAR_FILES = {
    "zeroEstrellas": 0,
    "estrellasDos": 2,
    "estrellasDos2": 2,
    "estrellasCuatro": 4,
    "estrellasCuatro2": 4,
    "estrellasCinco": 5,
}


@dataclass
class LegacyBook:
    key: str  # "saleDino" (página de detalle) o "list:<título>" (solo aparece en listados)
    title: str = ""
    author: str = ""
    publisher: str | None = None
    pages: int | None = None
    language: str | None = None
    price_detail: int | None = None
    shipping_detail: int | None = None
    price_by_page: dict[str, int] = field(default_factory=dict)  # listado -> precio mostrado
    shipping_by_page: dict[str, int] = field(default_factory=dict)
    title_by_page: dict[str, str] = field(default_factory=dict)
    author_by_page: dict[str, str] = field(default_factory=dict)
    rating: int | None = None
    cover_file: str | None = None
    description: str = ""
    categories: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    has_detail_page: bool = False


def clean(text: str) -> str:
    """Colapsa espacios y arregla entidades rotas del original (`1 & #8201;000`)."""
    text = re.sub(r"&\s+#(\d+);", lambda m: chr(int(m.group(1))), text)
    return re.sub(r"[ \t\r\n]+", " ", text).strip()


def parse_money(text: str) -> int | None:
    """'$306.708' -> 306708. 'gratis' -> 0. Sin cifra -> None."""
    if re.search(r"gratis", text, re.I):
        return 0
    match = re.search(r"\$\s*([\d.]+)", text)
    return int(match.group(1).replace(".", "")) if match else None


def stars_from(img: Tag | None) -> int | None:
    if img is None or not img.get("src"):
        return None
    return STAR_FILES.get(Path(img["src"]).stem)


def soup_of(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")


def parse_detail(path: Path) -> LegacyBook:
    soup = soup_of(path)
    book = LegacyBook(key=path.stem, has_detail_page=True)

    article = soup.select_one("article.product")
    assert article is not None, f"{path.name}: sin article.product"

    h2s = [clean(h.get_text()) for h in article.find_all("h2")]
    book.title = h2s[0]
    for p in article.find_all("p"):
        text = clean(p.get_text())
        label, _, value = text.partition(":")
        label = label.lower()
        if label.startswith("autor"):
            book.author = value.strip()
        elif label.startswith("editorial"):
            book.publisher = value.strip()
        elif "gina" in label:  # "N° Páginas"
            book.pages = int(re.sub(r"\D", "", value))
        elif label.startswith("idioma"):
            book.language = value.strip()
    for text in h2s[1:]:
        if text.startswith("$"):
            book.price_detail = parse_money(text)
        elif re.search(r"env[ií]o", text, re.I):
            book.shipping_detail = parse_money(text)

    imgs = article.find_all("img")
    book.cover_file = Path(imgs[0]["src"]).name if imgs else None
    book.rating = stars_from(imgs[1] if len(imgs) > 1 else None)

    # Descripción: párrafo visible + continuación dentro de <details>.
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and clean(h2.get_text()).upper().startswith("DESCRI"):
            info = section.select_one(".info-libro")
            paragraphs = [clean(p.get_text()) for p in info.find_all("p")] if info else []
            book.description = "\n\n".join(p for p in paragraphs if p)
            break
    return book


def parse_listings(books: dict[str, LegacyBook]) -> None:
    """Completa `books` con lo que dicen los listados; añade los libros que solo existen ahí."""
    for page_name in ["index", *LISTING_CATEGORY]:
        soup = soup_of(LEGACY_HTML / f"{page_name}.html")
        for section in soup.find_all("section"):
            h1 = section.find("h1")
            heading = clean(h1.get_text()) if h1 else ""
            flag = next((f for name, f in HOME_SECTIONS.items() if heading.lower() == name.lower()), None)
            for card in section.select("article.product, div.book-item"):
                a = card.find("a", href=True)
                href = a["href"] if a else ""
                key = Path(href).stem if href.endswith(".html") else None

                title_tag = card.find(["h2", "h3"])
                title = clean(title_tag.get_text()) if title_tag else ""
                text = clean(card.get_text(" "))
                author_match = re.search(r"Autor:\s*(.+?)(?:\s+Precio|\s+\$|\s+Env|\s+Costo|$)", text)
                author = author_match.group(1).strip() if author_match else ""

                # El precio es el primer "$…" fuera de "Costo de envío".
                price_text = re.sub(r"Costo de env[ií]o:?\s*\$?[\d.]+|Env[ií]o:?\s*\$?[\d.]+", "", text)
                price = parse_money(re.sub(r"gratis", "", price_text, flags=re.I))
                ship_match = re.search(r"(Costo de env[ií]o:?|Env[ií]o:?)\s*(gratis|\$?[\d.]+)", text, re.I)
                shipping = parse_money(ship_match.group(2) if ship_match and ship_match.group(2).lower() == "gratis"
                                       else f"${ship_match.group(2).lstrip('$')}") if ship_match else None

                if key is None:
                    key = f"list:{title}"
                book = books.get(key)
                if book is None:
                    book = books[key] = LegacyBook(key=key, title=title, author=author)
                    imgs = card.find_all("img")
                    book.cover_file = Path(imgs[0]["src"]).name if imgs else None
                    book.rating = stars_from(imgs[1] if len(imgs) > 1 else None)
                if page_name in LISTING_CATEGORY:
                    slug = LISTING_CATEGORY[page_name]
                    if slug not in book.categories:
                        book.categories.append(slug)
                if price is not None:
                    book.price_by_page[page_name] = price
                if shipping is not None:
                    book.shipping_by_page[page_name] = shipping
                book.title_by_page[page_name] = title
                if author:
                    book.author_by_page[page_name] = author
                if flag:
                    book.flags.add(flag)


def parse_legacy() -> dict[str, LegacyBook]:
    books: dict[str, LegacyBook] = {}
    for path in sorted((LEGACY_HTML / "ventaTemplates").glob("sale*.html")):
        books[path.stem] = parse_detail(path)
    parse_listings(books)

    # Los libros de Historia que solo existen en el listado (sin detalle) se cruzan por título con
    # los que sí tienen detalle (Dino aparece en Historia y en Recomendados con y sin enlace).
    by_title = {b.title.lower(): b for b in books.values() if b.has_detail_page}
    for key in [k for k, b in books.items() if k.startswith("list:")]:
        twin = by_title.get(books[key].title.lower())
        if twin:
            dup = books.pop(key)
            for cat in dup.categories:
                if cat not in twin.categories:
                    twin.categories.append(cat)
            twin.price_by_page.update(dup.price_by_page)
            twin.shipping_by_page.update(dup.shipping_by_page)
            twin.title_by_page.update(dup.title_by_page)
            twin.author_by_page.update(dup.author_by_page)
            twin.flags |= dup.flags
    return books


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    parsed = parse_legacy()
    print(f"{len(parsed)} libros ({sum(b.has_detail_page for b in parsed.values())} con detalle)\n")
    for b in parsed.values():
        desc = b.description
        print(
            f"{b.key:30} r={b.rating} cats={b.categories} flags={sorted(b.flags)}\n"
            f"   {b.title!r} / {b.author!r} / {b.publisher} / {b.pages} p / {b.language}\n"
            f"   detalle=${b.price_detail} env={b.shipping_detail} | listados={b.price_by_page} env={b.shipping_by_page}\n"
            f"   cover={b.cover_file} desc({len(desc)}): {desc[:50]!r} … {desc[-40:]!r}"
        )

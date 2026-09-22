"""Aplica las reglas de catalog_rules.py y unas reseñas genéricas al catálogo YA IMPORTADO en backend/data:
- ISBN para los libros que aún no tengan (todos, hoy).
- Envío recalculado por precio y páginas (regla nueva, reemplaza la que traía cada libro).
- Editorial normalizada cuando estaba en MAYÚSCULAS o minúsculas sueltas.
- Descuento: 15 % del catálogo completo, al azar (semilla fija), mitad al 10 % y mitad al 15 %.
  Se RECALCULA entero cada vez (no es aditivo): el libro que ya no salga elegido vuelve a 0 %.
- Destacado / más vendido, y unas reseñas de muestra genéricas, solo para los libros que añadió
  `add_catalog.py` (id > bk_037: los 37 originales de `import_legacy.py` no se tocan, para conservar
  fielmente los que el sitio original marcaba).

Idempotente para todo menos el descuento (que siempre refleja la última selección al azar): no quita
destacado/más vendido ya puestos, no reemplaza un ISBN que ya exista, no toca reseñas de libros que ya
tengan alguna (reales o de muestra). Se puede repetir sin duplicar nada.

Uso (desde backend/):
    .venv\\Scripts\\python.exe -m scripts.enrich_catalog [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.domain.models import Book, Review
from scripts.catalog_rules import extra_flags, isbn_for, normalize_publisher, pick_discounts, shipping_for
from scripts.generic_reviews import build_generic_reviews

ORIGINAL_BOOK_COUNT = 37  # bk_001..bk_037 son del sitio original; el resto, de add_catalog.py


def dump(path: Path, items: list) -> None:
    payload = [i.model_dump(mode="json") for i in items]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def is_extra(book: Book) -> bool:
    number = int(book.id.removeprefix("bk_")) if book.id.startswith("bk_") else 0
    return number > ORIGINAL_BOOK_COUNT


def main(dry_run: bool = False) -> int:
    data = settings.data_dir
    books = [Book(**b) for b in json.loads((data / "books.json").read_text(encoding="utf-8"))]
    reviews_path = data / "reviews.json"
    reviews = [Review(**r) for r in json.loads(reviews_path.read_text(encoding="utf-8"))] if reviews_path.exists() else []
    reviewed_book_ids = {r.book_id for r in reviews}

    changed = Counter()
    updated_books: list[Book] = []
    new_reviews: list[Review] = []
    next_review_id = max((int(r.id[3:]) for r in reviews if r.id.startswith("rv_") and r.id[3:].isdigit()), default=0) + 1
    anchor = datetime(2025, 3, 1, 9, tzinfo=timezone.utc)
    discount_map = pick_discounts([b.slug for b in books])

    for book in books:
        updates: dict = {}

        if not book.isbn:
            updates["isbn"] = isbn_for(book.slug, book.language)
            changed["isbn"] += 1

        new_shipping = shipping_for(book.price_cop, book.pages)
        if new_shipping != book.shipping_cost_cop:
            updates["shipping_cost_cop"] = new_shipping
            changed["shipping"] += 1

        new_discount = discount_map.get(book.slug, 0)
        if new_discount != book.discount_pct:
            updates["discount_pct"] = new_discount
            changed["discount_pct"] += 1

        normalized = normalize_publisher(book.publisher)
        if normalized != book.publisher:
            updates["publisher"] = normalized
            changed["publisher"] += 1

        extra = is_extra(book)
        if extra:
            for key, value in extra_flags(book.slug).items():
                if not getattr(book, key):  # aditivo: nunca se quita una marca ya puesta
                    updates[key] = value
                    changed[key] += 1

        updated_books.append(book.model_copy(update=updates) if updates else book)

        if extra and book.id not in reviewed_book_ids:
            merged = book.model_copy(update=updates) if updates else book
            bonus = 2 if merged.featured or merged.bestseller else 0
            generated = build_generic_reviews(book_id=book.id, slug=book.slug, start_id=next_review_id, start_date=anchor, bonus=bonus)
            next_review_id += len(generated)
            new_reviews.extend(generated)
            if generated:
                changed["books_with_new_reviews"] += 1

    print("Cambios:")
    for key in ("isbn", "shipping", "publisher", "featured", "bestseller", "discount_pct", "books_with_new_reviews"):
        print(f"  {key}: {changed[key]}")
    print(f"  reseñas de muestra nuevas: {len(new_reviews)}")

    if not dry_run:
        dump(data / "books.json", updated_books)
        if new_reviews:
            dump(reviews_path, [*reviews, *new_reviews])
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    sys.exit(main(parser.parse_args().dry_run))

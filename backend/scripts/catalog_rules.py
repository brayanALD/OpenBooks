"""Reglas de datos inventados compartidas por los scripts de catálogo
(import_legacy, add_catalog, enrich_catalog): envío, ISBN y reparto de destacado/más vendido/descuento.

Nada de esto es real: son datos de desarrollo, deterministas a partir del slug del libro para que
el catálogo sea reproducible (mismo libro -> mismo resultado, sin azar entre ejecuciones).
"""

from __future__ import annotations

import random
import zlib

# -- envío ------------------------------------------------------------------------------------
# Decisión del usuario: envío gratis desde $70.000; si no, 5.000 con hasta 150 páginas y 10.000 con más
# (o si no se conocen las páginas, para no regalar envío en un libro potencialmente grande).
FREE_SHIPPING_FROM_COP = 70_000
SHORT_BOOK_MAX_PAGES = 150
SHORT_BOOK_SHIPPING_COP = 5_000
LONG_BOOK_SHIPPING_COP = 10_000


def shipping_for(price_cop: int, pages: int | None) -> int:
    if price_cop > FREE_SHIPPING_FROM_COP:
        return 0
    if pages is not None and pages <= SHORT_BOOK_MAX_PAGES:
        return SHORT_BOOK_SHIPPING_COP
    return LONG_BOOK_SHIPPING_COP


# -- ISBN -------------------------------------------------------------------------------------
# Inventado (no corresponde a una edición real), pero con la forma y el dígito de control de un
# ISBN-13 válido. El prefijo de grupo se elige por idioma para que se vea plausible: 978-0 para
# libros en inglés, o uno de los prefijos hispanohablantes más comunes para el resto.
_ISBN_GROUPS_ES = [
    ("84", 2, 3, 4),  # España
    ("958", 3, 2, 4),  # Colombia
    ("607", 3, 2, 4),  # México
    ("950", 3, 2, 4),  # Argentina
]
_ISBN_GROUP_EN = ("0", 1, 2, 6)  # anglosajón (Reino Unido / EE. UU.)


def _ean13_check_digit(digits12: str) -> str:
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits12))
    return str((10 - total % 10) % 10)


def isbn_for(seed: str, language: str | None) -> str:
    h = zlib.crc32(seed.encode())
    if language and language.strip().lower().startswith("ingl"):
        group, _, registrant_len, publication_len = _ISBN_GROUP_EN
    else:
        group, _, registrant_len, publication_len = _ISBN_GROUPS_ES[h % len(_ISBN_GROUPS_ES)]
    registrant = str(h % (10**registrant_len)).zfill(registrant_len)
    publication = str((h // 97) % (10**publication_len)).zfill(publication_len)
    body = f"978{group}{registrant}{publication}"
    return f"978-{group}-{registrant}-{publication}-{_ean13_check_digit(body)}"


def is_valid_isbn13(value: str) -> bool:
    digits = value.replace("-", "")
    if len(digits) != 13 or not digits.isdigit():
        return False
    return _ean13_check_digit(digits[:12]) == digits[12]


# -- destacado / más vendido ---------------------------------------------------------------------
# Reparto determinista para que el catálogo ampliado (los libros que no venían del sitio original)
# no se vea vacío en portada. Es aditivo: solo se usa para PONER una marca, nunca para quitarla.


def extra_flags(seed: str) -> dict[str, bool]:
    h = zlib.crc32(seed.encode())
    flags: dict[str, bool] = {}
    if h % 12 == 0:
        flags["featured"] = True
    if h % 11 == 0:
        flags["bestseller"] = True
    return flags


# -- descuento ------------------------------------------------------------------------------------
# Decisión del usuario: 15 % del catálogo en descuento, elegido al azar; la mitad de esos al 10 %
# y la otra mitad al 15 %. Semilla fija: la elección es "al azar" pero reproducible entre ejecuciones.
ON_SALE_FRACTION = 0.15
ON_SALE_LOW_PCT = 10
ON_SALE_HIGH_PCT = 15
_DISCOUNT_SEED = "descuentos-catalogo"


def pick_discounts(slugs: list[str]) -> dict[str, int]:
    """slug -> % de descuento, solo para los libros elegidos; el resto no aparece en el resultado."""
    rng = random.Random(_DISCOUNT_SEED)
    chosen = rng.sample(sorted(slugs), k=round(len(slugs) * ON_SALE_FRACTION))
    half = len(chosen) // 2
    return {slug: ON_SALE_LOW_PCT for slug in chosen[:half]} | {
        slug: ON_SALE_HIGH_PCT for slug in chosen[half:]
    }


# -- editorial --------------------------------------------------------------------------------


_MINOR_WORDS = {"y", "de", "del", "la", "el", "en", "a", "los", "las"}


def normalize_publisher(name: str | None) -> str | None:
    """Arregla mayúsculas/minúsculas sueltas (TODO MAYÚSCULAS o todo minúsculas); deja en paz el resto."""
    if not name:
        return name
    if not (name.isupper() or name.islower()):
        return name
    words = name.split(" ")
    fixed = [w.lower() if w.lower() in _MINOR_WORDS and i > 0 else w.capitalize() for i, w in enumerate(words)]
    return " ".join(fixed)

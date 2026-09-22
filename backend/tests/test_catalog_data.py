"""Integridad del catálogo real importado (backend/data + frontend/public/covers)."""

from collections import Counter
from pathlib import Path

import pytest
from PIL import Image

from app.config import settings
from app.domain.models import Author, Book, Category, Review
from app.repositories.json_repo import JsonRepository
from app.services.catalog_service import final_price
from scripts.catalog_rules import is_valid_isbn13, shipping_for


@pytest.fixture(scope="module")
def books():
    return JsonRepository(settings.data_dir / "books.json", Book).list()


@pytest.fixture(scope="module")
def authors():
    return JsonRepository(settings.data_dir / "authors.json", Author).list()


@pytest.fixture(scope="module")
def categories():
    return JsonRepository(settings.data_dir / "categories.json", Category).list()


@pytest.fixture(scope="module")
def reviews():
    return JsonRepository(settings.data_dir / "reviews.json", Review).list()


def test_expected_volumes(books, authors, categories, reviews):
    assert len(books) == 37
    assert len(categories) == 6
    assert len(authors) == 35
    assert len(reviews) == 72


def test_ids_and_slugs_are_unique(books, authors, categories, reviews):
    for collection in (books, authors, categories, reviews):
        ids = [x.id for x in collection]
        assert len(ids) == len(set(ids))
    for collection in (books, authors, categories):
        slugs = [x.slug for x in collection]
        assert len(slugs) == len(set(slugs))


def test_slugs_are_url_safe(books):
    for b in books:
        assert b.slug == b.slug.lower() and b.slug.replace("-", "").isalnum() and b.slug.isascii(), b.slug


def test_foreign_keys_resolve(books, authors, categories, reviews):
    author_ids = {a.id for a in authors}
    category_ids = {c.id for c in categories}
    book_ids = {b.id for b in books}
    for b in books:
        assert b.author_id in author_ids, b.slug
        assert b.category_ids and set(b.category_ids) <= category_ids, b.slug
    for r in reviews:
        assert r.book_id in book_ids


def test_every_category_has_books(books, categories):
    used = {cid for b in books for cid in b.category_ids}
    assert used == {c.id for c in categories}


def test_no_orphan_authors(books, authors):
    assert {a.id for a in authors} == {b.author_id for b in books}


def test_money_and_stock_are_sane(books):
    for b in books:
        assert b.price_cop > 0, b.slug
        assert b.shipping_cost_cop == shipping_for(b.price_cop, b.pages), f"{b.slug}: no sigue la regla de envío"
        assert 3 <= b.stock <= 30, b.slug
        assert final_price(b.price_cop, b.discount_pct) <= b.price_cop


def test_isbns_are_present_unique_and_valid(books):
    isbns = [b.isbn for b in books]
    assert all(is_valid_isbn13(i) for i in isbns), [i for i in isbns if not is_valid_isbn13(i)]
    assert len(isbns) == len(set(isbns))


def test_decisions_applied(books):
    by_slug = {b.slug: b for b in books}
    # Precio de la página de categoría, no el del detalle.
    assert by_slug["estuche-harry-potter-7-libros"].price_cop == 349_000
    assert by_slug["crimen-y-castigo"].price_cop == 45_000
    # Descuento del 15 % solo en los 5 libros de «Libros en Descuento».
    discounted = {b.slug for b in books if b.discount_pct}
    assert discounted == {
        "cabeza-corazon-y-manos",
        "crimen-y-castigo",
        "el-jardin-de-la-bruja-verde",
        "los-renglones-torcidos-de-dios",
        "sin-limites",
    }
    assert {b.discount_pct for b in books if b.discount_pct} == {15}
    # El envío de estos 5 ya no es fijo: sigue la regla general por precio y páginas (ver test_money_and_stock_are_sane).


def test_flags_match_the_legacy_home_page(books):
    assert {b.slug for b in books if b.featured} == {
        "records-y-curiosidades-de-los-dinosaurios",
        "estuche-harry-potter-7-libros",
    }
    assert {b.slug for b in books if b.bestseller} == {
        "en-agosto-nos-vemos",
        "los-vagabundos-de-dios",
        "cien-anos-de-soledad",
        "el-viento-conoce-mi-nombre",
        "la-paciente-silenciosa",
    }


def test_only_the_seven_historia_only_books_are_incomplete(books):
    incomplete = [b for b in books if b.incomplete]
    assert len(incomplete) == 7
    for b in incomplete:
        assert b.publisher is None and b.pages is None and b.description == ""
    for b in books:
        if not b.incomplete:
            assert b.publisher and b.pages and b.language and len(b.description) > 100, b.slug


def test_dirty_original_data_was_cleaned(books, authors):
    publishers = {b.publisher for b in books if b.publisher}
    assert "Plaza & Jane" not in publishers and "Plaza & Janés" in publishers
    assert not any(p.isupper() for p in publishers)
    names = {a.name for a in authors}
    assert "Lev N. Tolstói (Leon Tolstói)" not in names and "León Tolstói" in names
    assert "Eduardo Mendoza" in names and "Manuel Rivas" not in names
    for b in books:
        assert "???" not in b.description and "& #" not in b.description, b.slug


def test_multi_book_authors_are_unified(books, authors):
    counts = Counter(b.author_id for b in books)
    by_name = {a.name: a.id for a in authors}
    assert counts[by_name["León Tolstói"]] == 2
    assert counts[by_name["Gabriel García Márquez"]] == 2


def test_covers_exist_and_match_declared_size(books, seed_data_dir):
    covers_dir = seed_data_dir / "covers"  # el importador escribe aquí durante la suite, no en frontend/public
    on_disk = {p.name for p in covers_dir.glob("*.webp")}
    assert on_disk == {Path(b.cover).name for b in books}, "portadas huérfanas o faltantes"
    for b in books:
        with Image.open(covers_dir / Path(b.cover).name) as img:
            assert (img.width, img.height) == (b.cover_width, b.cover_height), b.slug
        assert b.cover_blur and b.cover_blur.startswith("data:image/webp;base64,"), b.slug


def test_reviews_are_all_marked_as_samples(reviews, books):
    assert all(r.is_demo and r.user_id is None for r in reviews)
    reviewed = Counter(r.book_id for r in reviews)
    assert set(reviewed.values()) == {2}
    no_reviews = [b.slug for b in books if b.id not in reviewed]
    assert no_reviews == ["mi-lucha-lite"]  # sin reseñas de muestra a propósito

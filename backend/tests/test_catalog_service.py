import pytest

from app.domain.models import Author, Category
from app.repositories.memory_repo import InMemoryRepository
from app.schemas.catalog import BookSort
from app.services.catalog_service import BookQuery, CatalogService, final_price, fold
from tests.conftest import make_book


def titles(page):
    return [b.title for b in page.items]


def rec_titles(recommended):
    return [b.title for b in recommended]


# -- precio y utilidades --------------------------------------------------------------------


def test_final_price_applies_discount_in_whole_pesos():
    assert final_price(100_000, 0) == 100_000
    assert final_price(100_000, 20) == 80_000
    assert final_price(45_000, 15) == 38_250
    assert final_price(9_999, 15) == 8_499  # redondea hacia abajo


def test_fold_removes_accents_and_case():
    assert fold("García MÁRQUEZ") == "garcia marquez"


# -- filtros ----------------------------------------------------------------------------------


def test_lists_everything_by_default(catalog):
    page = catalog.list_books(BookQuery())
    assert page.total == 4 and page.pages == 1


def test_filter_by_category_slug(catalog):
    assert set(titles(catalog.list_books(BookQuery(category="clasicos")))) == {
        "Cien años de soledad",
        "Orgullo y prejuicio",
    }


def test_book_in_two_categories_appears_in_both(catalog):
    assert "Cien años de soledad" in titles(catalog.list_books(BookQuery(category="novela")))
    assert "Cien años de soledad" in titles(catalog.list_books(BookQuery(category="clasicos")))


def test_unknown_category_returns_nothing(catalog):
    assert catalog.list_books(BookQuery(category="no-existe")).total == 0


def test_filter_by_author_slug(catalog):
    page = catalog.list_books(BookQuery(author="gabriel-garcia-marquez"))
    assert set(titles(page)) == {"Cien años de soledad", "En agosto nos vemos"}


def test_price_range_uses_final_price(catalog):
    # Nacidos de la bruma: 100.000 con 20 % = 80.000 → entra en 75.000–85.000.
    page = catalog.list_books(BookQuery(min_price=75_000, max_price=85_000))
    assert titles(page) == ["Nacidos de la bruma"]


def test_free_shipping_on_sale_in_stock_flags(catalog):
    assert catalog.list_books(BookQuery(free_shipping=False)).total == 1
    assert titles(catalog.list_books(BookQuery(on_sale=True))) == ["Nacidos de la bruma"]
    assert "En agosto nos vemos" not in titles(catalog.list_books(BookQuery(in_stock=True)))
    assert titles(catalog.list_books(BookQuery(bestseller=True))) == ["Cien años de soledad"]
    assert titles(catalog.list_books(BookQuery(featured=True))) == ["Orgullo y prejuicio"]


# -- búsqueda ---------------------------------------------------------------------------------


def test_search_ignores_accents_and_case(catalog):
    assert titles(catalog.list_books(BookQuery(q="GARCIA marquez"))) == [
        "Cien años de soledad",
        "En agosto nos vemos",
    ]


def test_search_requires_every_word(catalog):
    assert catalog.list_books(BookQuery(q="cien austen")).total == 0


def test_search_matches_description(catalog):
    assert titles(catalog.list_books(BookQuery(q="rebelion"))) == ["Nacidos de la bruma"]


def test_title_match_ranks_above_author_match():
    authors = [Author(id="a1", name="Jane Austen", slug="jane-austen"), Author(id="a2", name="Otra Persona", slug="otra")]
    books = [
        make_book("b1", "Aaa", "a1", []),  # "jane" solo en el autor; alfabéticamente iría primero
        make_book("b2", "Jane Eyre", "a2", []),  # "jane" en el título
    ]
    service = CatalogService(
        InMemoryRepository(books), InMemoryRepository(authors), InMemoryRepository([]), InMemoryRepository([])
    )
    assert titles(service.list_books(BookQuery(q="jane"))) == ["Jane Eyre", "Aaa"]


def test_blank_search_is_ignored(catalog):
    assert catalog.list_books(BookQuery(q="   ")).total == 4


# -- orden y paginación ---------------------------------------------------------------------------


def test_default_order_puts_featured_then_bestsellers_first(catalog):
    assert titles(catalog.list_books(BookQuery()))[:2] == ["Orgullo y prejuicio", "Cien años de soledad"]


@pytest.mark.parametrize(
    "sort, expected_first",
    [
        (BookSort.price_asc, "Orgullo y prejuicio"),
        (BookSort.price_desc, "Nacidos de la bruma"),  # 100.000 con 20 % = 80.000 finales, más que 70.000
        (BookSort.title, "Cien años de soledad"),
        (BookSort.rating, "Cien años de soledad"),
    ],
)
def test_sorting(catalog, sort, expected_first):
    assert titles(catalog.list_books(BookQuery(sort=sort)))[0] == expected_first


def test_pagination(catalog):
    first = catalog.list_books(BookQuery(page=1, page_size=3, sort=BookSort.title))
    second = catalog.list_books(BookQuery(page=2, page_size=3, sort=BookSort.title))
    assert (first.total, first.pages, len(first.items)) == (4, 2, 3)
    assert len(second.items) == 1
    assert not set(titles(first)) & set(titles(second))


def test_page_beyond_the_end_is_empty_not_an_error(catalog):
    page = catalog.list_books(BookQuery(page=9, page_size=3))
    assert page.items == [] and page.total == 4


# -- forma de la respuesta ----------------------------------------------------------------------


def test_summary_computes_derived_fields(catalog):
    book = catalog.get_book("nacidos-de-la-bruma")
    assert book.final_price_cop == 80_000
    assert book.free_shipping is False and book.shipping_cost_cop == 5_000
    assert book.in_stock is True and book.description.startswith("Una saga")
    assert book.author.name == "Brandon Sanderson"
    assert [c.slug for c in book.categories] == ["fantasia"]


def test_out_of_stock_and_free_shipping(catalog):
    book = catalog.get_book("en-agosto-nos-vemos")
    assert book.in_stock is False and book.free_shipping is True


def test_rating_average_and_count(catalog):
    with_reviews = catalog.get_book("cien-años-de-soledad")
    assert (with_reviews.rating_avg, with_reviews.rating_count) == (4.5, 2)
    without = catalog.get_book("nacidos-de-la-bruma")
    assert (without.rating_avg, without.rating_count) == (None, 0)


def test_unknown_book_returns_none(catalog):
    assert catalog.get_book("no-existe") is None
    assert catalog.related_books("no-existe") is None
    assert catalog.book_reviews("no-existe") is None


# -- relacionados, reseñas, categorías -------------------------------------------------------------


def test_related_prefers_same_author_then_shared_category(catalog):
    related = [b.title for b in catalog.related_books("cien-años-de-soledad")]
    assert related[0] == "En agosto nos vemos"  # mismo autor
    assert "Orgullo y prejuicio" in related  # comparte "Clásicos"
    assert "Cien años de soledad" not in related
    assert "Nacidos de la bruma" not in related  # sin relación


def test_related_respects_limit(catalog):
    assert len(catalog.related_books("cien-años-de-soledad", limit=1)) == 1


def test_reviews_newest_first(catalog):
    reviews = catalog.book_reviews("cien-años-de-soledad")
    assert [r.author_name for r in reviews] == ["Beto", "Ana"]  # Beto es 1 día posterior


# -- recomendaciones ---------------------------------------------------------------------------


def test_recommendations_without_purchases_match_the_generic_default_order(catalog):
    # Igual que un cliente nuevo: destacados y más vendidos primero (ver test_default_order_puts_featured_then_bestsellers_first).
    assert rec_titles(catalog.recommended_books(limit=2)) == ["Orgullo y prejuicio", "Cien años de soledad"]


def test_recommendations_favor_shared_category_over_unrelated_books(catalog):
    # Compró "Orgullo y prejuicio" (autor a2, categoría c1 "Clásicos").
    recs = rec_titles(catalog.recommended_books({"b3"}, limit=10))
    assert "Orgullo y prejuicio" not in recs  # no se recomienda lo ya comprado
    assert recs[0] == "Cien años de soledad"  # comparte "Clásicos"
    assert set(recs) == {"Cien años de soledad", "En agosto nos vemos", "Nacidos de la bruma"}  # se completa con genéricos


def test_recommendations_prefer_same_author_over_shared_category():
    # Aislado del resto: A comparte solo autor con lo comprado, B comparte solo categoría. A debe ir primero.
    authors = [Author(id="a1", name="Autora Comprada", slug="autora-comprada"), Author(id="a2", name="Otra", slug="otra")]
    categories = [Category(id="c1", name="Categoría Comprada", slug="cat-comprada")]
    bought = make_book("p1", "Comprado", "a1", ["c1"])
    same_author = make_book("b1", "Mismo autor", "a1", [])
    same_category = make_book("b2", "Misma categoria", "a2", ["c1"])
    service = CatalogService(
        InMemoryRepository([bought, same_author, same_category]),
        InMemoryRepository(authors),
        InMemoryRepository(categories),
        InMemoryRepository([]),
    )
    assert rec_titles(service.recommended_books({"p1"}, limit=2)) == ["Mismo autor", "Misma categoria"]


def test_recommendations_respect_limit_and_exclude_purchased(catalog):
    recs = catalog.recommended_books({"b1", "b3"}, limit=1)
    assert len(recs) == 1
    assert recs[0].title not in {"Cien años de soledad", "Orgullo y prejuicio"}


def test_categories_ordered_with_counts(catalog):
    cats = catalog.list_categories()
    assert [c.slug for c in cats] == ["clasicos", "fantasia", "novela"]
    assert {c.slug: c.book_count for c in cats} == {"clasicos": 2, "fantasia": 1, "novela": 2}
    assert catalog.get_category("fantasia").book_count == 1
    assert catalog.get_category("no-existe") is None

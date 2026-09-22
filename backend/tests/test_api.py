"""Endpoints del catálogo contra los datos reales importados."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


# -- /books -----------------------------------------------------------------------------------


def test_list_books_default_page(client):
    body = client.get("/api/v1/books").json()
    assert body["total"] == 37 and body["page"] == 1 and body["page_size"] == 12 and body["pages"] == 4
    assert len(body["items"]) == 12
    card = body["items"][0]
    assert {"slug", "title", "author", "final_price_cop", "free_shipping", "cover", "rating_avg"} <= card.keys()
    assert "description" not in card  # las tarjetas no cargan la descripción larga


def test_default_order_shows_featured_first(client):
    items = client.get("/api/v1/books").json()["items"]
    assert [b["featured"] for b in items[:2]] == [True, True]


def test_filter_by_category(client):
    body = client.get("/api/v1/books", params={"category": "fantasia", "page_size": 48}).json()
    assert body["total"] == 6
    assert all("fantasia" in [c["slug"] for c in b["categories"]] for b in body["items"])


def test_novela_and_clasicos_share_cien_anos(client):
    for slug in ("novela", "clasicos"):
        titles = [b["title"] for b in client.get("/api/v1/books", params={"category": slug, "page_size": 48}).json()["items"]]
        assert "Cien años de soledad" in titles


def test_search_is_accent_insensitive(client):
    titles = [b["title"] for b in client.get("/api/v1/books", params={"q": "garcia marquez"}).json()["items"]]
    assert set(titles) == {"Cien años de soledad", "En Agosto Nos Vemos"}
    assert client.get("/api/v1/books", params={"q": "zzzz"}).json()["total"] == 0


def test_on_sale_returns_the_five_discounted_books_with_final_price(client):
    body = client.get("/api/v1/books", params={"on_sale": True}).json()
    assert body["total"] == 5
    crimen = next(b for b in body["items"] if b["title"] == "Crimen y Castigo")
    assert (crimen["price_cop"], crimen["discount_pct"], crimen["final_price_cop"]) == (45_000, 15, 38_250)


def test_price_sort(client):
    prices = [b["final_price_cop"] for b in client.get("/api/v1/books", params={"sort": "price_asc", "page_size": 48}).json()["items"]]
    assert prices == sorted(prices)


def test_pagination_covers_every_book_once(client):
    seen = []
    for page in range(1, 5):
        seen += [b["slug"] for b in client.get("/api/v1/books", params={"page": page, "sort": "title"}).json()["items"]]
    assert len(seen) == 37 and len(set(seen)) == 37


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page_size": 0},
        {"page_size": 49},
        {"min_price": -1},
        {"sort": "inventado"},
        {"min_price": 100_000, "max_price": 1_000},
    ],
)
def test_invalid_query_is_rejected(client, params):
    assert client.get("/api/v1/books", params=params).status_code == 422


# -- /books/recommended ------------------------------------------------------------------------


def test_recommended_without_session_is_the_generic_fallback(client):
    items = client.get("/api/v1/books/recommended", params={"limit": 2}).json()
    assert [b["featured"] for b in items] == [True, True]  # misma regla que el orden por defecto de list_books


def test_recommended_respects_limit_and_does_not_collide_with_slug_route(client):
    assert len(client.get("/api/v1/books/recommended", params={"limit": 3}).json()) == 3
    assert client.get("/api/v1/books/recommended", params={"limit": 0}).status_code == 422


# -- /books/{slug} ----------------------------------------------------------------------------


def test_book_detail(client):
    book = client.get("/api/v1/books/1984").json()
    assert book["title"] == "1984" and book["author"]["name"] == "George Orwell"
    assert book["publisher"] == "Penguin" and book["pages"] == 336 and book["language"] == "Inglés"
    assert len(book["description"]) > 100 and book["incomplete"] is False
    assert book["rating_count"] == 2 and book["rating_avg"] == 4.5


def test_incomplete_book_detail_has_null_fields(client):
    book = client.get("/api/v1/books/de-animales-a-dioses").json()
    assert book["incomplete"] is True and book["publisher"] is None and book["description"] == ""


def test_unknown_book_is_404(client):
    for path in ("/api/v1/books/no-existe", "/api/v1/books/no-existe/related", "/api/v1/books/no-existe/reviews"):
        assert client.get(path).status_code == 404


def test_related_books(client):
    related = client.get("/api/v1/books/cien-anos-de-soledad/related").json()
    assert related[0]["title"] == "En Agosto Nos Vemos"  # mismo autor
    assert "Cien años de soledad" not in [b["title"] for b in related]
    assert len(client.get("/api/v1/books/cien-anos-de-soledad/related", params={"limit": 2}).json()) == 2


def test_reviews_are_flagged_as_samples(client):
    reviews = client.get("/api/v1/books/cien-anos-de-soledad/reviews").json()
    assert len(reviews) == 2 and all(r["is_demo"] for r in reviews)
    assert client.get("/api/v1/books/mi-lucha-lite/reviews").json() == []


# -- /cart/validate ----------------------------------------------------------------------------


def book_id(client, slug):
    return client.get(f"/api/v1/books/{slug}").json()["id"]


def test_cart_validate_prices_and_totals(client):
    crimen, sin_limites = book_id(client, "crimen-y-castigo"), book_id(client, "sin-limites")
    body = client.post(
        "/api/v1/cart/validate",
        json={"items": [{"book_id": crimen, "quantity": 2}, {"book_id": sin_limites, "quantity": 1}]},
    ).json()
    assert [l["unit_price_cop"] for l in body["lines"]] == [38_250, 12_750]  # con el 15 % de descuento
    assert body["subtotal_cop"] == 2 * 38_250 + 12_750
    # Ambos libros cuestan menos de $70.000 y tienen más de 150 páginas: envío 10.000 cada uno,
    # y el pedido cobra el envío más caro entre los libros, no la suma.
    assert body["shipping_cop"] == 10_000 and body["total_cop"] == body["subtotal_cop"] + 10_000
    assert body["item_count"] == 3 and body["has_issues"] is False
    assert body["lines"][0]["book"]["title"] == "Crimen y Castigo"


def test_cart_validate_ignores_client_supplied_prices(client):
    crimen = book_id(client, "crimen-y-castigo")
    body = client.post(
        "/api/v1/cart/validate",
        json={"items": [{"book_id": crimen, "quantity": 1, "unit_price_cop": 1}]},
    ).json()
    assert body["lines"][0]["unit_price_cop"] == 38_250


def test_cart_validate_reports_unknown_ids_and_caps_quantity(client):
    crimen = book_id(client, "crimen-y-castigo")
    body = client.post(
        "/api/v1/cart/validate",
        json={"items": [{"book_id": crimen, "quantity": 99}, {"book_id": "bk_999", "quantity": 1}]},
    ).json()
    assert body["unavailable_ids"] == ["bk_999"]
    assert body["lines"][0]["quantity"] <= 10 and body["lines"][0]["issue"] in ("quantity_capped", "limited_stock")
    assert body["has_issues"] is True


def test_cart_validate_empty(client):
    body = client.post("/api/v1/cart/validate", json={"items": []}).json()
    assert body["lines"] == [] and body["total_cop"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"items": [{"book_id": "bk_001", "quantity": 0}]},
        {"items": [{"book_id": "bk_001", "quantity": -1}]},
        {"items": [{"book_id": "bk_001", "quantity": 1000}]},
        {"items": [{"quantity": 1}]},
        {"items": [{"book_id": "", "quantity": 1}]},
        {"items": [{"book_id": "bk_001", "quantity": 1}] * 51},
    ],
)
def test_cart_validate_rejects_bad_payloads(client, payload):
    assert client.post("/api/v1/cart/validate", json=payload).status_code == 422


# -- /categories ------------------------------------------------------------------------------


def test_categories_in_navigation_order_with_counts(client):
    cats = client.get("/api/v1/categories").json()
    assert [c["slug"] for c in cats] == ["clasicos", "fantasia", "novela", "biografias", "historia", "desarrollo-personal"]
    assert {c["slug"]: c["book_count"] for c in cats} == {
        "clasicos": 9, "fantasia": 6, "novela": 6, "biografias": 6, "historia": 8, "desarrollo-personal": 3,
    }


def test_category_detail(client):
    assert client.get("/api/v1/categories/historia").json()["name"] == "Historia"
    assert client.get("/api/v1/categories/no-existe").status_code == 404

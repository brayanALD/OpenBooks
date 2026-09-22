"""API del panel de administración. Repositorios en memoria; las subidas van a la carpeta temporal de la suite."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import settings
from app.core.deps import get_admin_service, get_auth_service, get_catalog_service, get_order_service
from app.main import app
from app.schemas.auth import AddressIn, RegisterIn
from tests.admin_env import AdminEnv, build_admin_env
from tests.order_env import DECLINED_CARD, checkout_data


@pytest.fixture
def ae() -> AdminEnv:
    e = build_admin_env()
    app.dependency_overrides[get_auth_service] = lambda: e.env.auth
    app.dependency_overrides[get_admin_service] = lambda: e.admin
    app.dependency_overrides[get_order_service] = lambda: e.env.service
    app.dependency_overrides[get_catalog_service] = lambda: e.catalog
    yield e
    app.dependency_overrides.clear()


@pytest.fixture
def client(ae):
    return TestClient(app)


def headers_for(ae: AdminEnv, email: str, role: str = "customer") -> dict:
    user = ae.env.auth.register(
        RegisterIn(first_name="Ana", last_name="Pérez", email=email, address=AddressIn(line="Calle 1 # 2-3", city="Cali"), password="clave-segura-1"),
        role=role,
    )
    return {"Authorization": f"Bearer {ae.env.auth.create_token(user)}"}


@pytest.fixture
def admin(ae):
    return headers_for(ae, "admin@correo.com", "admin")


@pytest.fixture
def customer(ae):
    return headers_for(ae, "cliente@correo.com", "customer")


def png(size=(300, 450)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "#754c24").save(buffer, "PNG")
    return buffer.getvalue()


BOOK = {"title": "Libro por API", "author_name": "Autora Uno", "category_ids": ["c1"], "price_cop": 30_000, "stock": 5}

ADMIN_ROUTES = [
    ("get", "/api/v1/admin/summary", None),
    ("get", "/api/v1/admin/books", None),
    ("get", "/api/v1/admin/books/b1", None),
    ("post", "/api/v1/admin/books", BOOK),
    ("patch", "/api/v1/admin/books/b1", {"stock": 1}),
    ("get", "/api/v1/admin/orders", None),
    ("get", "/api/v1/admin/orders/ord_000001", None),
    ("post", "/api/v1/admin/orders/ord_000001/status", {"status": "shipped"}),
]


# -- control de acceso ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("method, path, body", ADMIN_ROUTES, ids=[f"{m} {p}" for m, p, _ in ADMIN_ROUTES])
def test_every_admin_route_is_closed_to_guests_and_customers(client, customer, method, path, body):
    call = lambda **kw: getattr(client, method)(path, **({"json": body} if body is not None else {}), **kw)  # noqa: E731
    assert call().status_code == 401
    assert call(headers=customer).status_code == 403
    assert call(headers={"Authorization": "Bearer basura"}).status_code == 401


def test_upload_is_admin_only_too(client, customer):
    files = {"file": ("portada.png", png(), "image/png")}
    assert client.post("/api/v1/admin/uploads/cover", files=files).status_code == 401
    assert client.post("/api/v1/admin/uploads/cover", files=files, headers=customer).status_code == 403


def test_admin_routes_are_open_to_admins(client, admin):
    for method, path, body in ADMIN_ROUTES[:3] + ADMIN_ROUTES[5:6]:
        res = getattr(client, method)(path, headers=admin)
        assert res.status_code == 200, (path, res.text)


# -- libros -----------------------------------------------------------------------------------------------------


def test_create_edit_and_read_a_book(client, admin, ae):
    created = client.post("/api/v1/admin/books", json=BOOK, headers=admin)
    assert created.status_code == 201
    book = created.json()
    assert book["slug"] == "libro-por-api" and book["author_name"] == "Autora Uno" and book["active"] is True
    assert book["final_price_cop"] == 30_000 and book["cover"] == "/covers/sin-portada.webp"

    patched = client.patch(f"/api/v1/admin/books/{book['id']}", json={"price_cop": 40_000, "discount_pct": 25, "stock": 9}, headers=admin)
    assert patched.status_code == 200
    assert (patched.json()["price_cop"], patched.json()["final_price_cop"], patched.json()["stock"]) == (40_000, 30_000, 9)
    assert client.get(f"/api/v1/admin/books/{book['id']}", headers=admin).json()["stock"] == 9
    assert client.patch("/api/v1/admin/books/fantasma", json={"stock": 1}, headers=admin).status_code == 404


def test_listing_includes_hidden_books_and_author_suggestions(client, admin):
    client.patch("/api/v1/admin/books/b1", json={"active": False}, headers=admin)
    body = client.get("/api/v1/admin/books", headers=admin).json()
    assert body["total"] == 4 and "Barato" in [b["title"] for b in body["items"]]
    assert next(b for b in body["items"] if b["id"] == "b1")["active"] is False
    assert body["authors"] == ["Autora Uno"]
    assert [b["id"] for b in client.get("/api/v1/admin/books?active=false", headers=admin).json()["items"]] == ["b1"]
    assert client.get("/api/v1/admin/books?q=agotado", headers=admin).json()["total"] == 1


def test_hiding_a_book_removes_it_from_the_public_api_and_showing_restores_it(client, admin):
    assert client.get("/api/v1/books/barato").status_code == 200
    client.patch("/api/v1/admin/books/b1", json={"active": False}, headers=admin)
    assert client.get("/api/v1/books/barato").status_code == 404
    assert "Barato" not in [b["title"] for b in client.get("/api/v1/books").json()["items"]]
    client.patch("/api/v1/admin/books/b1", json={"active": True}, headers=admin)
    assert client.get("/api/v1/books/barato").status_code == 200


def test_invalid_categories_are_422_and_nothing_is_created(client, admin, ae):
    res = client.post("/api/v1/admin/books", json={**BOOK, "category_ids": ["c99"]}, headers=admin)
    assert res.status_code == 422 and res.json()["detail"]["code"] == "invalid_category"
    assert len(ae.env.books.list()) == 4


@pytest.mark.parametrize(
    "override",
    [
        {"title": ""},
        {"title": "x" * 201},
        {"price_cop": -1},
        {"price_cop": 1_000_000_000},
        {"discount_pct": 91},
        {"discount_pct": -1},
        {"stock": -1},
        {"pages": 0},
        {"category_ids": []},
        {"author_name": "A"},
        {"shipping_cost_cop": -5},
        {"cover": "http://evil.com/x.webp"},
        {"cover": "//evil.com/x.webp"},
        {"cover": "/covers/../../etc/passwd.webp"},
        {"cover": "javascript:alert(1)"},
        {"cover": "/covers/x.png"},
        {"cover_blur": "data:text/html;base64,PHNjcmlwdD4="},
    ],
    ids=lambda o: str(o)[:45],
)
def test_invalid_book_data_is_422(client, admin, ae, override):
    assert client.post("/api/v1/admin/books", json={**BOOK, **override}, headers=admin).status_code == 422
    assert len(ae.env.books.list()) == 4


def test_a_client_cannot_smuggle_unknown_fields_into_a_book(client, admin, ae):
    res = client.post("/api/v1/admin/books", json={**BOOK, "id": "bk_999", "slug": "elegido-por-mi", "created_at": "2001-01-01T00:00:00Z"}, headers=admin)
    assert res.status_code == 201 and res.json()["id"] != "bk_999" and res.json()["slug"] == "libro-por-api"


# -- subida de portadas ---------------------------------------------------------------------------------------------


def test_cover_upload_converts_stores_and_serves(client, admin):
    res = client.post("/api/v1/admin/uploads/cover", files={"file": ("mi portada.png", png((1000, 2000)), "image/png")}, headers=admin)
    assert res.status_code == 201
    body = res.json()
    assert body["cover"].startswith("/media/covers/") and body["cover"].endswith(".webp")
    assert (body["cover_width"], body["cover_height"]) == (400, 800) and body["cover_blur"].startswith("data:image/webp;base64,")

    name = body["cover"].rsplit("/", 1)[1]
    stored = settings.media_dir / "covers" / name
    assert stored.is_file()
    with Image.open(stored) as saved:
        assert saved.format == "WEBP"

    served = client.get(f"/api/v1/media/covers/{name}")
    assert served.status_code == 200 and served.headers["content-type"] == "image/webp"
    assert "immutable" in served.headers["cache-control"]


def test_upload_never_uses_the_uploaded_file_name(client, admin):
    res = client.post("/api/v1/admin/uploads/cover", files={"file": ("../../evil.png", png(), "image/png")}, headers=admin)
    name = res.json()["cover"].rsplit("/", 1)[1]
    assert res.status_code == 201 and "evil" not in name and len(name) == 32 + len(".webp")
    assert not (settings.media_dir / "evil.png").exists()


def test_an_uploaded_cover_can_be_used_by_a_book(client, admin):
    cover = client.post("/api/v1/admin/uploads/cover", files={"file": ("a.png", png(), "image/png")}, headers=admin).json()
    res = client.post("/api/v1/admin/books", json={**BOOK, **cover}, headers=admin)
    assert res.status_code == 201 and res.json()["cover"] == cover["cover"]
    assert client.get(f"/api/v1/books/{res.json()['slug']}").json()["cover"] == cover["cover"]


@pytest.mark.parametrize(
    "name, data, content_type",
    [
        ("nota.txt", b"hola, no soy una imagen", "text/plain"),
        ("falsa.png", b"esto tampoco es un png", "image/png"),  # extensión y tipo mienten: manda el contenido
        ("dibujo.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "image/svg+xml"),
        ("animada.gif", None, "image/gif"),
        ("grande.png", b"\x89PNG" + b"\x00" * (5 * 1024 * 1024 + 10), "image/png"),
        ("bomba.png", "bomb", "image/png"),
        ("vacio.png", b"", "image/png"),
    ],
    ids=["texto", "png falso", "svg", "gif", "más de 5 MB", "bomba de píxeles", "vacío"],
)
def test_bad_uploads_are_rejected_with_a_clear_message(client, admin, name, data, content_type):
    if name.endswith(".gif"):
        buffer = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buffer, "GIF")
        data = buffer.getvalue()
    if data == "bomb":
        data = png((7000, 7000))
    before = set((settings.media_dir / "covers").glob("*")) if (settings.media_dir / "covers").exists() else set()
    res = client.post("/api/v1/admin/uploads/cover", files={"file": (name, data, content_type)}, headers=admin)
    assert res.status_code == 422 and res.json()["detail"]["code"] == "invalid_image" and res.json()["detail"]["message"]
    after = set((settings.media_dir / "covers").glob("*")) if (settings.media_dir / "covers").exists() else set()
    assert after == before  # no queda nada a medias en disco


def test_upload_without_a_file_is_422(client, admin):
    assert client.post("/api/v1/admin/uploads/cover", headers=admin).status_code == 422


@pytest.mark.parametrize(
    "name",
    ["../secret.webp", "..%2F..%2Fsecret.webp", "abc.webp", "A" * 32 + ".webp", "0" * 32 + ".png", "0" * 32 + ".webp.png", "0" * 32, "%2e%2e", "0" * 31 + "g.webp"],
)
def test_media_endpoint_only_serves_generated_names(client, name):
    assert client.get(f"/api/v1/media/covers/{name}").status_code == 404


def test_media_endpoint_404_for_a_valid_name_that_does_not_exist(client):
    assert client.get(f"/api/v1/media/covers/{'0' * 32}.webp").status_code == 404


# -- pedidos ---------------------------------------------------------------------------------------------------


@pytest.fixture
def order(ae):
    ana = ae.env.new_user("comprador@correo.com")
    paid, _ = ae.env.service.checkout(ana, checkout_data([("b1", 2)]))
    return paid


def test_order_list_and_detail_include_the_customer(client, admin, order):
    listed = client.get("/api/v1/admin/orders", headers=admin).json()
    assert listed["total"] == 1 and listed["items"][0]["number"] == "OB-000001"
    assert listed["items"][0]["customer"] == {"name": "Ana Pérez", "email": "comprador@correo.com"}
    detail = client.get(f"/api/v1/admin/orders/{order.id}", headers=admin).json()
    assert detail["shipping"]["line"] == "Calle 10 # 5-20" and detail["payment"]["method"] == "Visa •••• 4242"
    assert "4242424242424242" not in str(detail)


def test_order_filters(client, admin, ae, order):
    luis = ae.env.new_user("luis@correo.com")
    ae.env.service.checkout(luis, checkout_data([("b1", 1)], key="clave-de-luis-01", card=DECLINED_CARD))
    assert client.get("/api/v1/admin/orders?status=failed", headers=admin).json()["total"] == 1
    assert client.get("/api/v1/admin/orders?q=comprador", headers=admin).json()["total"] == 1
    assert client.get("/api/v1/admin/orders?status=inventado", headers=admin).status_code == 422


def test_status_flow_through_the_api(client, admin, ae, order):
    url = f"/api/v1/admin/orders/{order.id}/status"
    assert client.post(url, json={"status": "shipped"}, headers=admin).json()["status"] == "shipped"
    blocked = client.post(url, json={"status": "cancelled"}, headers=admin)
    assert blocked.status_code == 409 and blocked.json()["detail"]["code"] == "invalid_transition"
    assert client.post(url, json={"status": "delivered"}, headers=admin).json()["status"] == "delivered"


def test_cancelling_via_the_api_restores_stock(client, admin, ae, order):
    assert ae.env.stock("b1") == 18
    res = client.post(f"/api/v1/admin/orders/{order.id}/status", json={"status": "cancelled"}, headers=admin)
    assert res.status_code == 200 and res.json()["status"] == "cancelled" and ae.env.stock("b1") == 20


@pytest.mark.parametrize("status", ["paid", "pending", "failed", "inventado", ""])
def test_status_endpoint_only_accepts_the_three_admin_transitions(client, admin, order, status):
    assert client.post(f"/api/v1/admin/orders/{order.id}/status", json={"status": status}, headers=admin).status_code == 422


def test_unknown_order_is_404(client, admin):
    assert client.get("/api/v1/admin/orders/ord_999999", headers=admin).status_code == 404
    assert client.post("/api/v1/admin/orders/ord_999999/status", json={"status": "shipped"}, headers=admin).status_code == 404


def test_customers_still_only_see_their_own_orders(client, admin, order, ae):
    other = headers_for(ae, "otro@correo.com")
    assert client.get("/api/v1/orders", headers=other).json() == []
    assert client.get(f"/api/v1/orders/{order.id}", headers=other).status_code == 404


def test_summary(client, admin, order):
    body = client.get("/api/v1/admin/summary", headers=admin).json()
    assert body["books"]["total"] == 4 and body["orders"]["by_status"] == {"paid": 1} and body["orders"]["revenue_cop"] == order.total_cop

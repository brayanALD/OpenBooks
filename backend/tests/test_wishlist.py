"""Favoritos: servicio y API. Todo en memoria: no toca wishlists.json ni users.json."""

import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_auth_service, get_wishlist_service
from app.domain.models import Author, Category, Wishlist
from app.main import app
from app.repositories.memory_repo import InMemoryRepository
from app.services.catalog_service import CatalogService
from app.services.wishlist_service import MAX_FAVORITES, WishlistError, WishlistService
from tests.conftest import make_book
from tests.order_env import build_env


def build_service(extra_books=()) -> WishlistService:
    books = [make_book(f"b{i}", f"Libro {i}", "a1", ["c1"]) for i in (1, 2, 3)]
    books.append(make_book("hidden", "Oculto", "a1", ["c1"], active=False))
    catalog = CatalogService(
        InMemoryRepository([*books, *extra_books]),
        InMemoryRepository([Author(id="a1", name="Autora", slug="autora")]),
        InMemoryRepository([Category(id="c1", name="Novela", slug="novela")]),
        InMemoryRepository([]),
    )
    return WishlistService(catalog, InMemoryRepository[Wishlist]([]))


@pytest.fixture
def service() -> WishlistService:
    return build_service()


# -- servicio ---------------------------------------------------------------------------------------------------


def test_a_new_user_has_no_favorites(service):
    assert service.ids("u1") == []
    assert service.books("u1") == []


def test_newest_favorite_comes_first(service):
    service.add("u1", "b1")
    service.add("u1", "b2")
    assert service.ids("u1") == ["b2", "b1"]
    assert [b.title for b in service.books("u1")] == ["Libro 2", "Libro 1"]


def test_adding_twice_is_idempotent_and_keeps_position(service):
    service.add("u1", "b1")
    service.add("u1", "b2")
    service.add("u1", "b1")
    assert service.ids("u1") == ["b2", "b1"]


def test_remove_and_remove_again(service):
    service.add("u1", "b1")
    assert service.remove("u1", "b1") == []
    assert service.remove("u1", "b1") == []  # quitar algo que no está no es un error
    assert service.remove("u1", "nada") == []


def test_favorites_are_per_user(service):
    service.add("u1", "b1")
    service.add("u2", "b2")
    assert service.ids("u1") == ["b1"]
    assert service.ids("u2") == ["b2"]


def test_unknown_or_hidden_books_cannot_be_added(service):
    for book_id in ("nope", "hidden"):
        with pytest.raises(WishlistError) as error:
            service.add("u1", book_id)
        assert error.value.code == "not_found"
    assert service.ids("u1") == []


def test_a_book_hidden_later_disappears_but_comes_back_when_reactivated():
    hidden_later = make_book("b9", "Se oculta", "a1", ["c1"])
    service = build_service([hidden_later])
    service.add("u1", "b9")
    service.add("u1", "b1")

    books = service._catalog._books  # el repositorio en memoria del catálogo
    books.update(hidden_later.model_copy(update={"active": False}))
    assert service.ids("u1") == ["b1"]  # no aparece ni cuenta

    books.update(hidden_later)
    assert service.ids("u1") == ["b1", "b9"]


def test_the_list_has_a_maximum():
    many = [make_book(f"x{i}", f"Extra {i}", "a1", ["c1"]) for i in range(MAX_FAVORITES + 1)]
    service = build_service(many)
    for i in range(MAX_FAVORITES):
        service.add("u1", f"x{i}")
    with pytest.raises(WishlistError) as error:
        service.add("u1", f"x{MAX_FAVORITES}")
    assert error.value.code == "full"
    assert len(service.ids("u1")) == MAX_FAVORITES
    service.add("u1", "x0")  # repetir uno que ya está sigue funcionando


def test_concurrent_adds_do_not_lose_favorites():
    """Sin el candado, dos altas simultáneas leen la misma lista y una pisa a la otra."""
    service = build_service()
    original = service._wishlists.get

    def slow_get(id):
        result = original(id)
        time.sleep(0.005)  # ensancha la ventana de la carrera
        return result

    service._wishlists.get = slow_get
    threads = [threading.Thread(target=service.add, args=("u1", b)) for b in ("b1", "b2", "b3")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert set(service.ids("u1")) == {"b1", "b2", "b3"}


# -- API --------------------------------------------------------------------------------------------------------


@pytest.fixture
def env():
    e = build_env()
    app.dependency_overrides[get_auth_service] = lambda: e.auth
    service = build_service()
    app.dependency_overrides[get_wishlist_service] = lambda: service
    yield e
    app.dependency_overrides.clear()


@pytest.fixture
def client(env):
    return TestClient(app)


def session(env, email="ana@correo.com"):
    user = env.new_user(email)
    return {"Authorization": f"Bearer {env.auth.create_token(user)}"}


@pytest.mark.parametrize(
    "method, path",
    [("get", "/api/v1/wishlist"), ("get", "/api/v1/wishlist/ids"), ("put", "/api/v1/wishlist/b1"), ("delete", "/api/v1/wishlist/b1")],
)
def test_wishlist_requires_a_session(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_full_flow(client, env):
    headers = session(env)
    assert client.get("/api/v1/wishlist/ids", headers=headers).json() == {"book_ids": []}

    assert client.put("/api/v1/wishlist/b1", headers=headers).json() == {"book_ids": ["b1"]}
    assert client.put("/api/v1/wishlist/b2", headers=headers).json() == {"book_ids": ["b2", "b1"]}

    items = client.get("/api/v1/wishlist", headers=headers).json()["items"]
    assert [i["id"] for i in items] == ["b2", "b1"]
    assert items[0]["title"] == "Libro 2" and "final_price_cop" in items[0]

    assert client.delete("/api/v1/wishlist/b2", headers=headers).json() == {"book_ids": ["b1"]}


def test_unknown_book_is_404_with_a_message(client, env):
    response = client.put("/api/v1/wishlist/nope", headers=session(env))
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "not_found"


def test_users_do_not_see_each_others_favorites(client, env):
    ana, luis = session(env, "ana@correo.com"), session(env, "luis@correo.com")
    client.put("/api/v1/wishlist/b1", headers=ana)
    assert client.get("/api/v1/wishlist/ids", headers=luis).json() == {"book_ids": []}

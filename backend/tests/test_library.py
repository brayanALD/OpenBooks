"""Librero: lo que compró cada usuario, sin duplicados. Todo en memoria, vía la API."""

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_auth_service, get_catalog_service, get_order_service
from app.main import app
from tests.order_env import DECLINED_CARD, build_env, checkout_data


@pytest.fixture
def env():
    e = build_env()
    app.dependency_overrides[get_auth_service] = lambda: e.auth
    app.dependency_overrides[get_order_service] = lambda: e.service
    app.dependency_overrides[get_catalog_service] = lambda: e.catalog
    yield e
    app.dependency_overrides.clear()


@pytest.fixture
def client(env):
    return TestClient(app)


def session(env, email="ana@correo.com"):
    user = env.new_user(email)
    return user, {"Authorization": f"Bearer {env.auth.create_token(user)}"}


def test_library_requires_a_session(client):
    assert client.get("/api/v1/library").status_code == 401


def test_a_user_with_no_orders_has_an_empty_library(client, env):
    _, headers = session(env)
    assert client.get("/api/v1/library", headers=headers).json() == {"items": [], "unavailable": []}


def test_buying_two_units_of_the_same_book_shows_it_once(client, env):
    user, headers = session(env)
    env.service.checkout(user, checkout_data([("b1", 2)]))

    body = client.get("/api/v1/library", headers=headers).json()
    assert [i["id"] for i in body["items"]] == ["b1"]
    assert body["unavailable"] == []


def test_buying_the_same_book_in_two_orders_shows_it_once(client, env):
    user, headers = session(env)
    env.service.checkout(user, checkout_data([("b1", 1)], key="compra-1"))
    env.service.checkout(user, checkout_data([("b1", 1), ("b2", 1)], key="compra-2"))

    body = client.get("/api/v1/library", headers=headers).json()
    assert sorted(i["id"] for i in body["items"]) == ["b1", "b2"]


def test_unpaid_orders_do_not_count_as_owned(client, env):
    user, headers = session(env)
    env.service.checkout(user, checkout_data([("b1", 1)], card=DECLINED_CARD, key="rechazada"))

    body = client.get("/api/v1/library", headers=headers).json()
    assert body == {"items": [], "unavailable": []}


def test_a_hidden_book_moves_to_unavailable_but_keeps_its_frozen_data(client, env):
    user, headers = session(env)
    env.service.checkout(user, checkout_data([("b1", 1)]))

    book = env.books.get("b1")
    env.books.update(book.model_copy(update={"active": False}))

    body = client.get("/api/v1/library", headers=headers).json()
    assert body["items"] == []
    assert body["unavailable"] == [{"book_id": "b1", "title": "Barato", "author_name": "Autora Uno", "cover": book.cover}]

    env.books.update(book)  # se reactiva
    body = client.get("/api/v1/library", headers=headers).json()
    assert [i["id"] for i in body["items"]] == ["b1"]
    assert body["unavailable"] == []


def test_users_do_not_see_each_others_library(client, env):
    ana_user, ana = session(env, "ana@correo.com")
    luis_user, luis = session(env, "luis@correo.com")
    env.service.checkout(ana_user, checkout_data([("b1", 1)]))
    env.service.checkout(luis_user, checkout_data([("b2", 1)]))

    assert [i["id"] for i in client.get("/api/v1/library", headers=ana).json()["items"]] == ["b1"]
    assert [i["id"] for i in client.get("/api/v1/library", headers=luis).json()["items"]] == ["b2"]

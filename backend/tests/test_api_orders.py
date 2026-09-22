"""Pedidos por la API. Todo en memoria: no toca users.json, orders.json ni books.json."""

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_auth_service, get_catalog_service, get_order_service
from app.main import app
from tests.order_env import DECLINED_CARD, GOOD_CARD, build_env

CARD_NUMBER = "4242424242424242"


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
    return {"Authorization": f"Bearer {env.auth.create_token(user)}"}


def payload(items=(("b1", 2),), *, card=GOOD_CARD, key="clave-unica-0001", total=None, **overrides):
    if total is None:
        prices = {"b1": 10_000, "b2": 80_000}
        total = sum(prices[b] * q for b, q in items) + (5_000 if any(b == "b2" for b, _ in items) else 0)
    body = {
        "items": [{"book_id": b, "quantity": q} for b, q in items],
        "shipping": {"recipient_name": "Ana Pérez", "phone": "300 123 4567", "line": "Calle 10 # 5-20", "city": "Bogotá", "notes": "Torre 2"},
        "card": {"number": card, "cvc": "123", "holder": "ANA PEREZ", "exp_month": 12, "exp_year": 2035},
        "idempotency_key": key,
        "expected_total_cop": total,
    }
    body.update(overrides)
    return body


# -- acceso ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("method, path", [("post", "/api/v1/orders"), ("get", "/api/v1/orders"), ("get", "/api/v1/orders/ord_000001")])
def test_orders_require_a_session(client, method, path):
    kwargs = {"json": payload()} if method == "post" else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


# -- compra ------------------------------------------------------------------------------------------------------


def test_successful_checkout(client, env):
    headers = session(env)
    res = client.post("/api/v1/orders", json=payload(), headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "paid" and body["number"] == "OB-000001" and body["total_cop"] == 20_000
    assert body["payment"] == {"status": "approved", "method": "Visa •••• 4242", "reference": body["payment"]["reference"], "failure_reason": None}
    assert body["shipping"]["phone"] == "3001234567" and body["items"][0]["title"] == "Barato"
    assert env.stock("b1") == 18


def test_card_data_never_appears_in_responses(client, env):
    headers = session(env)
    created = client.post("/api/v1/orders", json=payload(), headers=headers).text
    listed = client.get("/api/v1/orders", headers=headers).text
    for text in (created, listed):
        assert CARD_NUMBER not in text and "4242 4242" not in text and '"cvc"' not in text and "ANA PEREZ" not in text


def test_replaying_the_same_key_returns_200_and_the_same_order(client, env):
    headers = session(env)
    first = client.post("/api/v1/orders", json=payload(), headers=headers)
    again = client.post("/api/v1/orders", json=payload(), headers=headers)
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["id"] == again.json()["id"] and env.stock("b1") == 18
    assert len(env.provider.charges) == 1


def test_declined_payment_is_a_failed_order_not_an_http_error(client, env):
    res = client.post("/api/v1/orders", json=payload(card=DECLINED_CARD), headers=session(env))
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "failed" and "rechazada" in body["payment"]["failure_reason"] and env.stock("b1") == 20


def test_changed_total_is_409_with_a_code(client, env):
    res = client.post("/api/v1/orders", json=payload(total=1), headers=session(env))
    assert res.status_code == 409 and res.json()["detail"]["code"] == "total_changed"
    assert env.stock("b1") == 20


def test_unavailable_stock_is_409(client, env):
    res = client.post("/api/v1/orders", json=payload([("b4", 1)], total=0), headers=session(env))
    assert res.status_code == 409 and res.json()["detail"]["code"] == "cart_issues"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.update(items=[]),
        lambda b: b["card"].update(number="4242424242424241"),  # Luhn inválido
        lambda b: b["card"].update(exp_month=1, exp_year=2020),  # vencida
        lambda b: b["card"].update(cvc="12"),
        lambda b: b["shipping"].update(line="x"),
        lambda b: b["shipping"].update(phone="123"),
        lambda b: b.update(idempotency_key="corta"),
        lambda b: b.update(idempotency_key="tiene espacios y ñ!!"),
        lambda b: b.update(expected_total_cop=-1),
        lambda b: b.pop("card"),
        lambda b: b.pop("shipping"),
    ],
)
def test_invalid_checkout_payloads_are_422_and_change_nothing(client, env, mutate):
    body = payload()
    mutate(body)
    assert client.post("/api/v1/orders", json=body, headers=session(env)).status_code == 422
    assert env.stock("b1") == 20 and env.orders.list() == []


def test_validation_errors_do_not_echo_what_the_user_typed(client, env):
    body = payload()
    body["card"].update(number="4242 4242 4242 4241", cvc="12")
    res = client.post("/api/v1/orders", json=body, headers=session(env))
    assert res.status_code == 422
    assert "4242" not in res.text and '"12"' not in res.text and "input" not in res.text
    fields = {tuple(e["loc"]) for e in res.json()["detail"]}
    assert ("body", "card", "number") in fields and ("body", "card", "cvc") in fields  # sí dice QUÉ campo falla


def test_passwords_are_not_echoed_in_registration_errors(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"first_name": "Ana", "last_name": "P", "email": "a@correo.com", "address": {"line": "Calle 1 # 2", "city": "Cali"}, "password": "corta-1"},
    )
    assert res.status_code == 422 and "corta-1" not in res.text


# -- consulta ------------------------------------------------------------------------------------------------------


def test_listing_and_detail_only_show_my_orders(client, env):
    ana, luis = session(env, "ana@correo.com"), session(env, "luis@correo.com")
    mine = client.post("/api/v1/orders", json=payload(key="clave-de-ana-001"), headers=ana).json()
    client.post("/api/v1/orders", json=payload(key="clave-de-luis-01"), headers=luis)

    assert [o["id"] for o in client.get("/api/v1/orders", headers=ana).json()] == [mine["id"]]
    assert client.get(f"/api/v1/orders/{mine['id']}", headers=ana).json()["number"] == mine["number"]
    assert client.get(f"/api/v1/orders/{mine['id']}", headers=luis).status_code == 404  # 404, no 403: no revela que existe
    assert client.get("/api/v1/orders/ord_999999", headers=ana).status_code == 404


# -- recomendaciones ---------------------------------------------------------------------------------------------


def test_recommended_books_is_public_but_personalizes_with_a_paid_order(client, env):
    anon = client.get("/api/v1/books/recommended").json()
    assert {b["title"] for b in anon} == {"Barato", "Con descuento", "Ultima unidad", "Agotado"}  # sin filtrar

    headers = session(env)
    client.post("/api/v1/orders", json=payload(), headers=headers)  # compra "Barato" (b1) y paga

    mine = client.get("/api/v1/books/recommended", headers=headers).json()
    assert "Barato" not in {b["title"] for b in mine}  # ya comprado: no se recomienda de nuevo


def test_recommended_books_ignores_unpaid_orders(client, env):
    headers = session(env)
    client.post("/api/v1/orders", json=payload(card=DECLINED_CARD, key="rechazada-1"), headers=headers)

    mine = client.get("/api/v1/books/recommended", headers=headers).json()
    assert "Barato" in {b["title"] for b in mine}  # el pago falló: sigue sin comprar


def test_failed_orders_show_up_in_the_history(client, env):
    headers = session(env)
    client.post("/api/v1/orders", json=payload(card=DECLINED_CARD, key="intento-numero-1"), headers=headers)
    client.post("/api/v1/orders", json=payload(key="intento-numero-2"), headers=headers)
    assert [o["status"] for o in client.get("/api/v1/orders", headers=headers).json()] == ["paid", "failed"]

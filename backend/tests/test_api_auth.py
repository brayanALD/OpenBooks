"""Autenticación y carrito guardado por la API. Usuarios y carritos en memoria: no tocan users.json."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import security
from app.core.deps import (
    get_auth_service,
    get_cart_storage,
    get_catalog_service,
    get_current_user,
    require_admin,
)
from app.domain.models import Cart, User
from app.main import app
from app.repositories.memory_repo import InMemoryRepository
from app.services.auth_service import AuthService, LoginThrottle
from app.services.cart_storage import CartStorage

SECRET = "un-secreto-de-prueba-suficientemente-largo-123"

PAYLOAD = {
    "first_name": "Ana",
    "last_name": "Pérez",
    "email": "Ana@Correo.com",
    "phone": "300 123 4567",
    "address": {"line": "Calle 10 # 5-20", "city": "Bogotá", "notes": "Torre 2"},
    "password": "clave-segura-1",
}


@pytest.fixture
def client():
    users = InMemoryRepository[User]([])
    auth = AuthService(users, SECRET, 60, LoginThrottle(max_attempts=5, window=900))
    storage = CartStorage(get_catalog_service(), InMemoryRepository[Cart]([]))
    app.dependency_overrides[get_auth_service] = lambda: auth
    app.dependency_overrides[get_cart_storage] = lambda: storage
    yield TestClient(app)
    app.dependency_overrides.clear()


def register(client, **overrides):
    return client.post("/api/v1/auth/register", json={**PAYLOAD, **overrides})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def book_ids(client, n=3):
    return [b["id"] for b in client.get("/api/v1/books", params={"page_size": n, "sort": "title"}).json()["items"]]


# -- registro ---------------------------------------------------------------------------------------


def test_register_returns_a_session_and_the_user(client):
    res = register(client)
    assert res.status_code == 201
    body = res.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    user = body["user"]
    assert user["email"] == "ana@correo.com" and user["phone"] == "3001234567" and user["role"] == "customer"
    assert user["address"] == {"line": "Calle 10 # 5-20", "city": "Bogotá", "notes": "Torre 2"}


def test_responses_never_leak_the_password_hash(client):
    body = register(client).json()
    assert "password" not in str(body).lower() and "argon2" not in str(body)
    me = client.get("/api/v1/auth/me", headers=bearer(body["access_token"])).text
    assert "password" not in me.lower() and "argon2" not in me


def test_client_cannot_choose_its_own_role(client):
    body = register(client, role="admin").json()
    assert body["user"]["role"] == "customer"


def test_duplicate_email_is_409(client):
    register(client)
    res = register(client, email="ANA@correo.com")
    assert res.status_code == 409 and "correo" in res.json()["detail"]


def test_optional_phone_can_be_omitted(client):
    payload = {k: v for k, v in PAYLOAD.items() if k != "phone"}
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201 and res.json()["user"]["phone"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "corta"},
        {"email": "no-es-correo"},
        {"phone": "12345"},
        {"first_name": ""},
        {"address": {"line": "x", "city": "Bogotá"}},
        {"address": None},
    ],
)
def test_invalid_registration_is_422(client, overrides):
    assert register(client, **overrides).status_code == 422


# -- login ------------------------------------------------------------------------------------------


def test_login_ok(client):
    register(client)
    res = client.post("/api/v1/auth/login", json={"email": "ANA@correo.com", "password": "clave-segura-1"})
    assert res.status_code == 200 and res.json()["user"]["email"] == "ana@correo.com"


def test_wrong_password_and_unknown_user_give_the_same_401(client):
    register(client)
    wrong = client.post("/api/v1/auth/login", json={"email": "ana@correo.com", "password": "mala"})
    unknown = client.post("/api/v1/auth/login", json={"email": "nadie@correo.com", "password": "mala"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Correo o contraseña incorrectos"}


def test_brute_force_gets_429_with_retry_after(client):
    register(client)
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"email": "ana@correo.com", "password": "mala"}).status_code == 401
    res = client.post("/api/v1/auth/login", json={"email": "ana@correo.com", "password": "clave-segura-1"})
    assert res.status_code == 429 and int(res.headers["Retry-After"]) > 0


# -- /me y tokens ----------------------------------------------------------------------------------------


def test_me_with_a_valid_token(client):
    token = register(client).json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=bearer(token)).json()["first_name"] == "Ana"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer basura"}, {"Authorization": "Token abc"}, {"Authorization": "Bearer "}])
def test_me_without_a_valid_token_is_401(client, headers):
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401 and res.headers["www-authenticate"] == "Bearer"


def test_expired_and_forged_tokens_are_401(client):
    user_id = register(client).json()["user"]["id"]
    expired = security.create_access_token(user_id, SECRET, -1)
    forged = security.create_access_token(user_id, "otro-secreto", 60)
    for token in (expired, forged):
        assert client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 401


def test_token_for_a_user_that_does_not_exist_is_401(client):
    ghost = security.create_access_token("usr_fantasma", SECRET, 60)
    assert client.get("/api/v1/auth/me", headers=bearer(ghost)).status_code == 401


def test_require_admin_allows_admins_and_blocks_customers():
    users = InMemoryRepository[User]([])
    auth = AuthService(users, SECRET, 60)
    from app.schemas.auth import AddressIn, RegisterIn

    def signup(email, role):
        data = RegisterIn(first_name="A", last_name="B", email=email, address=AddressIn(line="Calle 1 # 2", city="Cali"), password="clave-segura-1")
        return auth.create_token(auth.register(data, role=role))

    mini = FastAPI()

    @mini.get("/solo-admin")
    def only_admin(user: User = Depends(require_admin)):
        return {"ok": user.email}

    mini.dependency_overrides[get_auth_service] = lambda: auth
    http = TestClient(mini)
    assert http.get("/solo-admin", headers=bearer(signup("admin@correo.com", "admin"))).json() == {"ok": "admin@correo.com"}
    assert http.get("/solo-admin", headers=bearer(signup("cliente@correo.com", "customer"))).status_code == 403
    assert http.get("/solo-admin").status_code == 401
    assert get_current_user  # el módulo expone la dependencia base


# -- carrito guardado -------------------------------------------------------------------------------------


@pytest.mark.parametrize("method, path", [("get", "/api/v1/cart"), ("put", "/api/v1/cart"), ("post", "/api/v1/cart/merge")])
def test_saved_cart_requires_a_session(client, method, path):
    kwargs = {} if method == "get" else {"json": {"items": []}}
    assert getattr(client, method)(path, **kwargs).status_code == 401


def test_validate_stays_public(client):
    assert client.post("/api/v1/cart/validate", json={"items": []}).status_code == 200


def test_saved_cart_roundtrip_and_isolation(client):
    a, b = book_ids(client, 2)
    ana = register(client).json()["access_token"]
    luis = register(client, email="luis@correo.com").json()["access_token"]

    put = client.put("/api/v1/cart", json={"items": [{"book_id": a, "quantity": 2}]}, headers=bearer(ana))
    assert put.json() == {"items": [{"book_id": a, "quantity": 2}], "removed": []}
    assert client.get("/api/v1/cart", headers=bearer(ana)).json()["items"] == [{"book_id": a, "quantity": 2}]
    assert client.get("/api/v1/cart", headers=bearer(luis)).json()["items"] == []  # no ve el carrito de Ana


def test_merge_endpoint_sums_guest_and_saved_carts(client):
    a, b = book_ids(client, 2)
    token = register(client).json()["access_token"]
    client.put("/api/v1/cart", json={"items": [{"book_id": a, "quantity": 2}]}, headers=bearer(token))
    merged = client.post(
        "/api/v1/cart/merge",
        json={"items": [{"book_id": a, "quantity": 3}, {"book_id": b, "quantity": 1}, {"book_id": "fantasma", "quantity": 4}]},
        headers=bearer(token),
    ).json()
    assert merged["items"] == [{"book_id": a, "quantity": 5}, {"book_id": b, "quantity": 1}]


def test_saved_cart_rejects_bad_payloads(client):
    token = register(client).json()["access_token"]
    for bad in ({}, {"items": [{"book_id": "x", "quantity": 0}]}, {"items": [{"book_id": "x", "quantity": 1000}]}):
        assert client.put("/api/v1/cart", json=bad, headers=bearer(token)).status_code == 422


def test_get_cart_reports_removed_books(client):
    a, b = book_ids(client, 2)
    token = register(client).json()["access_token"]
    client.put("/api/v1/cart", json={"items": [{"book_id": a, "quantity": 1}, {"book_id": b, "quantity": 2}]}, headers=bearer(token))
    first = client.get("/api/v1/cart", headers=bearer(token)).json()
    assert first == {"items": [{"book_id": a, "quantity": 1}, {"book_id": b, "quantity": 2}], "removed": []}

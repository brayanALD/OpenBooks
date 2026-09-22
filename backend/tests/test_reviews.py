"""Reseñas de compradores verificados: servicio y API, con repositorios en memoria."""

import threading
import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.deps import get_admin_service, get_auth_service, get_catalog_service, get_order_service, get_review_service
from app.domain.models import Review
from app.main import app
from app.repositories.memory_repo import InMemoryRepository
from app.schemas.admin import BookUpdateIn
from app.schemas.reviews import ReviewIn
from app.services.catalog_service import CatalogService
from app.services.review_service import ReviewError, ReviewService
from tests.admin_env import build_admin_env
from tests.conftest import NOW
from tests.order_env import DECLINED_CARD, checkout_data

GOOD_COMMENT = "Me gustó mucho, lo recomiendo."


@pytest.fixture
def ae():
    return build_admin_env()


@pytest.fixture
def svc(ae):
    return ReviewService(InMemoryRepository[Review]([]), ae.env.books, ae.env.orders)


def buy(ae, user, slug_items, key="clave-unica-0001", **kw):
    order, _ = ae.env.service.checkout(user, checkout_data(slug_items, key=key, **kw))
    return order


def data(rating=5, comment=GOOD_COMMENT):
    return ReviewIn(rating=rating, comment=comment)


# -- quién puede reseñar ---------------------------------------------------------------------------------


def test_only_buyers_can_review(ae, svc):
    ana, luis = ae.env.new_user("ana@correo.com"), ae.env.new_user("luis@correo.com")
    buy(ae, ana, [("b1", 1)])
    with pytest.raises(ReviewError) as error:
        svc.create(luis, "barato", data())
    assert error.value.code == "not_eligible"
    assert svc.create(ana, "barato", data()).book_id == "b1"


@pytest.mark.parametrize("final_status", ["paid", "shipped", "delivered"])
def test_paid_shipped_and_delivered_orders_count_as_a_purchase(ae, svc, final_status):
    ana = ae.env.new_user()
    order = buy(ae, ana, [("b1", 1)])
    for step in {"paid": [], "shipped": ["shipped"], "delivered": ["shipped", "delivered"]}[final_status]:
        ae.admin.change_order_status(order.id, step)
    assert svc.status(ana, "barato")[0] is True


def test_failed_and_cancelled_orders_do_not_count(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)], key="intento-numero-1", card=DECLINED_CARD)  # pago rechazado
    assert svc.status(ana, "barato")[:2] == (False, False)
    cancelled = buy(ae, ana, [("b1", 1)], key="intento-numero-2")
    ae.admin.change_order_status(cancelled.id, "cancelled")
    assert svc.status(ana, "barato")[:2] == (False, False)
    with pytest.raises(ReviewError) as error:
        svc.create(ana, "barato", data())
    assert error.value.code == "not_eligible"


def test_buying_one_book_does_not_allow_reviewing_another(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    with pytest.raises(ReviewError):
        svc.create(ana, "con-descuento", data())


def test_someone_elses_purchase_does_not_count(ae, svc):
    buy(ae, ae.env.new_user("comprador@correo.com"), [("b1", 1)])
    intruso = ae.env.new_user("intruso@correo.com")
    with pytest.raises(ReviewError):
        svc.create(intruso, "barato", data())


def test_unknown_and_hidden_books_are_not_found(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    for slug in ("no-existe",):
        with pytest.raises(ReviewError) as error:
            svc.create(ana, slug, data())
        assert error.value.code == "not_found"
    ae.admin.update_book("b1", BookUpdateIn(active=False))
    with pytest.raises(ReviewError) as hidden:
        svc.create(ana, "barato", data())
    assert hidden.value.code == "not_found"


# -- una por libro, editable y borrable ----------------------------------------------------------------------


def test_one_review_per_person_and_book(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 2)])
    svc.create(ana, "barato", data())
    with pytest.raises(ReviewError) as error:
        svc.create(ana, "barato", data(4, "Otra opinión distinta."))
    assert error.value.code == "already_reviewed"
    assert svc.status(ana, "barato")[0] is False  # ya no puede crear otra


def test_the_review_shows_first_name_and_last_initial_only(ae, svc):
    ana = ae.env.new_user("ana.secreta@correo.com")
    buy(ae, ana, [("b1", 1)])
    review = svc.create(ana, "barato", data())
    assert review.author_name == "Ana P." and "secreta" not in review.author_name and review.user_id == ana.id
    assert review.is_demo is False and review.updated_at is None


def test_edit_own_review_keeps_identity_and_marks_the_edit(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    original = svc.create(ana, "barato", data(5))
    edited = svc.update(ana, "barato", data(3, "Después de releerlo, me gustó menos."))
    assert (edited.id, edited.created_at) == (original.id, original.created_at)
    assert (edited.rating, edited.comment) == (3, "Después de releerlo, me gustó menos.") and edited.updated_at is not None


def test_cannot_edit_or_delete_what_you_did_not_write(ae, svc):
    ana, luis = ae.env.new_user("ana@correo.com"), ae.env.new_user("luis@correo.com")
    buy(ae, ana, [("b1", 1)])
    buy(ae, luis, [("b1", 1)], key="clave-de-luis-01")
    svc.create(ana, "barato", data(5, "La reseña de Ana, muy buena."))
    # Luis compró el libro pero no ha reseñado: «mi reseña» para él no existe, no puede tocar la de Ana.
    with pytest.raises(ReviewError) as edit:
        svc.update(luis, "barato", data(1, "Intento pisar la reseña de Ana."))
    with pytest.raises(ReviewError) as delete:
        svc.delete_mine(luis, "barato")
    assert edit.value.code == delete.value.code == "not_found"
    assert svc._mine(ana.id, "b1").comment == "La reseña de Ana, muy buena."


def test_delete_then_review_again(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    svc.create(ana, "barato", data())
    svc.delete_mine(ana, "barato")
    assert svc.status(ana, "barato") [0] is True
    assert svc.create(ana, "barato", data(2, "Ahora opino distinto, la verdad.")).rating == 2


def test_ids_continue_after_the_existing_ones(ae):
    seed = [Review(id="rv_072", book_id="b2", user_id=None, author_name="Demo", rating=4, comment="Comentario de muestra", is_demo=True, created_at=NOW)]
    svc = ReviewService(InMemoryRepository(seed), ae.env.books, ae.env.orders)
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    assert svc.create(ana, "barato", data()).id == "rv_073"


def test_two_simultaneous_submissions_create_only_one(ae, svc):
    # Se alarga la lectura para que la carrera «comprobar y luego guardar» ocurra de verdad sin candado.
    original_list = svc._reviews.list

    def slow_list():
        items = original_list()
        time.sleep(0.003)
        return items

    svc._reviews.list = slow_list

    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    outcomes = []

    def submit():
        try:
            svc.create(ana, "barato", data())
            outcomes.append("ok")
        except ReviewError as error:
            outcomes.append(error.code)

    threads = [threading.Thread(target=submit) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert outcomes.count("ok") == 1 and outcomes.count("already_reviewed") == 7
    assert len([r for r in svc._reviews.list() if r.user_id == ana.id]) == 1


# -- validación --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("rating", [0, 6, -1, 100])
def test_rating_must_be_1_to_5(rating):
    with pytest.raises(ValidationError):
        ReviewIn(rating=rating, comment=GOOD_COMMENT)


@pytest.mark.parametrize("comment", ["", "corto", "   dieciocho    ", "x" * 2001])
def test_comment_must_have_10_to_2000_characters_after_trimming(comment):
    with pytest.raises(ValidationError):
        ReviewIn(rating=5, comment=comment)


def test_comment_is_trimmed_and_html_is_kept_as_text():
    parsed = ReviewIn(rating=5, comment="   <b>negrita</b> y <script>1</script>   ")
    assert parsed.comment == "<b>negrita</b> y <script>1</script>"  # se guarda tal cual: el frontend lo muestra como texto


# -- efecto en la nota y en la ficha -------------------------------------------------------------------------


def test_a_new_review_changes_the_public_average_and_is_marked_verified(ae, svc):
    catalog = CatalogService(ae.env.books, ae.authors, ae.categories, svc._reviews)
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    assert catalog.get_book("barato").rating_count == 0
    svc.create(ana, "barato", data(4))
    book = catalog.get_book("barato")
    assert (book.rating_avg, book.rating_count) == (4.0, 1)
    listed = catalog.book_reviews("barato")
    assert listed[0].verified is True and listed[0].is_demo is False


def test_sample_reviews_are_never_verified(ae, svc):
    svc._reviews.add(Review(id="rv_001", book_id="b1", user_id=None, author_name="Demo", rating=5, comment="Comentario de muestra", is_demo=True, created_at=NOW))
    catalog = CatalogService(ae.env.books, ae.authors, ae.categories, svc._reviews)
    only = catalog.book_reviews("barato")[0]
    assert only.is_demo is True and only.verified is False


# -- moderación ----------------------------------------------------------------------------------------------


def test_admin_can_list_and_remove_any_review_including_samples(ae, svc):
    ana = ae.env.new_user()
    buy(ae, ana, [("b1", 1)])
    svc._reviews.add(Review(id="rv_001", book_id="b1", user_id=None, author_name="Demo", rating=5, comment="Comentario de muestra", is_demo=True, created_at=NOW))
    real = svc.create(ana, "barato", data())
    assert {r.id for r in svc.admin_list("b1")} == {"rv_001", real.id}
    svc.admin_delete("rv_001")
    svc.admin_delete(real.id)
    assert svc.admin_list("b1") == []
    assert svc.status(ana, "barato")[0] is True  # tras moderar, puede volver a escribir
    with pytest.raises(ReviewError) as error:
        svc.admin_delete("rv_001")
    assert error.value.code == "not_found"


# ======================================= API =====================================================================


@pytest.fixture
def api(ae, svc):
    app.dependency_overrides[get_auth_service] = lambda: ae.env.auth
    app.dependency_overrides[get_admin_service] = lambda: ae.admin
    app.dependency_overrides[get_order_service] = lambda: ae.env.service
    app.dependency_overrides[get_catalog_service] = lambda: CatalogService(ae.env.books, ae.authors, ae.categories, svc._reviews)
    app.dependency_overrides[get_review_service] = lambda: svc
    yield TestClient(app)
    app.dependency_overrides.clear()


def headers(ae, email, role="customer"):
    from app.schemas.auth import AddressIn, RegisterIn

    user = ae.env.auth.register(RegisterIn(first_name="Ana", last_name="Pérez", email=email, address=AddressIn(line="Calle 1 # 2-3", city="Cali"), password="clave-segura-1"), role=role)
    return user, {"Authorization": f"Bearer {ae.env.auth.create_token(user)}"}


URL = "/api/v1/books/barato/reviews"
BODY = {"rating": 5, "comment": GOOD_COMMENT}


@pytest.mark.parametrize("method, path", [("get", f"{URL}/mine"), ("post", URL), ("put", f"{URL}/mine"), ("delete", f"{URL}/mine")])
def test_review_writes_require_a_session(api, method, path):
    kwargs = {"json": BODY} if method in ("post", "put") else {}
    assert getattr(api, method)(path, **kwargs).status_code == 401


def test_public_review_listing_stays_public(api):
    assert api.get(URL).status_code == 200


def test_full_review_flow_through_the_api(api, ae):
    user, h = headers(ae, "ana@correo.com")
    assert api.get(f"{URL}/mine", headers=h).json() == {"can_review": False, "has_purchased": False, "review": None}
    assert api.post(URL, json=BODY, headers=h).status_code == 403  # aún no compró

    buy(ae, user, [("b1", 1)])
    assert api.get(f"{URL}/mine", headers=h).json()["can_review"] is True
    created = api.post(URL, json=BODY, headers=h)
    assert created.status_code == 201
    body = created.json()
    assert body["verified"] is True and body["is_demo"] is False and body["author_name"] == "Ana P." and "user_id" not in body

    assert api.post(URL, json=BODY, headers=h).status_code == 409
    mine = api.get(f"{URL}/mine", headers=h).json()
    assert mine["can_review"] is False and mine["has_purchased"] is True and mine["review"]["id"] == body["id"]

    edited = api.put(f"{URL}/mine", json={"rating": 2, "comment": "Cambié de opinión con el tiempo."}, headers=h)
    assert edited.status_code == 200 and edited.json()["rating"] == 2 and edited.json()["updated_at"]
    assert api.get("/api/v1/books/barato").json()["rating_avg"] == 2.0

    assert api.delete(f"{URL}/mine", headers=h).status_code == 204
    assert api.get(f"{URL}/mine", headers=h).json()["can_review"] is True
    assert api.get(URL).json() == []


def test_error_codes_are_stable(api, ae):
    user, h = headers(ae, "ana@correo.com")
    assert api.post(URL, json=BODY, headers=h).json()["detail"]["code"] == "not_eligible"
    assert api.put(f"{URL}/mine", json=BODY, headers=h).json()["detail"]["code"] == "not_found"
    assert api.delete(f"{URL}/mine", headers=h).status_code == 404
    assert api.post("/api/v1/books/no-existe/reviews", json=BODY, headers=h).status_code == 404


@pytest.mark.parametrize("body", [{}, {"rating": 0, "comment": GOOD_COMMENT}, {"rating": 6, "comment": GOOD_COMMENT}, {"rating": 5, "comment": "corto"}, {"rating": 5, "comment": "x" * 2001}, {"rating": "cinco", "comment": GOOD_COMMENT}])
def test_invalid_review_payloads_are_422(api, ae, body):
    user, h = headers(ae, "ana@correo.com")
    buy(ae, user, [("b1", 1)])
    assert api.post(URL, json=body, headers=h).status_code == 422


def test_a_client_cannot_forge_who_wrote_it_or_that_it_is_a_sample(api, ae):
    user, h = headers(ae, "ana@correo.com")
    buy(ae, user, [("b1", 1)])
    body = api.post(URL, json={**BODY, "user_id": "usr_otro", "author_name": "Otra Persona", "is_demo": True, "id": "rv_999"}, headers=h).json()
    assert body["author_name"] == "Ana P." and body["is_demo"] is False and body["id"] != "rv_999"


def test_admin_moderation_is_admin_only_and_removes_reviews(api, ae):
    user, h = headers(ae, "ana@correo.com")
    buy(ae, user, [("b1", 1)])
    review_id = api.post(URL, json=BODY, headers=h).json()["id"]
    _, admin = headers(ae, "admin@correo.com", "admin")

    for method, path in (("get", "/api/v1/admin/books/b1/reviews"), ("delete", f"/api/v1/admin/reviews/{review_id}")):
        assert getattr(api, method)(path).status_code == 401
        assert getattr(api, method)(path, headers=h).status_code == 403  # ni siquiera su propia reseña, por esta vía

    listed = api.get("/api/v1/admin/books/b1/reviews", headers=admin).json()
    assert [r["id"] for r in listed] == [review_id]
    assert api.delete(f"/api/v1/admin/reviews/{review_id}", headers=admin).status_code == 204
    assert api.delete(f"/api/v1/admin/reviews/{review_id}", headers=admin).status_code == 404
    assert api.get(URL).json() == []

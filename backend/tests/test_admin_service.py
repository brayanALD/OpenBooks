import threading
import time

import pytest

from app.schemas.admin import BookUpdateIn
from app.schemas.cart import CartItemIn
from app.services.admin_service import AdminError
from app.services.catalog_service import BookQuery
from app.services.order_service import CheckoutError
from tests.admin_env import build_admin_env, new_book
from tests.order_env import DECLINED_CARD, checkout_data


@pytest.fixture
def ae():
    return build_admin_env()


def titles(ae):
    return [b.title for b in ae.catalog.list_books(BookQuery(page_size=48)).items]


# -- crear ----------------------------------------------------------------------------------------------


def test_create_book_generates_id_slug_and_defaults(ae):
    book = ae.admin.create_book(new_book())
    assert book.id == "bk_001" and book.slug == "un-libro-nuevo"  # los libros de prueba (b1…b4) no siguen el formato bk_NNN
    assert ae.admin.create_book(new_book(title="Otro")).id == "bk_002"
    assert (book.active, book.featured, book.bestseller, book.discount_pct, book.shipping_cost_cop) == (True, False, False, 0, 0)
    assert book.cover == "/covers/sin-portada.webp" and book.incomplete is False


def test_slug_is_unique_and_strips_accents(ae):
    a = ae.admin.create_book(new_book(title="Cien años de soledad"))
    b = ae.admin.create_book(new_book(title="Cien años de soledad"))
    c = ae.admin.create_book(new_book(title="Cien años de soledad"))
    assert (a.slug, b.slug, c.slug) == ("cien-anos-de-soledad", "cien-anos-de-soledad-2", "cien-anos-de-soledad-3")


def test_existing_author_is_reused_ignoring_case_and_accents(ae):
    ae.authors.add(type(ae.authors.get("a1"))(id="a2", name="Gabriel García Márquez", slug="gabriel-garcia-marquez"))
    book = ae.admin.create_book(new_book(author_name="gabriel garcia marquez"))
    assert book.author_id == "a2" and len(ae.authors.list()) == 2


def test_new_author_is_created_with_a_unique_slug(ae):
    first = ae.admin.create_book(new_book(author_name="Ana Nueva"))
    second = ae.admin.create_book(new_book(author_name="Ana  Nueva "))  # mismo autor con espacios de más
    assert first.author_id == second.author_id
    author = ae.authors.get(first.author_id)
    assert (author.id, author.slug, author.name) == ("aut_001", "ana-nueva", "Ana Nueva")  # a1 no cuenta: otro formato de id
    assert len(ae.authors.list()) == 2


def test_unknown_category_is_rejected_and_nothing_is_saved(ae):
    with pytest.raises(AdminError) as error:
        ae.admin.create_book(new_book(category_ids=["c1", "c99"]))
    assert error.value.code == "invalid_category" and len(ae.env.books.list()) == 4


def test_incomplete_flag_reflects_missing_details(ae):
    assert ae.admin.create_book(new_book(publisher=None)).incomplete is True
    assert ae.admin.create_book(new_book(pages=None)).incomplete is True
    assert ae.admin.create_book(new_book(description="")).incomplete is True
    assert ae.admin.create_book(new_book()).incomplete is False


def test_new_book_shows_up_in_the_public_catalog(ae):
    ae.admin.create_book(new_book(title="Aparece en la tienda"))
    assert "Aparece en la tienda" in titles(ae)
    assert ae.catalog.get_book("aparece-en-la-tienda") is not None


# -- editar --------------------------------------------------------------------------------------------


def test_update_changes_only_what_is_sent(ae):
    before = ae.env.books.get("b1")
    updated = ae.admin.update_book("b1", BookUpdateIn(price_cop=12_345, stock=7))
    assert (updated.price_cop, updated.stock) == (12_345, 7)
    assert (updated.title, updated.discount_pct, updated.shipping_cost_cop, updated.cover) == (before.title, before.discount_pct, before.shipping_cost_cop, before.cover)


def test_editing_the_title_keeps_the_slug(ae):
    book = ae.admin.create_book(new_book(title="Título viejo"))
    updated = ae.admin.update_book(book.id, BookUpdateIn(title="Título nuevo"))
    assert updated.title == "Título nuevo" and updated.slug == "titulo-viejo"


def test_changing_the_author_reuses_or_creates(ae):
    updated = ae.admin.update_book("b1", BookUpdateIn(author_name="Otra Persona"))
    assert updated.author_id != "a1" and ae.authors.get(updated.author_id).name == "Otra Persona"
    assert ae.admin.update_book("b2", BookUpdateIn(author_name="AUTORA UNO")).author_id == "a1"


def test_optional_fields_can_be_cleared_but_required_ones_ignore_null(ae):
    book = ae.admin.create_book(new_book())
    cleared = ae.admin.update_book(book.id, BookUpdateIn(publisher=None))
    assert cleared.publisher is None and cleared.incomplete is True
    kept = ae.admin.update_book(book.id, BookUpdateIn(title=None, price_cop=None))
    assert kept.title == "Un libro nuevo" and kept.price_cop == 25_000


def test_update_validates_categories_and_existence(ae):
    with pytest.raises(AdminError) as bad_category:
        ae.admin.update_book("b1", BookUpdateIn(category_ids=["nope"]))
    assert bad_category.value.code == "invalid_category"
    with pytest.raises(AdminError) as missing:
        ae.admin.update_book("fantasma", BookUpdateIn(stock=1))
    assert missing.value.code == "not_found"


def test_price_and_discount_changes_reach_the_public_price(ae):
    ae.admin.update_book("b1", BookUpdateIn(price_cop=100_000, discount_pct=10))
    assert ae.catalog.get_book("barato").final_price_cop == 90_000


# -- ocultar -------------------------------------------------------------------------------------------


def test_hidden_book_disappears_everywhere_in_the_store(ae):
    ae.admin.update_book("b1", BookUpdateIn(active=False))
    assert "Barato" not in titles(ae)
    assert ae.catalog.get_book("barato") is None
    assert ae.catalog.related_books("barato") is None and ae.catalog.book_reviews("barato") is None
    assert ae.catalog.list_categories()[0].book_count == 3  # Novela: antes 4, ahora sin el oculto
    assert "Barato" not in [b.title for b in ae.catalog.related_books("con-descuento")]


def test_hidden_book_stays_in_the_admin_and_can_be_reactivated(ae):
    ae.admin.update_book("b1", BookUpdateIn(active=False))
    books, total, _ = ae.admin.list_books()
    assert total == 4 and "Barato" in [b.title for b in books]
    ae.admin.update_book("b1", BookUpdateIn(active=True))
    assert "Barato" in titles(ae)


def test_hidden_book_is_unavailable_in_the_cart_and_cannot_be_bought(ae):
    ae.admin.update_book("b1", BookUpdateIn(active=False))
    validation = ae.env.service._cart.validate([CartItemIn(book_id="b1", quantity=1)])
    assert validation.unavailable_ids == ["b1"] and validation.lines == []
    ana = ae.env.new_user()
    with pytest.raises(CheckoutError) as error:
        ae.env.service.checkout(ana, checkout_data([("b1", 1)], total=0))
    assert error.value.code == "cart_issues" and ae.env.stock("b1") == 20


def test_hiding_a_book_does_not_break_old_orders(ae):
    ana = ae.env.new_user()
    order, _ = ae.env.service.checkout(ana, checkout_data([("b1", 2)]))
    ae.admin.update_book("b1", BookUpdateIn(active=False))
    stored = ae.env.service.get_for_user(order.id, ana.id)
    assert stored.items[0].title == "Barato" and stored.status == "paid"


# -- listado de administración ---------------------------------------------------------------------------


def test_admin_list_filters_and_search(ae):
    ae.admin.update_book("b2", BookUpdateIn(active=False))
    ae.admin.update_book("b1", BookUpdateIn(stock=3))
    names = lambda **kw: [b.title for b in ae.admin.list_books(**kw)[0]]  # noqa: E731
    assert names(active=False) == ["Con descuento"]
    assert set(names(active=True)) == {"Barato", "Ultima unidad", "Agotado"}
    assert set(names(low_stock=True)) == {"Barato", "Ultima unidad", "Agotado"}  # stock ≤ 5 y activos
    assert names(q="ULTIMA") == ["Ultima unidad"]  # sin distinguir mayúsculas
    assert names(q="autora uno")  # también busca por autor


def test_admin_list_is_sorted_and_paginated(ae):
    first, total, _ = ae.admin.list_books(page=1, page_size=3)
    second, _, _ = ae.admin.list_books(page=2, page_size=3)
    assert total == 4 and len(first) == 3 and len(second) == 1
    assert [b.title for b in first + second] == sorted(b.title for b in first + second)


def test_admin_list_can_sort_by_stock(ae):
    # b1 Barato=20, b2 Con descuento=20, b3 Ultima unidad=1, b4 Agotado=0 (empates: por título).
    names = lambda **kw: [b.title for b in ae.admin.list_books(**kw)[0]]  # noqa: E731
    assert names(sort="stock_asc") == ["Agotado", "Ultima unidad", "Barato", "Con descuento"]
    assert names(sort="stock_desc") == ["Barato", "Con descuento", "Ultima unidad", "Agotado"]
    assert names(sort="lo-que-sea")[0] == "Agotado"  # cualquier valor desconocido cae al orden por título


# -- pedidos -------------------------------------------------------------------------------------------


@pytest.fixture
def paid(ae):
    ana = ae.env.new_user("ana@correo.com")
    order, _ = ae.env.service.checkout(ana, checkout_data([("b1", 3), ("b3", 1)]))
    return ae, ana, order


def test_order_lifecycle_paid_shipped_delivered(paid):
    ae, _, order = paid
    assert ae.admin.change_order_status(order.id, "shipped").status == "shipped"
    assert ae.admin.change_order_status(order.id, "delivered").status == "delivered"


@pytest.mark.parametrize(
    "path, bad",
    [
        (["shipped"], "cancelled"),  # ya enviado: no se cancela
        (["shipped", "delivered"], "cancelled"),
        (["shipped", "delivered"], "shipped"),  # entregado es final
        ([], "delivered"),  # no se salta el envío
        (["cancelled"], "shipped"),
        (["cancelled"], "cancelled"),
    ],
)
def test_invalid_transitions_are_rejected(paid, path, bad):
    ae, _, order = paid
    for step in path:
        ae.admin.change_order_status(order.id, step)
    with pytest.raises(AdminError) as error:
        ae.admin.change_order_status(order.id, bad)
    assert error.value.code == "invalid_transition"


def test_cancelling_returns_the_stock_exactly_once(paid):
    ae, _, order = paid
    assert (ae.env.stock("b1"), ae.env.stock("b3")) == (17, 0)
    ae.admin.change_order_status(order.id, "cancelled")
    assert (ae.env.stock("b1"), ae.env.stock("b3")) == (20, 1)
    with pytest.raises(AdminError):
        ae.admin.change_order_status(order.id, "cancelled")  # segunda vez: no devuelve otra vez
    assert (ae.env.stock("b1"), ae.env.stock("b3")) == (20, 1)


def test_cancelled_units_can_be_bought_again(paid):
    ae, _, order = paid
    ae.admin.change_order_status(order.id, "cancelled")
    luis = ae.env.new_user("luis@correo.com")
    again, _ = ae.env.service.checkout(luis, checkout_data([("b3", 1)], key="clave-de-luis-01"))
    assert again.status == "paid"


def test_failed_and_pending_orders_cannot_be_changed(ae):
    ana = ae.env.new_user()
    failed, _ = ae.env.service.checkout(ana, checkout_data([("b1", 1)], card=DECLINED_CARD))
    for target in ("shipped", "delivered", "cancelled"):
        with pytest.raises(AdminError):
            ae.admin.change_order_status(failed.id, target)
    assert ae.env.stock("b1") == 20  # y no se "devolvió" nada por error


def test_unknown_order(ae):
    with pytest.raises(AdminError) as error:
        ae.admin.change_order_status("ord_999999", "shipped")
    assert error.value.code == "not_found" and ae.admin.get_order("ord_999999") is None


def test_order_listing_with_customer_filters_and_order(ae):
    ana, luis = ae.env.new_user("ana@correo.com"), ae.env.new_user("luis@correo.com")
    ae.env.service.checkout(ana, checkout_data([("b1", 1)], key="clave-de-ana-001"))
    ae.env.service.checkout(luis, checkout_data([("b1", 1)], key="clave-de-luis-01", card=DECLINED_CARD))
    ae.env.service.checkout(ana, checkout_data([("b1", 1)], key="clave-de-ana-002"))

    rows, total = ae.admin.list_orders()
    assert total == 3 and [o.number for o, _ in rows] == ["OB-000003", "OB-000002", "OB-000001"]
    assert rows[0][1].email == "ana@correo.com"
    assert [o.number for o, _ in ae.admin.list_orders(status="failed")[0]] == ["OB-000002"]
    assert {o.number for o, _ in ae.admin.list_orders(q="LUIS@")[0]} == {"OB-000002"}
    assert [o.number for o, _ in ae.admin.list_orders(q="ob-000001")[0]] == ["OB-000001"]
    assert len(ae.admin.list_orders(page=1, page_size=2)[0]) == 2 and ae.admin.list_orders(page=2, page_size=2)[1] == 3


def test_summary_numbers(paid):
    ae, _, order = paid
    summary = ae.admin.summary()
    # Tras la compra: Barato 17, Con descuento 20, Ultima unidad 0 y Agotado 0.
    assert summary["books"] == {"total": 4, "active": 4, "hidden": 0, "out_of_stock": 2, "low_stock": 0}
    assert summary["orders"]["by_status"] == {"paid": 1}
    assert summary["orders"]["revenue_cop"] == order.total_cop
    ae.admin.change_order_status(order.id, "cancelled")
    assert ae.admin.summary()["orders"]["revenue_cop"] == 0  # lo cancelado no cuenta como ingreso


# -- concurrencia: el panel y las compras comparten candado --------------------------------------------------


def test_admin_edits_never_lose_stock_from_concurrent_sales(ae):
    # En memoria la ventana entre "leer el libro" y "guardarlo" es de microsegundos y la carrera casi nunca ocurre.
    # Con el disco real es mucho mayor: se simula alargándola, para que el test FALLE si falta el candado compartido.
    original_get = ae.env.books.get

    def slow_get(book_id):
        book = original_get(book_id)
        time.sleep(0.002)
        return book

    ae.env.books.get = slow_get

    buyers = [ae.env.new_user(f"u{i}@correo.com") for i in range(12)]
    results = []

    def buy(user, i):
        try:
            price = ae.env.books.get("b1").price_cop  # el precio cambia mientras se compra: algunas compras darán 409
            order, _ = ae.env.service.checkout(user, checkout_data([("b1", 1)], key=f"clave-comprador-{i}", total=price))
            results.append(order.status)
        except CheckoutError:
            results.append("rechazada")

    def edit_price():
        for n in range(40):
            ae.admin.update_book("b1", BookUpdateIn(price_cop=10_000 + (n % 2)))

    threads = [threading.Thread(target=buy, args=(u, i)) for i, u in enumerate(buyers)] + [threading.Thread(target=edit_price)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    paid_orders = results.count("paid")
    assert ae.env.stock("b1") == 20 - paid_orders, "una edición del administrador pisó el stock de una venta"
    assert ae.env.stock("b1") >= 0

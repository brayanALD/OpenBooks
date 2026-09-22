import threading

import pytest

from app.services.order_service import PAYMENT_ERROR, CheckoutError
from tests.order_env import (
    DECLINED_CARD,
    NO_FUNDS_CARD,
    CountingProvider,
    build_env,
    checkout_data,
)


@pytest.fixture
def env():
    return build_env()


@pytest.fixture
def ana(env):
    return env.new_user("ana@correo.com")


# -- compra correcta ---------------------------------------------------------------------------------------


def test_paid_order_snapshot_totals_and_stock(env, ana):
    order, created = env.service.checkout(ana, checkout_data([("b1", 2), ("b2", 1)]))
    assert created and order.status == "paid" and order.number == "OB-000001"
    assert [(i.book_id, i.quantity, i.unit_price_cop, i.line_total_cop) for i in order.items] == [
        ("b1", 2, 10_000, 20_000),
        ("b2", 1, 80_000, 80_000),  # 100.000 con 20 %
    ]
    assert (order.subtotal_cop, order.shipping_cop, order.total_cop) == (100_000, 5_000, 105_000)
    assert order.payment.status == "approved" and order.payment.method == "Visa •••• 4242"
    assert (env.stock("b1"), env.stock("b2")) == (18, 19)
    assert env.provider.charges == [(105_000, "OB-000001")]


def test_order_keeps_the_shipping_of_this_order_not_the_account(env, ana):
    order, _ = env.service.checkout(ana, checkout_data([("b1", 1)]))
    assert (order.shipping.recipient_name, order.shipping.phone, order.shipping.notes) == ("Ana Pérez", "3001234567", "Torre 2")


def test_saved_cart_is_emptied_only_after_a_successful_payment(env, ana):
    env.storage.replace(ana.id, [("b1", 2)])
    env.service.checkout(ana, checkout_data([("b1", 2)], card=DECLINED_CARD, key="clave-unica-0001"))
    assert [(i.book_id, i.quantity) for i in env.storage.get(ana.id)] == [("b1", 2)]  # intacto tras el rechazo
    env.service.checkout(ana, checkout_data([("b1", 2)], key="clave-unica-0002"))
    assert env.storage.get(ana.id) == []


def test_order_numbers_are_sequential(env, ana):
    numbers = [env.service.checkout(ana, checkout_data([("b1", 1)], key=f"clave-unica-000{i}"))[0].number for i in range(1, 4)]
    assert numbers == ["OB-000001", "OB-000002", "OB-000003"]


def test_the_order_does_not_change_when_the_catalog_does(env, ana):
    order, _ = env.service.checkout(ana, checkout_data([("b1", 1)]))
    book = env.books.get("b1")
    env.books.update(book.model_copy(update={"price_cop": 99_999, "title": "Otro título"}))
    stored = env.service.get_for_user(order.id, ana.id)
    assert stored.items[0].unit_price_cop == 10_000 and stored.items[0].title == "Barato"


def test_no_card_data_is_stored_in_the_order(env, ana):
    order, _ = env.service.checkout(ana, checkout_data([("b1", 1)]))
    dump = order.model_dump_json()
    assert "4242424242424242" not in dump and "4242 4242" not in dump and '"cvc"' not in dump and "ANA PEREZ" not in dump


# -- pago rechazado -----------------------------------------------------------------------------------------


def test_declined_payment_saves_a_failed_order_and_restores_stock(env, ana):
    order, created = env.service.checkout(ana, checkout_data([("b1", 3)], card=NO_FUNDS_CARD))
    assert created and order.status == "failed" and order.payment.status == "declined"
    assert "Fondos insuficientes" in order.payment.failure_reason and order.payment.method == "Visa •••• 9995"
    assert env.stock("b1") == 20  # devuelto
    assert [o.status for o in env.service.list_for_user(ana.id)] == ["failed"]  # queda en el historial


def test_retry_after_a_decline_creates_a_new_order_and_can_succeed(env, ana):
    failed, _ = env.service.checkout(ana, checkout_data([("b1", 1)], card=DECLINED_CARD, key="intento-numero-1"))
    paid, _ = env.service.checkout(ana, checkout_data([("b1", 1)], key="intento-numero-2"))
    assert (failed.status, paid.status) == ("failed", "paid") and failed.id != paid.id
    assert env.stock("b1") == 19  # solo el pagado descuenta


def test_gateway_crash_counts_as_failed_and_restores_stock(env, ana):
    env.provider.fail_with = RuntimeError("pasarela caída")
    order, _ = env.service.checkout(ana, checkout_data([("b1", 2)]))
    assert order.status == "failed" and order.payment.failure_reason == PAYMENT_ERROR
    assert env.stock("b1") == 20


# -- idempotencia -------------------------------------------------------------------------------------------


def test_same_key_returns_the_same_order_and_charges_once(env, ana):
    data = checkout_data([("b1", 2)])
    first, created_first = env.service.checkout(ana, data)
    again, created_again = env.service.checkout(ana, data)
    assert (created_first, created_again) == (True, False) and again.id == first.id
    assert len(env.provider.charges) == 1 and env.stock("b1") == 18 and len(env.orders.list()) == 1


def test_the_same_key_from_two_users_are_different_orders(env):
    a, b = env.new_user("a@correo.com"), env.new_user("b@correo.com")
    oa, _ = env.service.checkout(a, checkout_data([("b1", 1)], key="misma-clave-0001"))
    ob, _ = env.service.checkout(b, checkout_data([("b1", 1)], key="misma-clave-0001"))
    assert oa.id != ob.id


def test_double_submission_while_charging_does_not_charge_twice():
    provider = CountingProvider(delay=0.4)
    env = build_env(provider)
    ana = env.new_user()
    data = checkout_data([("b1", 2)])
    results = []
    threads = [threading.Thread(target=lambda: results.append(env.service.checkout(ana, data))) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(provider.charges) == 1
    assert len({order.id for order, _ in results}) == 1 and sorted(created for _, created in results) == [False, False, True]
    assert env.stock("b1") == 18


# -- validaciones de negocio ---------------------------------------------------------------------------------


def test_changed_total_is_rejected_before_reserving_anything(env, ana):
    with pytest.raises(CheckoutError) as error:
        env.service.checkout(ana, checkout_data([("b1", 1)], total=1))
    assert error.value.code == "total_changed"
    assert env.stock("b1") == 20 and env.orders.list() == [] and env.provider.charges == []


@pytest.mark.parametrize("items", [[("b4", 1)], [("b3", 2)], [("fantasma", 1)], [("b1", 99)]])
def test_unavailable_quantities_are_rejected(env, ana, items):
    with pytest.raises(CheckoutError) as error:
        env.service.checkout(ana, checkout_data([("b1", 1)] if False else items, total=0))
    assert error.value.code == "cart_issues" and env.orders.list() == [] and env.provider.charges == []


def test_rejection_leaves_stock_untouched_even_if_only_one_line_is_bad(env, ana):
    with pytest.raises(CheckoutError):
        env.service.checkout(ana, checkout_data([("b1", 2), ("b4", 1)], total=0))
    assert env.stock("b1") == 20


# -- concurrencia --------------------------------------------------------------------------------------------


def test_the_last_unit_is_sold_exactly_once():
    env = build_env(CountingProvider(delay=0.05))
    buyers = [env.new_user(f"u{i}@correo.com") for i in range(8)]
    outcomes = []

    def buy(user, i):
        try:
            order, _ = env.service.checkout(user, checkout_data([("b3", 1)], key=f"clave-comprador-{i}"))
            outcomes.append(order.status)
        except CheckoutError as error:
            outcomes.append(error.code)

    threads = [threading.Thread(target=buy, args=(u, i)) for i, u in enumerate(buyers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert outcomes.count("paid") == 1 and outcomes.count("cart_issues") == 7
    assert env.stock("b3") == 0  # nunca negativo
    assert len(env.provider.charges) == 1


def test_a_declined_payment_frees_the_reserved_unit_for_the_next_buyer(env):
    a, b = env.new_user("a@correo.com"), env.new_user("b@correo.com")
    failed, _ = env.service.checkout(a, checkout_data([("b3", 1)], card=DECLINED_CARD, key="clave-comprador-a"))
    paid, _ = env.service.checkout(b, checkout_data([("b3", 1)], key="clave-comprador-b"))
    assert (failed.status, paid.status) == ("failed", "paid") and env.stock("b3") == 0


# -- consulta ------------------------------------------------------------------------------------------------


def test_users_only_see_their_own_orders(env):
    a, b = env.new_user("a@correo.com"), env.new_user("b@correo.com")
    order, _ = env.service.checkout(a, checkout_data([("b1", 1)]))
    assert env.service.get_for_user(order.id, a.id) is not None
    assert env.service.get_for_user(order.id, b.id) is None
    assert env.service.list_for_user(b.id) == []


def test_orders_are_listed_newest_first(env, ana):
    for i in range(1, 4):
        env.service.checkout(ana, checkout_data([("b1", 1)], key=f"clave-unica-000{i}"))
    assert [o.number for o in env.service.list_for_user(ana.id)] == ["OB-000003", "OB-000002", "OB-000001"]

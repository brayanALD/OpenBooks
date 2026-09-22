import pytest

from app.domain.models import Author, Category
from app.repositories.memory_repo import InMemoryRepository
from app.schemas.cart import CartIssue, CartItemIn
from app.services.cart_service import CartService, shipping_for
from app.services.catalog_service import CatalogService
from tests.conftest import make_book


def items(*pairs: tuple[str, int]) -> list[CartItemIn]:
    return [CartItemIn(book_id=b, quantity=q) for b, q in pairs]


@pytest.fixture
def cart() -> CartService:
    authors = [Author(id="a1", name="Autora Uno", slug="autora-uno")]
    categories = [Category(id="c1", name="Novela", slug="novela")]
    books = [
        make_book("b1", "Barato", "a1", ["c1"], price_cop=10_000, stock=20),  # envío gratis
        make_book("b2", "Con descuento", "a1", ["c1"], price_cop=100_000, discount_pct=20, shipping_cost_cop=5_000, stock=20),
        make_book("b3", "Poco stock", "a1", ["c1"], price_cop=30_000, stock=3, shipping_cost_cop=8_000),
        make_book("b4", "Agotado", "a1", ["c1"], price_cop=50_000, stock=0),
    ]
    catalog = CatalogService(
        InMemoryRepository(books), InMemoryRepository(authors), InMemoryRepository(categories), InMemoryRepository([])
    )
    return CartService(catalog)


def test_empty_cart(cart):
    out = cart.validate([])
    assert (out.lines, out.item_count, out.subtotal_cop, out.shipping_cop, out.total_cop) == ([], 0, 0, 0, 0)
    assert out.has_issues is False


def test_totals_use_server_prices_with_discount(cart):
    out = cart.validate(items(("b1", 2), ("b2", 1)))
    assert [l.unit_price_cop for l in out.lines] == [10_000, 80_000]  # b2: 100.000 con 20 %
    assert [l.line_total_cop for l in out.lines] == [20_000, 80_000]
    assert (out.subtotal_cop, out.shipping_cop, out.total_cop, out.item_count) == (100_000, 5_000, 105_000, 3)
    assert out.has_issues is False


def test_free_shipping_when_every_book_ships_free(cart):
    assert cart.validate(items(("b1", 1))).shipping_cop == 0


def test_shipping_is_the_highest_cost_not_the_sum(cart):
    out = cart.validate(items(("b2", 1), ("b3", 1)))  # 5.000 y 8.000
    assert out.shipping_cop == 8_000


def test_shipping_ignores_lines_that_are_not_bought(cart):
    assert cart.validate(items(("b1", 1), ("b4", 1))).shipping_cop == 0


def test_shipping_for_helper():
    assert shipping_for([]) == 0
    assert shipping_for([0, 5_000, 3_000]) == 5_000


def test_repeated_lines_are_merged_in_order(cart):
    out = cart.validate(items(("b2", 1), ("b1", 1), ("b2", 2)))
    assert [(l.book.id, l.requested_quantity) for l in out.lines] == [("b2", 3), ("b1", 1)]


def test_quantity_is_capped_at_ten_per_book(cart):
    line = cart.validate(items(("b1", 25))).lines[0]
    assert (line.requested_quantity, line.quantity, line.max_quantity) == (25, 10, 10)
    assert line.issue is CartIssue.quantity_capped


def test_limited_stock_reduces_the_quantity(cart):
    out = cart.validate(items(("b3", 5)))
    line = out.lines[0]
    assert (line.quantity, line.max_quantity, line.issue) == (3, 3, CartIssue.limited_stock)
    assert out.subtotal_cop == 90_000 and out.has_issues


def test_enough_stock_has_no_issue(cart):
    line = cart.validate(items(("b3", 3))).lines[0]
    assert line.issue is None and line.quantity == 3


def test_out_of_stock_is_listed_but_excluded_from_totals(cart):
    out = cart.validate(items(("b4", 2), ("b1", 1)))
    sold_out = next(l for l in out.lines if l.book.id == "b4")
    assert (sold_out.quantity, sold_out.line_total_cop, sold_out.issue) == (0, 0, CartIssue.out_of_stock)
    assert (out.subtotal_cop, out.item_count) == (10_000, 1)
    assert out.has_issues


def test_unknown_book_is_reported_not_priced(cart):
    out = cart.validate(items(("b1", 1), ("fantasma", 2)))
    assert out.unavailable_ids == ["fantasma"]
    assert [l.book.id for l in out.lines] == ["b1"]
    assert out.subtotal_cop == 10_000 and out.has_issues

import pytest

from app.domain.models import Author, Cart, Category
from app.repositories.memory_repo import InMemoryRepository
from app.services.cart_storage import CartStorage
from app.services.catalog_service import CatalogService
from tests.conftest import make_book


@pytest.fixture
def storage() -> CartStorage:
    catalog = CatalogService(
        InMemoryRepository([make_book(f"b{i}", f"Libro {i}", "a1", ["c1"]) for i in (1, 2, 3)]),
        InMemoryRepository([Author(id="a1", name="Autora", slug="autora")]),
        InMemoryRepository([Category(id="c1", name="Novela", slug="novela")]),
        InMemoryRepository([]),
    )
    return CartStorage(catalog, InMemoryRepository[Cart]([]))


def as_pairs(items):
    return [(i.book_id, i.quantity) for i in items]


def test_new_user_has_an_empty_cart(storage):
    assert storage.get("u1") == []


def test_replace_then_get(storage):
    storage.replace("u1", [("b1", 2), ("b2", 1)])
    assert as_pairs(storage.get("u1")) == [("b1", 2), ("b2", 1)]


def test_replace_overwrites_and_can_empty(storage):
    storage.replace("u1", [("b1", 2)])
    storage.replace("u1", [("b3", 1)])
    assert as_pairs(storage.get("u1")) == [("b3", 1)]
    storage.replace("u1", [])
    assert storage.get("u1") == []


def test_replace_drops_unknown_books_and_caps_quantity(storage):
    storage.replace("u1", [("fantasma", 3), ("b1", 99)])
    assert as_pairs(storage.get("u1")) == [("b1", 10)]


def test_replace_joins_repeated_lines(storage):
    storage.replace("u1", [("b1", 2), ("b2", 1), ("b1", 3)])
    assert as_pairs(storage.get("u1")) == [("b1", 5), ("b2", 1)]


def test_merge_into_an_empty_cart_keeps_the_guest_items(storage):
    assert as_pairs(storage.merge("u1", [("b1", 2)])) == [("b1", 2)]


def test_merge_sums_common_books_and_keeps_the_rest(storage):
    storage.replace("u1", [("b1", 2), ("b2", 1)])
    merged = storage.merge("u1", [("b1", 3), ("b3", 1)])
    assert as_pairs(merged) == [("b1", 5), ("b2", 1), ("b3", 1)]
    assert as_pairs(storage.get("u1")) == as_pairs(merged)  # queda guardado


def test_merge_caps_the_sum_at_ten(storage):
    storage.replace("u1", [("b1", 8)])
    assert as_pairs(storage.merge("u1", [("b1", 8)])) == [("b1", 10)]


def test_merge_ignores_unknown_books(storage):
    assert as_pairs(storage.merge("u1", [("fantasma", 1), ("b2", 1)])) == [("b2", 1)]


def test_carts_are_isolated_per_user(storage):
    storage.replace("u1", [("b1", 1)])
    storage.replace("u2", [("b2", 2)])
    assert as_pairs(storage.get("u1")) == [("b1", 1)]
    assert as_pairs(storage.get("u2")) == [("b2", 2)]


# -- libros que dejan de estar disponibles ---------------------------------------------------------


def test_books_that_stop_existing_are_reported_once_and_removed_for_good(storage):
    storage.replace("u1", [("b1", 2), ("b2", 1)])
    hidden = storage._catalog._books.get("b1")
    storage._catalog._books.update(hidden.model_copy(update={"active": False}))

    items, removed = storage.get_with_removed("u1")
    assert as_pairs(items) == [("b2", 1)] and removed == ["b1"]
    assert storage.get_with_removed("u1") == (items, [])  # el aviso se da una sola vez: la limpieza queda guardada
    assert as_pairs(storage.get("u1")) == [("b2", 1)]


def test_removed_is_empty_when_nothing_changed_and_for_new_users(storage):
    storage.replace("u1", [("b1", 1)])
    assert storage.get_with_removed("u1")[1] == [] and storage.get_with_removed("nadie") == ([], [])

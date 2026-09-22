from scripts.catalog_rules import (
    LONG_BOOK_SHIPPING_COP,
    ON_SALE_HIGH_PCT,
    ON_SALE_LOW_PCT,
    SHORT_BOOK_SHIPPING_COP,
    extra_flags,
    is_valid_isbn13,
    isbn_for,
    normalize_publisher,
    pick_discounts,
    shipping_for,
)


def test_shipping_is_free_above_the_threshold():
    assert shipping_for(70_001, 500) == 0
    assert shipping_for(1_000_000, None) == 0


def test_shipping_depends_on_pages_below_the_threshold():
    assert shipping_for(70_000, 150) == SHORT_BOOK_SHIPPING_COP  # justo en el límite: cuenta como "corto"
    assert shipping_for(70_000, 151) == LONG_BOOK_SHIPPING_COP
    assert shipping_for(10_000, None) == LONG_BOOK_SHIPPING_COP  # sin dato de páginas: no se regala envío


def test_isbn_is_deterministic_and_checksums_validate():
    a = isbn_for("un-libro", "Español")
    b = isbn_for("un-libro", "Español")
    assert a == b
    assert is_valid_isbn13(a)


def test_isbn_uses_an_english_prefix_for_english_books():
    assert isbn_for("some-book", "Inglés").startswith("978-0-")


def test_isbn_rejects_a_tampered_checksum():
    valid = isbn_for("otro-libro", None)
    tampered = valid[:-1] + ("0" if valid[-1] != "0" else "1")
    assert not is_valid_isbn13(tampered)


def test_extra_flags_are_deterministic():
    assert extra_flags("mismo-libro") == extra_flags("mismo-libro")


def test_normalize_publisher_fixes_shouting_and_all_lowercase():
    assert normalize_publisher("TALLER DEL EXITO") == "Taller del Exito"
    assert normalize_publisher("penguin clasicos") == "Penguin Clasicos"


def test_normalize_publisher_leaves_mixed_case_alone():
    assert normalize_publisher("Plaza & Janés") == "Plaza & Janés"
    assert normalize_publisher(None) is None


def test_pick_discounts_is_15_percent_split_evenly_between_10_and_15():
    slugs = [f"libro-{i}" for i in range(300)]  # 15 % de 300 = 45, exacto: no hay redondeo que desempatar
    chosen = pick_discounts(slugs)
    assert len(chosen) == 45
    assert set(chosen).issubset(set(slugs))
    assert list(chosen.values()).count(ON_SALE_LOW_PCT) == 22
    assert list(chosen.values()).count(ON_SALE_HIGH_PCT) == 23
    assert set(chosen.values()) == {ON_SALE_LOW_PCT, ON_SALE_HIGH_PCT}


def test_pick_discounts_is_deterministic():
    slugs = [f"libro-{i}" for i in range(120)]
    assert pick_discounts(slugs) == pick_discounts(slugs)

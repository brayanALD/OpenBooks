import pytest
from pydantic import ValidationError

from app.payments.base import CardDetails
from app.payments.mock_provider import MockPaymentProvider, brand_of
from app.schemas.orders import CardIn, luhn_valid


def card(number: str) -> CardDetails:
    return CardDetails(number=number, cvc="123", exp_month=12, exp_year=2035, holder="ANA PEREZ")


@pytest.mark.parametrize("number, brand", [("4242424242424242", "Visa"), ("5555555555554444", "Mastercard")])
def test_approved_test_cards(number, brand):
    result = MockPaymentProvider().charge(50_000, card(number), "OB-000001")
    assert result.approved and result.brand == brand and result.last4 == number[-4:]
    assert result.failure_reason is None and result.reference.startswith("mock_")


@pytest.mark.parametrize(
    "number, reason",
    [
        ("4000000000000002", "rechazada"),
        ("4000000000009995", "Fondos insuficientes"),
        ("4000000000000069", "vencida"),
        ("4000000000000127", "CVC"),
    ],
)
def test_declined_test_cards_explain_why(number, reason):
    result = MockPaymentProvider().charge(50_000, card(number), "OB-000001")
    assert not result.approved and reason in result.failure_reason


def test_unknown_but_valid_cards_are_declined_with_a_hint():
    result = MockPaymentProvider().charge(1, card("4111111111111111"), "OB-000001")
    assert not result.approved and "tarjetas de prueba" in result.failure_reason


def test_every_charge_gets_a_distinct_reference():
    provider = MockPaymentProvider()
    refs = {provider.charge(1, card("4242424242424242"), "x").reference for _ in range(20)}
    assert len(refs) == 20


def test_brand_detection():
    assert brand_of("4111111111111111") == "Visa"
    assert brand_of("5105105105105100") == "Mastercard"
    assert brand_of("378282246310005") == "Tarjeta"


def test_card_details_repr_hides_number_and_cvc():
    text = repr(card("4242424242424242"))
    assert "4242424242424242" not in text and "123" not in text


# -- CardIn (validación antes de cobrar) -----------------------------------------------------------------


def make(**overrides):
    data = dict(number="4242 4242 4242 4242", cvc="123", holder="Ana Pérez", exp_month=12, exp_year=2035)
    data.update(overrides)
    return CardIn(**data)


def test_luhn():
    assert luhn_valid("4242424242424242") and luhn_valid("5555555555554444")
    assert not luhn_valid("4242424242424241")


def test_number_is_cleaned_and_valid():
    assert make(number="4242-4242 4242-4242").number.get_secret_value() == "4242424242424242"


@pytest.mark.parametrize("number", ["4242424242424241", "1234", "abcd" * 4, "4242" * 6, ""])
def test_invalid_numbers_are_rejected(number):
    with pytest.raises(ValidationError):
        make(number=number)


@pytest.mark.parametrize("cvc", ["12", "12345", "abc", ""])
def test_invalid_cvc(cvc):
    with pytest.raises(ValidationError):
        make(cvc=cvc)


def test_expired_card_is_rejected_and_this_month_is_still_valid():
    from datetime import date

    today = date.today()
    with pytest.raises(ValidationError):
        make(exp_month=1, exp_year=2020)
    assert make(exp_month=today.month, exp_year=today.year)


def test_two_digit_year_is_normalized():
    assert make(exp_year=35).exp_year == 2035


@pytest.mark.parametrize("month", [0, 13])
def test_invalid_month(month):
    with pytest.raises(ValidationError):
        make(exp_month=month)


def test_secret_fields_are_masked_when_printed():
    text = repr(make()) + str(make().model_dump())
    assert "4242424242424242" not in text and "'123'" not in text

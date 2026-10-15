import pytest
from AI.stipend import extract_stipend_amount


def test_extract_stipend_with_currency_and_k():
    assert extract_stipend_amount("₹20k/mo") == 20000
    assert extract_stipend_amount("20K / month") == 20000
    assert extract_stipend_amount("Rs. 15k") == 15000
    assert extract_stipend_amount("INR 12.5k") == 12500


def test_extract_stipend_with_commas_and_symbols():
    assert extract_stipend_amount("₹15,000 per month") == 15000
    assert extract_stipend_amount("Rs 25,000 / mo") == 25000
    assert extract_stipend_amount("INR 10000") == 10000


def test_extract_stipend_plain_numbers():
    assert extract_stipend_amount("20000") == 20000
    assert extract_stipend_amount("8000") == 8000


def test_extract_stipend_reject_duration():
    # Durations like "3 months" or "6 months" must NOT be extracted as ₹3 or ₹6
    assert extract_stipend_amount("3 months") is None
    assert extract_stipend_amount("6 months duration") is None
    assert extract_stipend_amount("8 weeks") is None


def test_extract_stipend_unpaid_or_unknown():
    assert extract_stipend_amount("Unpaid") == 0
    assert extract_stipend_amount("Volunteer") == 0
    assert extract_stipend_amount("Not mentioned") is None
    assert extract_stipend_amount(None) is None
    assert extract_stipend_amount("") is None

"""Test suite for the demo repository.

One test in this file is deliberately weak: it calls a function but does not
verify its behavior, so it passes even when the underlying code is mutated.
This gives the test-honesty gate something real to catch.
"""

import pytest

from pricing import (
    apply_discount,
    get_display_name,
    is_eligible_for_free_shipping,
    is_valid_username,
    sum_first_n,
)


class TestApplyDiscount:
    def test_zero_discount_returns_original_price(self) -> None:
        assert apply_discount(100.0, 0.0) == 100.0

    def test_ten_percent_discount(self) -> None:
        assert apply_discount(100.0, 10.0) == pytest.approx(90.0)

    def test_negative_discount_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_discount(100.0, -1.0)

    def test_over_100_percent_discount_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_discount(100.0, 101.0)


class TestIsEligibleForFreeShipping:
    def test_weak_smoke_test(self) -> None:
        """Deliberately weak: calls the function but asserts nothing.

        This is the ONLY test covering ``is_eligible_for_free_shipping``,
        and it passes regardless of whether the equality check is correct.
        The ``== -> !=`` mutant therefore survives the suite.
        """
        is_eligible_for_free_shipping(50.0)


class TestSumFirstN:
    def test_sums_first_n_elements(self) -> None:
        assert sum_first_n([1, 2, 3, 4, 5], 3) == 6

    def test_n_zero_returns_zero(self) -> None:
        assert sum_first_n([1, 2, 3], 0) == 0

    def test_n_one_returns_first_element(self) -> None:
        assert sum_first_n([7, 8, 9], 1) == 7


class TestIsValidUsername:
    def test_valid_username(self) -> None:
        assert is_valid_username("alice") is True

    def test_empty_username_is_invalid(self) -> None:
        assert is_valid_username("") is False

    def test_too_long_username_is_invalid(self) -> None:
        assert is_valid_username("a" * 21) is False

    def test_exactly_20_chars_is_valid(self) -> None:
        assert is_valid_username("a" * 20) is True


class TestGetDisplayName:
    def test_none_returns_anonymous(self) -> None:
        assert get_display_name(None) == "anonymous"

    def test_user_with_name(self) -> None:
        assert get_display_name({"name": "bob"}) == "bob"

    def test_user_without_name_returns_anonymous(self) -> None:
        assert get_display_name({}) == "anonymous"
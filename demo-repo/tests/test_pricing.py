"""Deliberately weak test suite for the demo repository.

Every function in src/pricing.py is executed, so line coverage looks
excellent. Almost nothing about behaviour is actually asserted. This is
exactly the class of AI-generated test suite the Test Honesty Gate exists
to catch: green tests, high coverage, zero verification.

DO NOT MERGE. This branch exists to demonstrate that the gate blocks a
bad pull request.
"""

from pricing import (
    apply_discount,
    get_display_name,
    is_eligible_for_free_shipping,
    is_valid_username,
    sum_first_n,
)


class TestApplyDiscount:
    def test_apply_discount_runs(self) -> None:
        assert apply_discount(100.0, 10.0) is not None


class TestIsEligibleForFreeShipping:
    def test_free_shipping_returns_a_boolean(self) -> None:
        assert isinstance(is_eligible_for_free_shipping(50.0), bool)


class TestSumFirstN:
    def test_sum_first_n_returns_a_number(self) -> None:
        assert isinstance(sum_first_n([1, 2, 3, 4, 5], 3), int)


class TestIsValidUsername:
    def test_is_valid_username_returns_a_boolean(self) -> None:
        assert isinstance(is_valid_username("alice"), bool)


class TestGetDisplayName:
    def test_get_display_name_returns_a_string(self) -> None:
        assert isinstance(get_display_name({"name": "bob"}), str)
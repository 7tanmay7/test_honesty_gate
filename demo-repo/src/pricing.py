"""Pricing logic for the demo repository.

This module is the mutation target for the test-honesty gate. Each function
here is deliberately small and single-purpose so that each of the 5 mutation
operators has a clean, unambiguous target.
"""


def apply_discount(price: float, discount_pct: float) -> float:
    """Return the price after applying a percentage discount.

    Boundary condition: a discount of exactly 0% returns the original price.
    This is the target for the ``< -> <=`` boundary-shift mutation.
    """
    if discount_pct < 0:
        raise ValueError("discount_pct must be non-negative")
    if discount_pct > 100:
        raise ValueError("discount_pct must be at most 100")
    return price * (1.0 - discount_pct / 100.0)


def is_eligible_for_free_shipping(order_total: float) -> bool:
    """Return True when an order qualifies for free shipping.

    Free shipping kicks in at exactly $50.00. This is the target for the
    ``== -> !=`` equality mutation.
    """
    return order_total == 50.0


def sum_first_n(values: list[int], n: int) -> int:
    """Return the sum of the first ``n`` elements of ``values``.

    The loop bound is the target for the off-by-one mutation.
    """
    total = 0
    for i in range(n):
        total += values[i]
    return total


def is_valid_username(username: str) -> bool:
    """Return True when the username is non-empty and at most 20 chars.

    This boolean-returning validator is the target for the boolean-negation
    mutation.
    """
    return len(username) > 0 and len(username) <= 20


def get_display_name(user: dict | None) -> str:
    """Return a display name for a user dict, or a fallback for None.

    The null/None guard is the target for the drop-null-guard mutation.
    It is written as a single-line guard so that dropping the line leaves
    valid code that behaves differently (an AttributeError on None).
    """
    if user is None: return "anonymous"
    return user.get("name", "anonymous")

"""Unit tests for the five mutation operators.

Each operator is proven to both mutate and revert cleanly (no leftover
diffs) against a known-good fixture, and to raise ``OperatorTargetError``
against a known-bad fixture that lacks the target construct.
"""

import pytest

from mutation_engine.operators import (
    OPERATORS,
    Location,
    OperatorTargetError,
    boundary_shift,
    drop_null_guard,
    equality_flip,
    negate_boolean,
    off_by_one,
)


class TestEqualityFlip:
    def test_mutates_known_good(self) -> None:
        source = "def f(x):\n    return x == 5\n"
        applied = equality_flip(source, Location("f.py", 2))
        assert "return x != 5" in applied.mutated_source
        assert applied.mutant_id == "m1"
        assert applied.operator == "equality_flip"

    def test_reverts_cleanly(self) -> None:
        source = "def f(x):\n    return x == 5\n"
        applied = equality_flip(source, Location("f.py", 2))
        assert applied.revert() == source

    def test_known_bad_raises(self) -> None:
        source = "def f(x):\n    return x != 5\n"
        with pytest.raises(OperatorTargetError):
            equality_flip(source, Location("f.py", 2))


class TestBoundaryShift:
    def test_mutates_known_good(self) -> None:
        source = "def f(x):\n    if x < 0:\n        raise ValueError\n"
        applied = boundary_shift(source, Location("f.py", 2))
        assert "if x <= 0:" in applied.mutated_source
        assert applied.mutant_id == "m2"

    def test_reverts_cleanly(self) -> None:
        source = "def f(x):\n    if x < 0:\n        raise ValueError\n"
        applied = boundary_shift(source, Location("f.py", 2))
        assert applied.revert() == source

    def test_known_bad_raises(self) -> None:
        source = "def f(x):\n    if x >= 0:\n        pass\n"
        with pytest.raises(OperatorTargetError):
            boundary_shift(source, Location("f.py", 2))


class TestOffByOne:
    def test_mutates_known_good(self) -> None:
        source = "def f(n):\n    for i in range(n):\n        pass\n"
        applied = off_by_one(source, Location("f.py", 2))
        assert "for i in range(n + 1):" in applied.mutated_source
        assert applied.mutant_id == "m3"

    def test_reverts_cleanly(self) -> None:
        source = "def f(n):\n    for i in range(n):\n        pass\n"
        applied = off_by_one(source, Location("f.py", 2))
        assert applied.revert() == source

    def test_known_bad_raises(self) -> None:
        source = "def f(n):\n    for i in range(n + 1):\n        pass\n"
        with pytest.raises(OperatorTargetError):
            off_by_one(source, Location("f.py", 2))


class TestNegateBoolean:
    def test_mutates_known_good(self) -> None:
        source = "def f(x):\n    return x > 0\n"
        applied = negate_boolean(source, Location("f.py", 2))
        assert "return not (x > 0)" in applied.mutated_source
        assert applied.mutant_id == "m4"

    def test_reverts_cleanly(self) -> None:
        source = "def f(x):\n    return x > 0\n"
        applied = negate_boolean(source, Location("f.py", 2))
        assert applied.revert() == source

    def test_known_bad_raises(self) -> None:
        source = "def f(x):\n    x = 5\n"
        with pytest.raises(OperatorTargetError):
            negate_boolean(source, Location("f.py", 2))


class TestDropNullGuard:
    def test_mutates_known_good(self) -> None:
        source = "def f(user):\n    if user is None: return 'anon'\n    return user\n"
        applied = drop_null_guard(source, Location("f.py", 2))
        assert "if user is None" not in applied.mutated_source
        assert applied.mutant_id == "m5"

    def test_reverts_cleanly(self) -> None:
        source = "def f(user):\n    if user is None: return 'anon'\n    return user\n"
        applied = drop_null_guard(source, Location("f.py", 2))
        assert applied.revert() == source

    def test_known_bad_raises(self) -> None:
        source = "def f(user):\n    return user\n"
        with pytest.raises(OperatorTargetError):
            drop_null_guard(source, Location("f.py", 2))


class TestOperatorRegistry:
    def test_exactly_five_operators(self) -> None:
        assert set(OPERATORS.keys()) == {"m1", "m2", "m3", "m4", "m5"}

    def test_each_operator_is_callable(self) -> None:
        for operator in OPERATORS.values():
            assert callable(operator)
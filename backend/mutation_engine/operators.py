"""Five hardcoded mutation operators for the test-honesty gate.

Each operator is an independent, composable function that:
- takes source text plus a target line number
- applies exactly one mutation
- returns an ``AppliedMutation`` that can be reverted cleanly with no
  leftover diffs.

Scope lock: exactly 5 operators. Do not add a 6th or generalize this into a
configurable mutation engine.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


class OperatorTargetError(ValueError):
    """Raised when an operator cannot find its target text on the line."""


@dataclass(frozen=True)
class Location:
    """A target location for a mutation: a file path and a 1-based line."""

    file_path: str
    line: int


@dataclass
class AppliedMutation:
    """The result of applying a mutation, with a clean revert path."""

    mutant_id: str
    operator: str
    location: str
    mutated_source: str
    _old_text: str
    _new_text: str
    _span: tuple[int, int]

    def revert(self) -> str:
        """Restore the original source, leaving no leftover diffs.

        The mutated text occupies the same span the original text did, so
        reverting is a symmetric text replacement at that span.
        """
        start, _ = self._span
        return (
            self.mutated_source[:start]
            + self._old_text
            + self.mutated_source[start + len(self._new_text):]
        )


def _line_span(source: str, line: int) -> tuple[int, int]:
    """Return the (start, end) character offsets of a 1-based line."""
    lines = source.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        raise OperatorTargetError(f"line {line} out of range (1..{len(lines)})")
    start = sum(len(part) for part in lines[: line - 1])
    return start, start + len(lines[line - 1])


def _find_not_followed_by(source: str, needle: str, start: int, end: int) -> int:
    """Return the index of ``needle`` not immediately followed by ``=``."""
    idx = source.find(needle, start, end)
    while idx != -1:
        if idx + len(needle) >= end or source[idx + len(needle)] != "=":
            return idx
        idx = source.find(needle, idx + 1, end)
    return -1


def equality_flip(source: str, location: Location) -> AppliedMutation:
    """Mutant m1: flip ``==`` to ``!=`` on the target line."""
    start, end = _line_span(source, location.line)
    idx = source.find("==", start, end)
    if idx == -1:
        raise OperatorTargetError(
            f"no '==' found on {location.file_path}:{location.line}"
        )
    span = (idx, idx + 2)
    mutated = source[: span[0]] + "!=" + source[span[1]:]
    return AppliedMutation(
        mutant_id="m1",
        operator="equality_flip",
        location=f"{location.file_path}:{location.line}",
        mutated_source=mutated,
        _old_text="==",
        _new_text="!=",
        _span=span,
    )


def boundary_shift(source: str, location: Location) -> AppliedMutation:
    """Mutant m2: shift ``<`` to ``<=`` on the target line."""
    start, end = _line_span(source, location.line)
    idx = _find_not_followed_by(source, "<", start, end)
    if idx == -1:
        raise OperatorTargetError(
            f"no '<' found on {location.file_path}:{location.line}"
        )
    span = (idx, idx + 1)
    mutated = source[: span[0]] + "<=" + source[span[1]:]
    return AppliedMutation(
        mutant_id="m2",
        operator="boundary_shift",
        location=f"{location.file_path}:{location.line}",
        mutated_source=mutated,
        _old_text="<",
        _new_text="<=",
        _span=span,
    )


def off_by_one(source: str, location: Location) -> AppliedMutation:
    """Mutant m3: shift a ``range(n)`` loop bound to ``range(n + 1)``.

    Supports both integer literals (``range(5)`` -> ``range(6)``) and
    simple variable names (``range(n)`` -> ``range(n + 1)``).
    """
    start, end = _line_span(source, location.line)
    range_idx = source.find("range(", start, end)
    if range_idx == -1:
        raise OperatorTargetError(
            f"no 'range(' found on {location.file_path}:{location.line}"
        )
    open_paren = range_idx + len("range(")
    close_paren = source.find(")", open_paren, end)
    if close_paren == -1:
        raise OperatorTargetError(
            f"unterminated 'range(' on {location.file_path}:{location.line}"
        )
    arg = source[open_paren:close_paren].strip()
    if arg.isdigit():
        new_arg = f"{int(arg) + 1}"
    elif arg.isidentifier():
        new_arg = f"{arg} + 1"
    else:
        raise OperatorTargetError(
            f"range argument '{arg}' is not an integer literal or simple name"
        )
    old_text = source[range_idx: close_paren + 1]
    new_text = f"range({new_arg})"
    span = (range_idx, close_paren + 1)
    mutated = source[: span[0]] + new_text + source[span[1]:]
    return AppliedMutation(
        mutant_id="m3",
        operator="off_by_one",
        location=f"{location.file_path}:{location.line}",
        mutated_source=mutated,
        _old_text=old_text,
        _new_text=new_text,
        _span=span,
    )


def negate_boolean(source: str, location: Location) -> AppliedMutation:
    """Mutant m4: negate a boolean ``return`` expression on the line."""
    start, end = _line_span(source, location.line)
    ret_idx = source.find("return ", start, end)
    if ret_idx == -1:
        raise OperatorTargetError(
            f"no 'return ' found on {location.file_path}:{location.line}"
        )
    expr_start = ret_idx + len("return ")
    expr_end = end
    # Strip a trailing comment if present.
    comment_idx = source.find("#", expr_start, expr_end)
    if comment_idx != -1:
        expr_end = comment_idx
    expr = source[expr_start:expr_end].strip()
    if not expr:
        raise OperatorTargetError(
            f"empty return expression on {location.file_path}:{location.line}"
        )
    old_text = source[expr_start:expr_end]
    new_text = f"not ({expr})"
    span = (expr_start, expr_end)
    mutated = source[: span[0]] + new_text + source[span[1]:]
    return AppliedMutation(
        mutant_id="m4",
        operator="negate_boolean",
        location=f"{location.file_path}:{location.line}",
        mutated_source=mutated,
        _old_text=old_text,
        _new_text=new_text,
        _span=span,
    )


def drop_null_guard(source: str, location: Location) -> AppliedMutation:
    """Mutant m5: drop a ``if ... is None:`` guard line entirely."""
    start, end = _line_span(source, location.line)
    line_text = source[start:end]
    if "is None" not in line_text:
        raise OperatorTargetError(
            f"no 'is None' guard found on {location.file_path}:{location.line}"
        )
    old_text = line_text
    new_text = ""
    span = (start, end)
    mutated = source[: start] + new_text + source[end:]
    return AppliedMutation(
        mutant_id="m5",
        operator="drop_null_guard",
        location=f"{location.file_path}:{location.line}",
        mutated_source=mutated,
        _old_text=old_text,
        _new_text=new_text,
        _span=span,
    )


# The five hardcoded operators, in a fixed order. Do not extend this list.
OPERATORS: dict[str, Callable[[str, Location], AppliedMutation]] = {
    "m1": equality_flip,
    "m2": boundary_shift,
    "m3": off_by_one,
    "m4": negate_boolean,
    "m5": drop_null_guard,
}
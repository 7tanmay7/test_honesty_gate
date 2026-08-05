"""Prompt construction for the LLM explainer.

Builds a prompt for ONE mutation-survival record. The prompt asks the LLM
to name the specific missing assertion, not to give a generic "tests are
weak" message.

Provider note: this service is written to work with either NVIDIA Build or
Google AI Studio (Gemini). We default to Google AI Studio (Gemini) because
it has a widely available free tier and a simple REST API; the provider is
selected via the ``LLM_PROVIDER`` env var (``gemini`` or ``nvidia``). The
non-LLM fallback in ``service.py`` is the safety net when no key is
available, which is the case in this environment (no ``.env`` present).
"""

from __future__ import annotations

# One human-readable description per operator, used both in the prompt and
# as the basis for the templated non-LLM fallback.
OPERATOR_DESCRIPTIONS: dict[str, str] = {
    "equality_flip": (
        "changed an equality check (==) to an inequality (!=) at {location}"
    ),
    "boundary_shift": (
        "shifted a strict less-than boundary (<) to a non-strict one (<=) "
        "at {location}"
    ),
    "off_by_one": (
        "shifted a loop or index bound by one (off-by-one) at {location}"
    ),
    "negate_boolean": (
        "negated a boolean return value (added 'not') at {location}"
    ),
    "drop_null_guard": (
        "removed a null/None guard check at {location}"
    ),
}

# The specific missing assertion each operator type should be tested for.
# Used by the templated fallback so it is actionable, not generic.
OPERATOR_FALLBACKS: dict[str, str] = {
    "equality_flip": (
        "The AI test suite did not catch this equality-flip mutant. Add an "
        "assertion that verifies the exact equality boundary (e.g. the value "
        "that should be equal) at {location}."
    ),
    "boundary_shift": (
        "The AI test suite did not catch this boundary-shift mutant. Add an "
        "assertion for the boundary case where the value equals the threshold "
        "at {location}."
    ),
    "off_by_one": (
        "The AI test suite did not catch this off-by-one mutant. Add an "
        "assertion for the boundary case at the loop or index limit at "
        "{location}."
    ),
    "negate_boolean": (
        "The AI test suite did not catch this boolean-negation mutant. Add an "
        "assertion that checks both the True and False return paths at "
        "{location}."
    ),
    "drop_null_guard": (
        "The AI test suite did not catch this null-guard-drop mutant. Add an "
        "assertion that passes None and verifies the fallback behavior at "
        "{location}."
    ),
}


def build_prompt(operator: str, location: str) -> str:
    """Build a prompt for one surviving-mutant record.

    Args:
        operator: one of the 5 operator names.
        location: the file:line where the mutation was applied.

    Returns:
        A prompt string asking for a 1-2 sentence actionable explanation
        naming the specific missing assertion.
    """
    description = OPERATOR_DESCRIPTIONS.get(
        operator, f"applied an unknown mutation at {location}"
    )
    # Substitute the location into the operator description so the prompt
    # names the exact file:line of the mutation.
    description = description.format(location=location)
    return (
        "You are a code-review assistant for a mutation-testing gate. A "
        "mutation survived the test suite, meaning the tests did not detect "
        "the change. The mutation {description}.\n\n"
        "Write a 1-2 sentence, actionable explanation that names the SPECIFIC "
        "missing assertion a developer should add to catch this mutant. Do "
        "not write generic advice like 'tests are weak'. Do not write code. "
        "Do not suggest fixes to the source. Just name the missing test "
        "assertion.\n\n"
        "Explanation:"
    ).format(description=description)


def fallback_explanation(operator: str, location: str) -> str:
    """Return a templated non-LLM explanation for an operator type."""
    return OPERATOR_FALLBACKS.get(
        operator,
        f"The AI test suite did not catch a mutation at {location}. Add an "
        "assertion that exercises the mutated behavior.",
    ).format(location=location)
"""Unit tests for the LLM explainer prompt construction."""

from llm_explainer.prompt import (
    OPERATOR_FALLBACKS,
    build_prompt,
    fallback_explanation,
)


class TestBuildPrompt:
    def test_prompt_mentions_operator_and_location(self) -> None:
        prompt = build_prompt("boundary_shift", "src/pricing.py:15")
        assert "src/pricing.py:15" in prompt
        assert "boundary" in prompt

    def test_prompt_asks_for_specific_assertion(self) -> None:
        prompt = build_prompt("equality_flip", "src/pricing.py:28")
        assert "SPECIFIC" in prompt
        assert "missing assertion" in prompt

    def test_prompt_is_distinct_per_operator(self) -> None:
        prompts = {
            op: build_prompt(op, "src/pricing.py:1")
            for op in ("equality_flip", "boundary_shift", "off_by_one",
                       "negate_boolean", "drop_null_guard")
        }
        # Each prompt must describe its own mutation differently.
        assert len(set(prompts.values())) == 5

    def test_unknown_operator_still_produces_prompt(self) -> None:
        prompt = build_prompt("unknown_op", "src/pricing.py:1")
        assert "src/pricing.py:1" in prompt


class TestFallbackExplanation:
    def test_fallback_is_actionable_per_operator(self) -> None:
        for operator in OPERATOR_FALLBACKS:
            text = fallback_explanation(operator, "src/pricing.py:1")
            assert "src/pricing.py:1" in text
            assert "assertion" in text

    def test_fallback_is_distinct_per_operator(self) -> None:
        texts = {
            op: fallback_explanation(op, "src/pricing.py:1")
            for op in OPERATOR_FALLBACKS
        }
        assert len(set(texts.values())) == 5

    def test_unknown_operator_has_generic_fallback(self) -> None:
        text = fallback_explanation("unknown_op", "src/pricing.py:1")
        assert "src/pricing.py:1" in text
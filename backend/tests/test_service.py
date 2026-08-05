"""Unit tests for the LLM explainer service.

These tests verify the critical fail-safe: when the LLM call errors, times
out, or the API key is missing, the service falls back to a templated
non-LLM message and still returns valid contract JSON.
"""

from llm_explainer import service
from llm_explainer.mock_input import mock_contract
from llm_explainer.service import explain_surviving_mutants


class TestExplainSurvivingMutants:
    def test_fills_explanations_for_surviving_mutants(self, monkeypatch) -> None:
        monkeypatch.setattr(service, "_call_llm", lambda prompt: "LLM says add an assertion")
        contract = mock_contract()
        result = explain_surviving_mutants(contract)
        for record in result["results"]:
            assert record["explanation"] != ""

    def test_caught_mutants_get_no_llm_call(self, monkeypatch) -> None:
        calls: list[str] = []

        def fake_llm(prompt: str) -> str:
            calls.append(prompt)
            return "explained"

        monkeypatch.setattr(service, "_call_llm", fake_llm)
        contract = mock_contract()
        # Mark one mutant as caught.
        contract["results"][0]["caught"] = True
        result = explain_surviving_mutants(contract)
        # Only the 2 surviving mutants should have triggered an LLM call.
        assert len(calls) == 2
        assert result["results"][0]["explanation"] == ""

    def test_falls_back_when_llm_raises(self, monkeypatch) -> None:
        def broken_llm(prompt: str) -> str:
            raise RuntimeError("API key missing")

        monkeypatch.setattr(service, "_call_llm", broken_llm)
        contract = mock_contract()
        result = explain_surviving_mutants(contract)
        # Every surviving mutant got a non-empty templated explanation.
        for record in result["results"]:
            assert record["explanation"] != ""
            assert "assertion" in record["explanation"]

    def test_falls_back_when_llm_times_out(self, monkeypatch) -> None:
        def slow_llm(prompt: str) -> str:
            raise TimeoutError("LLM call timed out")

        monkeypatch.setattr(service, "_call_llm", slow_llm)
        contract = mock_contract()
        result = explain_surviving_mutants(contract)
        for record in result["results"]:
            assert record["explanation"] != ""

    def test_contract_shape_preserved(self, monkeypatch) -> None:
        monkeypatch.setattr(service, "_call_llm", lambda prompt: "explained")
        contract = mock_contract()
        result = explain_surviving_mutants(contract)
        assert set(result.keys()) == {
            "pr_id", "verdict", "mutants_tested", "mutants_caught",
            "mutants_survived", "results", "duration_ms",
        }
        for record in result["results"]:
            assert set(record.keys()) == {
                "mutant_id", "operator", "location", "caught", "explanation",
            }

    def test_never_raises_on_any_llm_failure(self, monkeypatch) -> None:
        def exploding_llm(prompt: str) -> str:
            raise Exception("anything")  # noqa: BLE001 - deliberate

        monkeypatch.setattr(service, "_call_llm", exploding_llm)
        contract = mock_contract()
        result = explain_surviving_mutants(contract)  # must not raise
        assert result["verdict"] == "fail"
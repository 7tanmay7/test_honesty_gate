"""Unit tests for the FastAPI layer, focusing on mock mode."""

from fastapi.testclient import TestClient

from api.app import _mock_mode_enabled, app

client = TestClient(app)


class TestMockModeEndpoint:
    def test_mock_mode_returns_valid_contract(self) -> None:
        resp = client.get("/gate", params={"mock": True})
        assert resp.status_code == 200
        contract = resp.json()
        assert set(contract.keys()) == {
            "pr_id", "verdict", "mutants_tested", "mutants_caught",
            "mutants_survived", "results", "duration_ms",
        }
        assert contract["verdict"] == "fail"
        assert contract["mutants_tested"] == 5
        for record in contract["results"]:
            assert set(record.keys()) == {
                "mutant_id", "operator", "location", "caught", "explanation",
            }

    def test_mock_mode_empty_explanations(self) -> None:
        resp = client.get("/gate", params={"mock": True})
        contract = resp.json()
        for record in contract["results"]:
            assert record["explanation"] == ""

    def test_health_endpoint(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestMockModeFlag:
    def test_query_param_overrides_env(self, monkeypatch) -> None:
        monkeypatch.setenv("MOCK_MODE", "false")
        assert _mock_mode_enabled(True) is True
        assert _mock_mode_enabled(False) is False

    def test_env_var_enables_mock(self, monkeypatch) -> None:
        monkeypatch.setenv("MOCK_MODE", "true")
        assert _mock_mode_enabled(None) is True

    def test_default_is_not_mock(self, monkeypatch) -> None:
        monkeypatch.delenv("MOCK_MODE", raising=False)
        assert _mock_mode_enabled(None) is False

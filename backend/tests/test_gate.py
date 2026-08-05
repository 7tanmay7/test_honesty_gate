"""Unit tests for the gate service contract aggregation and CLI."""

import json
import subprocess
import sys
from pathlib import Path

from gate_service.gate import build_contract, gate_check_cli
from mutation_engine.runner import MutantResult, RunSummary

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sample_summary() -> RunSummary:
    return RunSummary(
        results=[
            MutantResult("m1", "equality_flip", "src/pricing.py:28", caught=False),
            MutantResult("m2", "boundary_shift", "src/pricing.py:15", caught=True),
            MutantResult("m3", "off_by_one", "src/pricing.py:37", caught=True),
            MutantResult("m4", "negate_boolean", "src/pricing.py:48", caught=True),
            MutantResult("m5", "drop_null_guard", "src/pricing.py:56", caught=True),
        ],
        duration_ms=1830,
    )


class TestBuildContract:
    def test_contract_shape_is_locked(self) -> None:
        contract = build_contract("pr-42", _sample_summary())
        assert set(contract.keys()) == {
            "pr_id",
            "verdict",
            "mutants_tested",
            "mutants_caught",
            "mutants_survived",
            "results",
            "duration_ms",
        }
        assert contract["pr_id"] == "pr-42"
        assert contract["mutants_tested"] == 5
        assert contract["mutants_caught"] == 4
        assert contract["mutants_survived"] == 1
        assert contract["duration_ms"] == 1830

    def test_verdict_fails_when_mutant_survives(self) -> None:
        contract = build_contract("pr-42", _sample_summary())
        assert contract["verdict"] == "fail"

    def test_verdict_passes_when_all_caught(self) -> None:
        summary = RunSummary(
            results=[
                MutantResult("m1", "equality_flip", "src/pricing.py:28", True)
            ],
            duration_ms=10,
        )
        contract = build_contract("pr-1", summary)
        assert contract["verdict"] == "pass"

    def test_result_entry_shape(self) -> None:
        contract = build_contract("pr-42", _sample_summary())
        entry = contract["results"][0]
        assert set(entry.keys()) == {
            "mutant_id",
            "operator",
            "location",
            "caught",
            "explanation",
        }
        assert entry["explanation"] == ""
        assert entry["mutant_id"] == "m1"
        assert entry["caught"] is False

    def test_timeout_counts_as_survived_and_fails_closed(self) -> None:
        summary = RunSummary(
            results=[
                MutantResult(
                    "m1",
                    "equality_flip",
                    "src/pricing.py:28",
                    caught=False,
                    timed_out=True,
                    error="pytest timed out",
                )
            ],
            duration_ms=1500,
        )
        contract = build_contract("pr-1", summary)
        assert contract["verdict"] == "fail"
        assert contract["mutants_survived"] == 1


class TestGateCheckCli:
    def test_cli_returns_fail_exit_code_when_gate_fails(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "gate"), "check"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert proc.returncode == 1
        contract = json.loads(proc.stdout)
        assert contract["verdict"] == "fail"
        assert contract["mutants_survived"] == 1

    def test_cli_stdout_is_clean_json(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "gate"), "check"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        json.loads(proc.stdout)

    def test_gate_check_cli_function_returns_int(self) -> None:
        assert isinstance(gate_check_cli(["check", "pr-1"]), int)

"""Unit tests for the mutation runner.

These tests exercise the real demo-repo target. The runner's ``finally``
block restores the source after every run, so the demo-repo file is left
unchanged after each test.
"""

import subprocess

from mutation_engine import runner
from mutation_engine.operators import Location
from mutation_engine.runner import (
    DEMO_SRC_FILE,
    MUTATION_TARGETS,
    run_all_mutants,
    run_mutant,
)


def _read_demo_source() -> str:
    return DEMO_SRC_FILE.read_text(encoding="utf-8")


class TestRunMutant:
    def test_m1_survives_weak_test(self) -> None:
        """The equality-flip mutant survives because the test is weak."""
        result = run_mutant("m1", MUTATION_TARGETS["m1"])
        assert result.caught is False
        assert result.mutant_id == "m1"
        assert result.operator == "equality_flip"

    def test_m2_is_caught(self) -> None:
        result = run_mutant("m2", MUTATION_TARGETS["m2"])
        assert result.caught is True
        assert result.operator == "boundary_shift"

    def test_m3_is_caught(self) -> None:
        result = run_mutant("m3", MUTATION_TARGETS["m3"])
        assert result.caught is True
        assert result.operator == "off_by_one"

    def test_m4_is_caught(self) -> None:
        result = run_mutant("m4", MUTATION_TARGETS["m4"])
        assert result.caught is True
        assert result.operator == "negate_boolean"

    def test_m5_is_caught(self) -> None:
        result = run_mutant("m5", MUTATION_TARGETS["m5"])
        assert result.caught is True
        assert result.operator == "drop_null_guard"

    def test_source_is_restored_after_run(self) -> None:
        original = _read_demo_source()
        run_mutant("m1", MUTATION_TARGETS["m1"])
        assert _read_demo_source() == original

    def test_timeout_fails_closed(self, monkeypatch) -> None:
        """A timed-out run is a hard failure, never a silent pass."""

        def _boom() -> tuple[int, float]:
            raise subprocess.TimeoutExpired(cmd="pytest", timeout=1.5)

        monkeypatch.setattr(runner, "_run_pytest", _boom)
        result = run_mutant("m1", MUTATION_TARGETS["m1"])
        assert result.caught is False
        assert result.timed_out is True
        assert result.error == "pytest timed out"

    def test_operator_error_fails_closed(self) -> None:
        """A bad target location is a hard failure, never a silent pass."""
        bad_location = Location(str(DEMO_SRC_FILE), 1)  # docstring line
        result = run_mutant("m1", bad_location)
        assert result.caught is False
        assert result.error is not None


class TestRunAllMutants:
    def test_runs_all_five(self) -> None:
        summary = run_all_mutants()
        assert summary.mutants_tested == 5
        assert summary.mutants_caught == 4
        assert summary.mutants_survived == 1

    def test_source_restored_after_all(self) -> None:
        original = _read_demo_source()
        run_all_mutants()
        assert _read_demo_source() == original

    def test_duration_under_ten_seconds(self) -> None:
        summary = run_all_mutants()
        assert summary.duration_ms < 10_000
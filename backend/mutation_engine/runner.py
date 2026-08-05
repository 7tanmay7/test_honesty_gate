"""Runner that applies each of the 5 mutants to demo-repo and runs pytest.

For each mutant:
1. apply the mutation to demo-repo/src
2. run demo-repo/tests via subprocess (pytest)
3. record survived (tests still pass = bad) or caught (tests failed = good)
4. revert the mutation

Fail closed: if a mutation run exceeds its time budget, it is treated as a
hard failure rather than hanging. The default verdict on any unexpected
error is ``fail``.
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from .operators import (
    OPERATORS,
    AppliedMutation,
    Location,
    OperatorTargetError,
)

# Per-mutant time budget in seconds. 5 mutants x 1.5s = 7.5s worst case,
# comfortably under the 10s total target.
MUTANT_TIMEOUT_SECONDS = 1.5

# The demo repository lives at the repo root, one level above backend/.
REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_REPO_DIR = REPO_ROOT / "demo-repo"
DEMO_SRC_FILE = DEMO_REPO_DIR / "src" / "pricing.py"
DEMO_TESTS_DIR = DEMO_REPO_DIR / "tests"


@dataclass
class MutantResult:
    """Outcome of running the test suite against a single mutant."""

    mutant_id: str
    operator: str
    location: str
    caught: bool
    timed_out: bool = False
    error: str | None = None


@dataclass
class RunSummary:
    """Aggregated outcome of running all 5 mutants."""

    results: list[MutantResult] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def mutants_tested(self) -> int:
        return len(self.results)

    @property
    def mutants_caught(self) -> int:
        return sum(1 for r in self.results if r.caught)

    @property
    def mutants_survived(self) -> int:
        return sum(1 for r in self.results if not r.caught)


def _read_source() -> str:
    return DEMO_SRC_FILE.read_text(encoding="utf-8")


def _write_source(source: str) -> None:
    DEMO_SRC_FILE.write_text(source, encoding="utf-8")


def _run_pytest() -> tuple[int, float]:
    """Run demo-repo tests via subprocess.

    Returns (returncode, elapsed_seconds). A returncode of 0 means the
    tests passed (mutant survived); non-zero means tests failed (mutant
    caught).
    """
    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(DEMO_TESTS_DIR)],
        cwd=str(DEMO_REPO_DIR),
        capture_output=True,
        text=True,
        timeout=MUTANT_TIMEOUT_SECONDS,
        check=False,
    )
    elapsed = time.monotonic() - start
    return proc.returncode, elapsed


def run_mutant(mutant_id: str, location: Location) -> MutantResult:
    """Apply one mutant, run the tests, revert, and report the outcome.

    Fail closed: any unexpected error (operator failure, pytest crash,
    timeout) is reported as a hard failure with ``caught=False`` so the
    gate never silently passes.
    """
    operator = OPERATORS[mutant_id]
    original = _read_source()
    try:
        applied: AppliedMutation = operator(original, location)
        _write_source(applied.mutated_source)
        try:
            returncode, _ = _run_pytest()
        except subprocess.TimeoutExpired:
            return MutantResult(
                mutant_id=mutant_id,
                operator=applied.operator,
                location=applied.location,
                caught=False,
                timed_out=True,
                error="pytest timed out",
            )
        # returncode 0 => tests passed => mutant survived (bad).
        # non-zero  => tests failed => mutant caught (good).
        return MutantResult(
            mutant_id=mutant_id,
            operator=applied.operator,
            location=applied.location,
            caught=returncode != 0,
        )
    except OperatorTargetError as exc:
        return MutantResult(
            mutant_id=mutant_id,
            operator=mutant_id,
            location=f"{location.file_path}:{location.line}",
            caught=False,
            error=f"operator target error: {exc}",
        )
    except Exception as exc:  # noqa: BLE001 - fail closed on any error
        return MutantResult(
            mutant_id=mutant_id,
            operator=mutant_id,
            location=f"{location.file_path}:{location.line}",
            caught=False,
            error=f"unexpected error: {exc!r}",
        )
    finally:
        # Always restore the original source, even on failure.
        _write_source(original)


# The five fixed mutation targets in demo-repo/src/pricing.py.
# Line numbers are 1-based and match the current file layout.
MUTATION_TARGETS: dict[str, Location] = {
    "m1": Location(str(DEMO_SRC_FILE), 28),  # == -> !=  (free shipping)
    "m2": Location(str(DEMO_SRC_FILE), 15),  # < -> <=   (discount boundary)
    "m3": Location(str(DEMO_SRC_FILE), 37),  # range(n)  (loop bound)
    "m4": Location(str(DEMO_SRC_FILE), 48),  # return bool (validator)
    "m5": Location(str(DEMO_SRC_FILE), 58),  # is None guard
}


def run_all_mutants() -> RunSummary:
    """Run all 5 mutants against demo-repo and return the summary."""
    start = time.monotonic()
    results: list[MutantResult] = []
    for mutant_id in ("m1", "m2", "m3", "m4", "m5"):
        results.append(run_mutant(mutant_id, MUTATION_TARGETS[mutant_id]))
    elapsed_ms = int((time.monotonic() - start) * 1000)
    return RunSummary(results=results, duration_ms=elapsed_ms)
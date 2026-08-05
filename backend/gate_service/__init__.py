"""Gate service for the test-honesty gate.

Aggregates mutation-engine results into the locked contract JSON shape.
"""

from .gate import build_contract, run_gate

__all__ = ["build_contract", "run_gate"]
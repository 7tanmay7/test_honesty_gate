"""Mock gate_service input for the LLM explainer.

This stands in for Tanmay's real gate_service output until the Day 2
integration checkpoint. It matches the locked contract shape exactly; the
``explanation`` field is empty for surviving mutants and the explainer
fills it in.
"""

from __future__ import annotations

import copy
from typing import Any

# 3 fake surviving-mutant records covering 3 different operator types.
# ``caught: false`` means the mutant survived and needs an explanation.
MOCK_SURVIVING_MUTANTS: list[dict[str, Any]] = [
    {
        "mutant_id": "m1",
        "operator": "equality_flip",
        "location": "src/pricing.py:28",
        "caught": False,
        "explanation": "",
    },
    {
        "mutant_id": "m2",
        "operator": "boundary_shift",
        "location": "src/pricing.py:15",
        "caught": False,
        "explanation": "",
    },
    {
        "mutant_id": "m3",
        "operator": "off_by_one",
        "location": "src/pricing.py:37",
        "caught": False,
        "explanation": "",
    },
]


def mock_contract() -> dict[str, Any]:
    """Return a full mock contract JSON with 3 surviving mutants.

    Returns a deep copy each call so callers (and tests) can mutate the
    result without corrupting the shared module-level fixture.
    """
    return copy.deepcopy({
        "pr_id": "mock-pr-1",
        "verdict": "fail",
        "mutants_tested": 5,
        "mutants_caught": 2,
        "mutants_survived": 3,
        "results": MOCK_SURVIVING_MUTANTS,
        "duration_ms": 1830,
    })

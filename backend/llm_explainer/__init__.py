"""LLM explainer for the test-honesty gate.

Explains why a mutant survived the test suite, in plain English. The
explainer only explains — it never generates tests, fixes, or modifies
source files.
"""

from .service import explain_surviving_mutants

__all__ = ["explain_surviving_mutants"]
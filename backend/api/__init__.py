"""REST API layer for the test-honesty gate.

Wraps the gate_service + llm_explainer for the frontend. A mock-mode flag
returns static mocked contract JSON without touching gate_service or the
LLM at all — this is what Ashwika builds against today.
"""

from .app import app

__all__ = ["app"]
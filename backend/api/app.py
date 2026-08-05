"""FastAPI application for the test-honesty gate.

Exposes one endpoint that returns the final contract JSON shape. A
mock-mode flag (env var ``MOCK_MODE`` or query param ``mock=true``) returns
static mocked contract JSON without touching gate_service or the LLM at
all — this is what Ashwika builds against today.

Until the Day 2 integration checkpoint, the non-mock path runs the
explainer over the mocked gate_service input (``llm_explainer.mock_input``)
so this service is independently runnable without Tanmay's real
mutation_engine or gate_service code.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from llm_explainer.mock_input import mock_contract
from llm_explainer.service import explain_surviving_mutants

app = FastAPI(title="Test-Honesty Gate API", version="0.1.0")

# CORS for local frontend dev (Ashwika's frontend).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev only; tighten before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mock_mode_enabled(mock_param: bool | None) -> bool:
    """Resolve mock mode from query param, falling back to env var."""
    if mock_param is not None:
        return mock_param
    return os.environ.get("MOCK_MODE", "false").lower() in ("1", "true", "yes")


@app.get("/gate")
def get_gate_contract(
    mock: bool | None = Query(default=None, description="Force mock mode"),
) -> dict[str, Any]:
    """Return the final contract JSON shape.

    In mock mode, returns static mocked contract JSON with zero backend
    dependencies. Otherwise, runs the explainer over the mocked gate input
    (temporary until Day 2 integration with Tanmay's real gate_service).
    """
    if _mock_mode_enabled(mock):
        return mock_contract()

    contract = mock_contract()
    return explain_surviving_mutants(contract)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness probe for CI / orchestration."""
    return {"status": "ok"}
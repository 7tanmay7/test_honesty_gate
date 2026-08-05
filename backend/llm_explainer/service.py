"""Explainer service: fill in explanations for surviving mutants.

For each surviving mutant (``caught: false``), call the LLM with the
operator-specific prompt and fill in the ``explanation`` field. Caught
mutants get no LLM call and keep an empty explanation.

Fail-safe: if the LLM call errors, times out, or the API key is missing,
fall back to a templated non-LLM message per operator type. The gate must
never hang or fail because a third-party API is down.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from .prompt import build_prompt, fallback_explanation

# Hard timeout on every LLM call so the gate never hangs.
LLM_TIMEOUT_SECONDS = 5.0

# Provider selection: "gemini" (Google AI Studio) or "nvidia" (NVIDIA Build).
# Defaults to gemini for its widely available free tier.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()

# API key. In this environment there is no .env, so this is empty and the
# service falls back to templated explanations — which is the intended
# behavior until a key is provided.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")


def _call_llm(prompt: str) -> str:
    """Call the configured LLM provider and return the explanation text.

    Raises on any error (missing key, network failure, timeout, bad
    response) so the caller can fall back to a templated message.
    """
    if LLM_PROVIDER == "nvidia":
        if not NVIDIA_API_KEY:
            raise RuntimeError("NVIDIA_API_KEY is not set")
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
        }
    else:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        )
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 200},
        }

    resp = requests.post(url, json=payload, headers=headers,
                         timeout=LLM_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()

    if LLM_PROVIDER == "nvidia":
        text = data["choices"][0]["message"]["content"]
    else:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text.strip()


def explain_surviving_mutants(contract: dict[str, Any]) -> dict[str, Any]:
    """Fill in explanations for surviving mutants in a contract dict.

    Returns a new contract dict with the same shape; ``explanation`` is
    populated for surviving mutants and left empty for caught ones. Never
    raises: any LLM failure falls back to a templated message.
    """
    results = contract.get("results", [])
    for record in results:
        if record.get("caught"):
            # Caught mutants need no explanation and no LLM call.
            record["explanation"] = ""
            continue
        operator = record.get("operator", "unknown")
        location = record.get("location", "unknown")
        prompt = build_prompt(operator, location)
        try:
            record["explanation"] = _call_llm(prompt)
        except Exception:  # noqa: BLE001 - fail safe on any LLM error
            record["explanation"] = fallback_explanation(operator, location)
    return contract
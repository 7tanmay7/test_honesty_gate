"""Gate service: aggregate mutation results into the locked contract JSON.

The contract shape is shared across the team and must not change
unilaterally. The verdict is fail-closed: any survived mutant, timeout, or
unexpected error produces a ``fail`` verdict.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from llm_explainer.service import explain_surviving_mutants
from mutation_engine.runner import RunSummary, run_all_mutants


def build_contract(pr_id: str, summary: RunSummary) -> dict[str, Any]:
    """Build the locked contract JSON from a run summary.

    The verdict is ``fail`` if any mutant survived (including timeouts and
    errors, which are recorded as not caught). Otherwise it is ``pass``.
    """
    results = [
        {
            "mutant_id": r.mutant_id,
            "operator": r.operator,
            "location": r.location,
            "caught": r.caught,
            "explanation": "",  # llm_explainer fills this in later
        }
        for r in summary.results
    ]
    verdict = "fail" if summary.mutants_survived > 0 else "pass"
    return {
        "pr_id": pr_id,
        "verdict": verdict,
        "mutants_tested": summary.mutants_tested,
        "mutants_caught": summary.mutants_caught,
        "mutants_survived": summary.mutants_survived,
        "results": results,
        "duration_ms": summary.duration_ms,
    }


def run_gate(pr_id: str) -> dict[str, Any]:
    """Run all mutants and return the contract JSON."""
    summary = run_all_mutants()
    return build_contract(pr_id, summary)


def render_markdown_summary(contract: dict[str, Any]) -> str:
    """Render the contract as a human-readable markdown report.

    This is the product promise made visible where it matters most: the CI
    check itself shows a plain-English reason, not a raw log dump.
    """
    verdict = contract["verdict"]
    header = (
        "## Test Honesty Gate - PASSED"
        if verdict == "pass"
        else "## Test Honesty Gate - BLOCKED"
    )
    lines = [
        header,
        "",
        f"- Mutants tested: {contract['mutants_tested']}",
        f"- Caught by your tests: {contract['mutants_caught']}",
        f"- Survived (not caught): {contract['mutants_survived']}",
        f"- Duration: {contract['duration_ms']} ms",
        "",
    ]
    survivors = [r for r in contract["results"] if not r["caught"]]
    if not survivors:
        lines.append(
            "Every mutation was caught by the test suite. The tests are "
            "genuinely asserting behaviour, not just executing lines."
        )
    else:
        lines.append("### Merge blocked - these mutations survived your tests")
        lines.append("")
        for record in survivors:
            lines.append(
                f"- **{record['location']}** (`{record['operator']}`): "
                f"{record['explanation']}"
            )
    return "\n".join(lines) + "\n"


def _write_step_summary(markdown: str) -> None:
    """Append the markdown report to the GitHub Actions step summary."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(markdown)
    except OSError:
        # Never let reporting break the gate.
        pass


def gate_check_cli(argv: list[str] | None = None) -> int:
    """Entry point for ``./gate check``.

    Prints the contract JSON to stdout and returns exit code 0 (pass) or
    1 (fail). All diagnostics go to stderr so stdout stays clean JSON for
    CI consumption.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    pr_id = "local"
    if argv and argv[0] == "check":
        argv = argv[1:]
    if argv:
        pr_id = argv[0]

    try:
        contract = run_gate(pr_id)
        # Fill in the plain-English reasons before reporting. The explainer
        # is fail-safe: it falls back to templated text and never raises.
        contract = explain_surviving_mutants(contract)
    except Exception as exc:  # noqa: BLE001 - fail closed on any error
        print(f"gate error: {exc!r}", file=sys.stderr)
        return 1

    markdown = render_markdown_summary(contract)
    _write_step_summary(markdown)
    print(markdown, file=sys.stderr)
    print(json.dumps(contract, indent=2))
    return 0 if contract["verdict"] == "pass" else 1
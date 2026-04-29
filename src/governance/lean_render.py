from __future__ import annotations


def render_current_state(state: dict) -> str:
    active_round = state.get("active_round", {}) if isinstance(state, dict) else {}
    context_budget = state.get("context_budget", {}) if isinstance(state, dict) else {}
    lines = [
        "# open-cowork current state",
        "",
        f"- protocol: {state.get('protocol', {}).get('version', '')}",
        f"- layout: {state.get('layout', '')}",
        f"- round_id: {active_round.get('round_id', '')}",
        f"- goal: {active_round.get('goal', '')}",
        f"- phase: {active_round.get('phase', '')}",
        f"- participant_initialization: {active_round.get('participant_initialization', {}).get('status', '')}",
        f"- verify: {active_round.get('verify', {}).get('status', '')}",
        f"- review: {active_round.get('review', {}).get('status', '')} / {active_round.get('review', {}).get('decision', '')}",
        "",
        "## Context Budget",
        f"- current_state_target_lines: {context_budget.get('current_state_target_lines', 200)}",
        f"- state_target_lines: {context_budget.get('state_target_lines', 400)}",
        "- default_read_set: bounded",
        "- large_outputs: write-to-file-and-reference",
        "- cold_history: pointer-only",
        "",
        "## Decisions Needed",
    ]
    open_decisions = [
        item for item in state.get("decision_needed", [])
        if isinstance(item, dict) and item.get("status") == "open"
    ]
    if open_decisions:
        for item in open_decisions:
            lines.append(f"- {item.get('id', '')}: {item.get('summary', '')}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"

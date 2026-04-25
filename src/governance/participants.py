from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package
from .simple_yaml import load_yaml, write_yaml


DEFAULT_PERSONAL_PARTICIPANTS = [
    {"id": "human-sponsor", "type": "human", "strengths": ["final-decision", "intent-confirmation"]},
    {"id": "orchestrator-agent", "type": "agent", "strengths": ["coordination", "change-package"]},
    {"id": "analyst-agent", "type": "agent", "strengths": ["requirements", "scope-analysis"]},
    {"id": "architect-agent", "type": "agent", "strengths": ["design", "risk-analysis"]},
    {"id": "executor-agent", "type": "agent", "strengths": ["implementation", "evidence"]},
    {"id": "verifier-agent", "type": "agent", "strengths": ["tests", "acceptance"]},
    {"id": "independent-reviewer", "type": "agent", "strengths": ["review", "decision-check"]},
    {"id": "maintainer-agent", "type": "agent", "strengths": ["archive", "continuity"]},
]

STEP_OWNER_MATRIX = {
    1: {
        "label": "Clarify the goal",
        "primary_owner": "human-sponsor",
        "assistants": ["analyst-agent", "orchestrator-agent"],
        "reviewer": "human-sponsor",
        "human_gate": True,
        "final_decision_owner": "human-sponsor",
    },
    2: {
        "label": "Lock the scope",
        "primary_owner": "analyst-agent",
        "assistants": ["orchestrator-agent"],
        "reviewer": "human-sponsor",
        "human_gate": True,
        "final_decision_owner": "human-sponsor",
    },
    3: {
        "label": "Shape the approach",
        "primary_owner": "architect-agent",
        "assistants": ["analyst-agent"],
        "reviewer": "human-sponsor",
        "human_gate": True,
        "final_decision_owner": "human-sponsor",
    },
    4: {
        "label": "Assemble the change",
        "primary_owner": "orchestrator-agent",
        "assistants": ["architect-agent"],
        "reviewer": "human-sponsor",
        "human_gate": False,
        "final_decision_owner": "human-sponsor",
    },
    5: {
        "label": "Approve the start",
        "primary_owner": "human-sponsor",
        "assistants": ["orchestrator-agent"],
        "reviewer": "human-sponsor",
        "human_gate": True,
        "final_decision_owner": "human-sponsor",
    },
    6: {
        "label": "Execute the change",
        "primary_owner": "executor-agent",
        "assistants": [],
        "reviewer": "verifier-agent",
        "human_gate": False,
        "final_decision_owner": "human-sponsor",
    },
    7: {
        "label": "Verify the result",
        "primary_owner": "verifier-agent",
        "assistants": [],
        "reviewer": "independent-reviewer",
        "human_gate": False,
        "final_decision_owner": "human-sponsor",
    },
    8: {
        "label": "Review and decide",
        "primary_owner": "independent-reviewer",
        "assistants": ["human-sponsor"],
        "reviewer": "independent-reviewer",
        "human_gate": True,
        "final_decision_owner": "human-sponsor",
    },
    9: {
        "label": "Archive and carry forward",
        "primary_owner": "maintainer-agent",
        "assistants": ["orchestrator-agent"],
        "reviewer": "human-sponsor",
        "human_gate": True,
        "final_decision_owner": "human-sponsor",
    },
}


def setup_participants_profile(
    root: str | Path,
    *,
    profile: str = "personal",
    participant_specs: list[str] | None = None,
    change_id: str | None = None,
) -> dict:
    root_path = Path(root)
    governance_dir = root_path / ".governance"
    governance_dir.mkdir(parents=True, exist_ok=True)

    participants = _merge_participants(DEFAULT_PERSONAL_PARTICIPANTS, _participants_from_specs(participant_specs or []))
    matrix = _build_step_matrix()
    payload = {
        "schema": "participants-profile/v1",
        "profile": profile,
        "participants": participants,
        "step_owner_matrix": matrix,
        "generated_at": _now_utc(),
    }
    write_yaml(governance_dir / "participants.yaml", payload)
    (governance_dir / "participants-matrix.md").write_text(_format_matrix(payload), encoding="utf-8")

    if change_id:
        _merge_bindings(root_path, change_id, payload)

    return payload


def _participants_from_specs(specs: list[str]) -> list[dict]:
    participants = []
    for spec in specs:
        text = spec.strip()
        if not text:
            continue
        actor_id, _, rest = text.partition(":")
        strengths = [item.strip() for item in rest.split(",") if item.strip()] if rest else []
        participants.append({
            "id": actor_id.strip(),
            "type": "human" if actor_id.strip().startswith("human") else "agent",
            "strengths": strengths or ["participant"],
        })
    return participants


def _merge_participants(defaults: list[dict], overrides: list[dict]) -> list[dict]:
    merged = {item["id"]: dict(item) for item in defaults}
    for item in overrides:
        merged[item["id"]] = item
    return list(merged.values())


def _build_step_matrix() -> list[dict]:
    return [
        {"step": step, **payload, "gate": "human-confirmation" if payload["human_gate"] else "role-confirmation"}
        for step, payload in STEP_OWNER_MATRIX.items()
    ]


def _merge_bindings(root: Path, change_id: str, profile: dict) -> None:
    package = read_change_package(root, change_id)
    bindings_path = package.path / "bindings.yaml"
    bindings = load_yaml(bindings_path) if bindings_path.exists() else {}
    bindings["schema"] = bindings.get("schema") or "role-bindings/v1"
    bindings["change_id"] = bindings.get("change_id") or change_id
    bindings["profile"] = profile["profile"]
    bindings["participants_profile_ref"] = ".governance/participants.yaml"
    steps = bindings.setdefault("steps", {})
    for item in profile["step_owner_matrix"]:
        steps[str(item["step"])] = {
            "owner": item["primary_owner"],
            "assistants": item["assistants"],
            "reviewer": item["reviewer"],
            "gate": item["gate"],
            "human_gate": item["human_gate"],
            "final_decision_owner": item["final_decision_owner"],
        }
    write_yaml(bindings_path, bindings)


def _format_matrix(payload: dict) -> str:
    lines = [
        "# Participants Matrix",
        "",
        f"Profile: {payload['profile']}",
        "",
        "## Participants",
    ]
    for participant in payload["participants"]:
        strengths = ", ".join(participant.get("strengths", []))
        lines.append(f"- {participant['id']} ({participant['type']}): {strengths}")
    lines.extend(["", "## 9-step owner matrix", ""])
    for item in payload["step_owner_matrix"]:
        assistants = ", ".join(item["assistants"]) or "none"
        lines.append(
            f"- Step {item['step']} / {item['label']}: owner={item['primary_owner']}; "
            f"assistants={assistants}; reviewer={item['reviewer']}; "
            f"human_gate={str(item['human_gate']).lower()}; final_decision={item['final_decision_owner']}"
        )
    return "\n".join(lines) + "\n"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

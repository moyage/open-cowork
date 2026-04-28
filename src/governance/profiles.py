from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


ADOPTION_PROFILES: dict[str, dict] = {
    "core": {
        "profile_version": "ocw.adoption-profile.v1",
        "profile_id": "core",
        "display_name": "Lightweight",
        "human_label": "轻量协作",
        "description": "低风险单人或单 Agent 工作的最小治理。",
        "selection_guidance": "Agent may choose this for low-risk solo work; humans only need to confirm that lightweight governance is acceptable.",
        "enabled_controls": [
            "deterministic_resume",
            "change_contract",
            "evidence",
            "verify",
            "review",
            "archive_carry_forward",
        ],
        "required_artifacts": ["contract", "bindings", "evidence", "verify", "review", "archive_receipt"],
        "defaults": {"context_pack_level": "minimal", "review_required": True},
        "prohibited": ["executor_final_self_review"],
    },
    "personal-multi-agent": {
        "profile_version": "ocw.adoption-profile.v1",
        "profile_id": "personal-multi-agent",
        "display_name": "Personal Multi-Agent",
        "human_label": "个人多 Agent 协作",
        "description": "一个人调度多个个人域 Agent 或 AI Coding 环境。",
        "selection_guidance": "Agent may choose this when one person uses several local or cloud Agents on the same project.",
        "enabled_controls": [
            "deterministic_resume",
            "participant_profiles",
            "compact_handoff",
            "reviewer_separation",
            "archive_carry_forward",
        ],
        "required_artifacts": ["contract", "bindings", "evidence", "verify", "review", "archive_receipt"],
        "defaults": {"context_pack_level": "standard", "review_required": True},
        "prohibited": ["executor_final_self_review", "runtime_session_as_governance_truth"],
    },
    "team-standard": {
        "profile_version": "ocw.adoption-profile.v1",
        "profile_id": "team-standard",
        "display_name": "Team Standard",
        "human_label": "团队标准协作",
        "description": "普通团队任务，明确参与者、审查者和接手摘要。",
        "selection_guidance": "Agent should default to this for normal team work unless risk or compliance requires stricter gates.",
        "enabled_controls": [
            "deterministic_resume",
            "participant_profiles",
            "step5_human_gate",
            "independent_review",
            "archive_carry_forward",
            "compact_handoff",
        ],
        "required_artifacts": ["contract", "bindings", "evidence", "verify", "review", "archive_receipt"],
        "defaults": {"context_pack_level": "standard", "review_required": True, "runtime_profile_required": "optional"},
        "prohibited": ["direct_step6_from_remote_channel", "executor_final_self_review"],
    },
    "team-strict": {
        "profile_version": "ocw.adoption-profile.v1",
        "profile_id": "team-strict",
        "display_name": "Team Strict",
        "human_label": "团队严格协作",
        "description": "发布、安全、数据、合规或影响面较大的团队任务。",
        "selection_guidance": "Agent may recommend this for release, security, data, compliance, or high-blast-radius work; humans approve the stricter overhead.",
        "enabled_controls": [
            "deterministic_resume",
            "participant_profiles",
            "strict_human_gates",
            "approval_provenance",
            "independent_review",
            "evidence_completeness",
            "compact_handoff",
        ],
        "required_artifacts": ["contract", "bindings", "evidence", "verify", "review", "archive_receipt"],
        "defaults": {"context_pack_level": "standard", "review_required": True},
        "prohibited": ["direct_step6_from_remote_channel", "executor_final_self_review", "unmanaged_hooks"],
    },
}


ADOPTION_ADD_ONS: dict[str, dict] = {
    "large-reference-set": {
        "add_on_id": "large-reference-set",
        "human_label": "大量资料阅读模式",
        "description": "Stackable internal mode for source-heavy work. It narrows recommended reads and adds compression checkpoints without changing the base collaboration profile.",
        "stackable_with": ["core", "personal-multi-agent", "team-standard", "team-strict"],
        "agent_selected": True,
    }
}


def list_adoption_profiles() -> list[dict]:
    return [
        {
            "profile_id": profile["profile_id"],
            "display_name": profile["display_name"],
            "human_label": profile["human_label"],
            "description": profile["description"],
            "selection_guidance": profile["selection_guidance"],
        }
        for profile in ADOPTION_PROFILES.values()
    ]


def get_adoption_profile(profile_id: str) -> dict:
    if profile_id not in ADOPTION_PROFILES:
        raise ValueError(f"unknown adoption profile: {profile_id}")
    return deepcopy(ADOPTION_PROFILES[profile_id])


def apply_adoption_profile(root: str | Path, profile_id: str, *, agent_id: str = "current-agent", preview: bool = False, force: bool = False) -> dict:
    paths = GovernancePaths(Path(root))
    profile = get_adoption_profile(profile_id)
    target_dir = paths.governance_dir / "profiles"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "adoption.yaml"
    existing = load_yaml(target) if target.exists() else {}
    result = {
        "profile_id": profile_id,
        "path": ".governance/profiles/adoption.yaml",
        "participant_profile_dir": ".governance/participants/",
        "preview": preview,
        "would_overwrite": bool(existing and existing != profile),
        "requires_force": bool(existing and existing != profile and not force),
    }
    if preview:
        return result
    if result["requires_force"]:
        raise ValueError("adoption profile already exists with different content; rerun with --force or --preview first")
    write_yaml(target, profile)
    _write_default_participant_profiles(paths, agent_id=agent_id)
    return {
        **result,
        "requires_force": False,
    }


def _write_default_participant_profiles(paths: GovernancePaths, *, agent_id: str) -> None:
    participants_dir = paths.governance_dir / "participants"
    participants_dir.mkdir(parents=True, exist_ok=True)
    normalized_agent_id = agent_id.strip() or "current-agent"
    defaults = [
        {
            "participant_version": "ocw.participant.v1",
            "participant_id": "human-sponsor",
            "participant_type": "human",
            "available_roles": ["sponsor", "final_decision_owner"],
            "review_eligibility": {"can_review_own_execution": False, "domains": ["governance"]},
            "authority": {
                "can_open_change": True,
                "can_approve_step5": True,
                "can_record_evidence": False,
                "can_archive": True,
            },
            "working_boundaries": {"allowed_paths": ["**"], "forbidden_paths": [".governance/archive/**"]},
        },
        {
            "participant_version": "ocw.participant.v1",
            "participant_id": normalized_agent_id,
            "participant_type": "agent",
            "primary_runtime": "current-agent-runtime",
            "available_roles": ["orchestrator", "executor", "verifier"],
            "review_eligibility": {"can_review_own_execution": False, "domains": ["docs", "python"]},
            "authority": {
                "can_open_change": True,
                "can_approve_step5": False,
                "can_record_evidence": True,
                "can_archive": False,
            },
            "working_boundaries": {"allowed_paths": ["src/**", "tests/**", "docs/**"], "forbidden_paths": [".governance/archive/**"]},
        },
    ]
    for participant in defaults:
        path = participants_dir / f"{participant['participant_id']}.yaml"
        if not path.exists():
            write_yaml(path, participant)

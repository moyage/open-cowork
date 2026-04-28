from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StepOutputRequirement:
    step: int
    label: str
    paths: tuple[str, ...]
    canonical: str


STEP_OUTPUT_REQUIREMENTS: tuple[StepOutputRequirement, ...] = (
    StepOutputRequirement(1, "Intent confirmation", ("intent-confirmation.yaml", "INTENT_CONFIRMATION.md", "intent.md"), "intent-confirmation.yaml"),
    StepOutputRequirement(2, "Requirements", ("requirements.md",), "requirements.md"),
    StepOutputRequirement(3, "Design", ("design.md",), "design.md"),
    StepOutputRequirement(4, "Task package", ("tasks.md",), "tasks.md"),
    StepOutputRequirement(5, "Execution baseline", ("BASELINE_REVIEW.md",), "BASELINE_REVIEW.md"),
    StepOutputRequirement(6, "Execution evidence", ("evidence/execution-summary.yaml",), "evidence/execution-summary.yaml"),
    StepOutputRequirement(7, "Verification report", ("VERIFY_REPORT.md", "verify.yaml"), "VERIFY_REPORT.md"),
    StepOutputRequirement(8, "Review report", ("REVIEW_REPORT.md", "review.yaml"), "REVIEW_REPORT.md"),
    StepOutputRequirement(9, "Final round report", ("FINAL_ROUND_REPORT.md", "archive-receipt.yaml"), "FINAL_ROUND_REPORT.md"),
)

_TEMPLATE_MARKERS = (
    "todo",
    "tbd",
    "template",
    "placeholder",
    "replace me",
    "fill in",
    "待补充",
    "占位",
    "模板",
)


def evaluate_step_output_contract(change_dir: Path, current_step: int) -> list[dict]:
    results = []
    for requirement in STEP_OUTPUT_REQUIREMENTS:
        if requirement.step > current_step:
            continue
        paths = [change_dir / item for item in requirement.paths]
        existing = [path for path in paths if path.exists()]
        selected = _select_reviewable(existing)
        status = "pass" if selected else "fail"
        message = f"Step {requirement.step} {requirement.label} output is reviewable"
        if not existing:
            message = f"Step {requirement.step} {requirement.label} required output is missing"
        elif not selected:
            message = f"Step {requirement.step} {requirement.label} required output is empty or template-like"
        results.append({
            "step": requirement.step,
            "name": f"step_{requirement.step}_required_output",
            "label": requirement.label,
            "status": status,
            "message": message,
            "canonical": requirement.canonical,
            "refs": [str(path.relative_to(change_dir)) for path in paths],
            "selected_ref": str(selected.relative_to(change_dir)) if selected else "",
        })
    return results


def _select_reviewable(paths: list[Path]) -> Path | None:
    for path in paths:
        if _reviewable(path):
            return path
    return None


def _reviewable(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8").strip()
    if len(text) < 12:
        return False
    lowered = text.lower()
    if lowered in {"{}", "[]"}:
        return False
    if len(text) < 120 and any(marker in lowered for marker in _TEMPLATE_MARKERS):
        return False
    return True

# Session Recovery Playbook (`Session compressed` / provider dropped)

## 1. When to Use

Use this playbook when your orchestrator/PM agent gets stuck with:
- repeated `Session compressed x times`
- then `Connection to provider dropped`
- and cannot continue runtime progression

## 2. Typical Root Cause Pattern

Most failures match a combined pattern:
1. lifecycle re-entry on already-closed rounds (`idle_post_close`)
2. duplicate context reads from both:
   - `.governance/changes/<same_change_id>/...`
   - `.governance/archive/<same_change_id>/...`
3. unbounded repository scans that exceed context budget

## 3. Recovery Commands

Run from project root:

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

The second command writes:
- `.governance/index/SESSION_RECOVERY_PACKET.yaml`

## 4. Mandatory Recovery Rules

1. If diagnosis returns `lifecycle_phase: idle_post_close`, do not re-run close on archived rounds.
2. Restrict reads to `recommended_read_set`.
3. Never read both `changes/` and `archive/` for the same `change_id` in one run.
4. Resume with the generated recovery packet as the compact context anchor.

## 5. Minimal Read-Set Strategy

- Always read first:
  - `.governance/index/maintenance-status.yaml`
  - `.governance/index/current-change.yaml`
- In post-close mode:
  - read only required files under `.governance/archive/<change_id>/`
- avoid full-repo scans unless explicitly required

## 6. Exit Criteria

Recovery is complete when:
1. `ocw --root . diagnose-session` no longer indicates close re-entry risk for the intended run path.
2. the orchestrator can complete one bounded progression run within context budget.
3. lifecycle state advances as expected with explicit artifacts.

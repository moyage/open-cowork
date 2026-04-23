# Quick Start

This guide helps teammates start using open-cowork quickly in their own local projects.

## 1. Install

```bash
python3 -m pip install -e .
```

## 2. Initialize Governance Runtime

Inside your target project root:

```bash
ocw --root . init
```

This creates the minimal `.governance/` runtime structure.

## 3. Check Runtime Status

```bash
ocw --root . status
```

## 4. Diagnose Session Instability (Optional)

If your PM/orchestrator agent hits long-session instability:

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

Use the generated packet as compact context for the next agent run.

## 5. Team Collaboration Starter Pattern

1. Keep existing coding tools unchanged.
2. Use open-cowork as governance layer only.
3. Store change, verification, and review artifacts under `.governance/`.
4. Keep execution and final review ownership separated.
5. Use evidence files as decision input, not chat-only claims.

## 6. Current CLI Scope

Implemented now:
- `init`
- `status`
- `diagnose-session`
- `session-recovery-packet`

Planned next:
- `propose`
- `change create`
- `contract`
- `run`
- `verify`
- `review`
- `archive`

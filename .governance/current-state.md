# open-cowork Current State

Project goal: 发布 v0.2.6 Agent-first adoption closure，清理发布前仓库状态，并为下一轮迭代保留清晰入口。
Lifecycle: idle
Last archived change: v0.2.6-agent-first-adoption-closure
Last archive at: 2026-04-24T12:20:28.390136+00:00
Current phase: Release cleanup / 发布整理
Current owner: maintainer-agent
Next recommended action: verify release artifacts, stage intended source files, then tag or publish v0.2.6 according to maintainer decision.
Need human decision: confirm whether to create a git tag / push / PR after local release validation.

## Completed / 已完成

- v0.2.6 implementation archived through Step 9.
- Hermes independent review approved the v0.2.6 implementation after follow-up fixes.
- Current repository version is `0.2.6`.
- Agent-first adoption, source-doc binding, hygiene/doctor, bounded handoff read sets, lifecycle guard, and evidence ref support are implemented.

## Read next / 下一步读取

- `README.md`
- `CHANGELOG.md`
- `docs/getting-started.md`
- `.governance/index/maintenance-status.yaml`
- `.governance/archive/v0.2.6-agent-first-adoption-closure/archive-receipt.yaml`

## Context budget / 上下文预算

- 不要默认全文读取 `docs/archive/**`。
- 归档材料只在追溯 source docs、review 或 archive receipt 时按路径读取。
- 使用 `ocw hygiene` / `ocw doctor` 区分 pending docs、cold archive docs 和 runtime generated files。

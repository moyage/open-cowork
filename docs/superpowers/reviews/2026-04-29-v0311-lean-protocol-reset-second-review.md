# v0.3.11 精简协议重置方案二次 Review

日期：2026-04-29

对象：

- `docs/superpowers/plans/2026-04-29-v0311-lean-protocol-reset.md`
- `docs/specs/08-v0311-lean-protocol-reset.md`

Review 参与方：

- Codex Subagent：`019dd78c-fbbc-73f2-8fcc-c7744a7f0ed6`
- Hermes 本地 Agent：`20260429_124401_b64b88`

## 结论

二次 Review 未发现阻断问题。

第一次 Review 中的主要阻断点已经被修订方案实质覆盖，包括默认文件集、授权证据模型、阶段枚举、closeout gate、旧版本 detect/migrate/cleanup/uninstall、上下文预算、压力测试、文档、dogfood 和 release gate。

建议进入源码实现阶段，但第一批实现必须先固化 `state.yaml` schema、bypass approval schema、role binding schema、review 状态组合、decision_needed 生命周期和统一枚举来源，再展开 CLI、迁移和文档实现。

## Codex Subagent Review 摘要

阻断问题：无。

高优先级问题：

- `state.yaml` schema 缺少显式 `compact plan` / `verification plan` 字段。
- `participant_initialization.bypass` schema 与测试要求不一致，缺少 `approval_evidence_ref`。
- `role_bindings` 形状偏抽象，需要固定 item schema。

建议优化：

- 增加第一次 Review 问题追踪表。
- phase、gate status、review decision、rule failure impact 应来自单一常量/枚举来源。
- 发布命令中的远端分支名应标注为示例，发布前按实际分支确认。
- grep 验证要允许迁移、兼容、废弃说明中的旧目录命中。

二次 Review 建议：

```text
建议进入源码实现阶段，但带一个前置条件：第一批实现应先固化 state.yaml schema、bypass approval schema 和 role binding schema，再展开 CLI/迁移/文档实现。
```

## Hermes Review 摘要

阻断问题：无。

Hermes 确认第一次 Review 的六类阻断点已经修复：

- 默认文件集包含 `agent-entry.md` 和 `templates/`。
- 授权模型不再依赖字符串前缀。
- 阶段模型与规格一致，`closeout` 已成为明确阶段和 gate。
- `state.yaml` schema 已从过薄状态扩展为可实现的权威结构。
- 协作者模型覆盖 sponsor、owner_agent、orchestrator、executor、reviewer、advisors。
- 迁移、清理、卸载已包含 receipt、git-tracked extra confirm、archive receipt conversion 和 `.gitignore` 更新。

高优先级问题：

- “按需读取集”对 `agent-playbook.md` 和 `templates/` 的表述需要收紧，避免误解为 `resume/status/preflight` 默认读取。
- `review.status` 与 `review.decision` 需要合法组合矩阵。
- `participant_initialization.role_bindings` 需要最小 item schema。
- `decision_needed` 需要明确 id、status、summary、requested_by、created_at、resolved 字段和 closeout 阻断规则。

建议优化：

- 每个实施任务增加规格章节引用。
- 增加 schema validation 层，统一校验 state、rules、evidence、ledger 和枚举。
- mixed layout 中 compact active state 与 legacy active change 冲突时必须阻断并请求人/团队裁决，不能自动合并。
- 增加跨运行入口语义一致性测试，同一 `state.yaml` 输入必须得到同一 gate decision。

二次 Review 建议：

```text
可以进入源码实现，但最好先完成上述文档级收口，避免实现阶段产生字段漂移。
```

## 已完成的方案收口

二次 Review 后，计划文档已补充：

- `active_round.plan`
- `active_round.verification_plan`
- `participant_initialization.role_bindings` item schema
- `participant_initialization.bypass.approval_evidence_ref`
- `review.status` / `review.decision` 合法组合矩阵
- `decision_needed` 生命周期
- `agent-playbook.md` / `templates/` 专项读取说明
- schema validation 与统一枚举要求
- mixed layout 冲突阻断规则
- 跨入口 gate decision 一致性测试
- 发布命令按实际分支确认的说明

## 后续进入实现阶段的前置要求

源码实现第一批必须先完成：

1. lean schema 与统一枚举。
2. schema validation。
3. gate validation。
4. role binding schema。
5. bypass approval schema。
6. review 状态组合校验。
7. decision_needed 阻断逻辑。
8. 跨入口 gate decision 一致性测试。

这些完成前，不应先实现迁移、发布或文档发布 gate。

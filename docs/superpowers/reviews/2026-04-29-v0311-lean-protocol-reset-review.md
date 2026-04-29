# v0.3.11 精简协议重置实施计划第三方 Review

审查对象：

- `docs/superpowers/plans/2026-04-29-v0311-lean-protocol-reset.md`

对照依据：

- `docs/specs/08-v0311-lean-protocol-reset.md`
- `.agent-state/tasks/v0311-lean-plan-hermes-review/execution-contract.json`

审查方：

- Codex Subagent：方案 Review，只读。
- Hermes Agent：真实本地 Agent Review，只读，Session `20260429_123718_340543`。

## 总结结论

当前中文实施计划方向正确，但不建议直接进入源码实现阶段。

两路 Review 均认为：计划已经覆盖了精简状态、bounded evidence、旧版迁移、门禁、外部规则、Review 分离等主骨架，但与规格文档仍存在多处结构性偏差。若现在进入实现，后续高概率出现“代码按计划实现完成，但与 v0.3.11 规格不一致”的返工。

建议先进入“方案修订与二次 Review”阶段。

## 阻断问题

### 1. 默认文件集合与默认读取集不一致

计划当前默认文件集合缺少：

- `.governance/agent-entry.md`
- `.governance/templates/`

规格中这两项属于 v0.3.11 默认布局的一部分，其中 `agent-entry.md` 还属于默认读取集。

影响：

- 可能破坏 Agent-first 接续入口。
- 无法证明 `resume`、`status`、`preflight` 只读取正确的 compact default read set。

修订方向：

- 将 `agent-entry.md` 纳入 lean path、init、resume/status/preflight 测试和文档更新。
- 明确 `templates/` 是默认布局组成部分，但不进入默认读取集，除非执行模板渲染。

### 2. 授权模型只有字符串前缀检查，不能防伪授权

计划目前主要通过 `human:*` 或 `team:*` 前缀判断授权来源。Review 认为这不足以满足“不能伪造人/团队授权”的要求，因为 Agent 仍可自行传入 `--by human:mlabs`。

影响：

- 这是核心治理漏洞。
- 无法满足强约束：不得伪造、模拟或事后补写授权。

修订方向：

授权记录至少应包含：

- `requested_by`
- `approved_by`
- `approval_source`
- `approval_channel`
- `approval_evidence_ref`
- `created_by`
- `created_at`
- `reason`

若没有外部 approval evidence，状态应进入 blocked，而不是通过前缀即授权。

### 3. 阶段模型与规格不一致，closeout gate 被弱化

计划采用：

- `scope`
- `plan`
- `implement`
- `verify`
- `review`

规格采用：

- `intent-scope`
- `plan-contract`
- `execute-evidence`
- `verify-review`
- `closeout`

影响：

- 阶段枚举、状态机、CLI、测试、跨 Agent 一致性都会出现歧义。
- 当前计划可能演变成 Review approve 后直接 close，缺少 closeout readiness、carry-forward、剩余风险、ledger closeout record 等硬门禁。

修订方向：

- 优先按规格阶段名实现。
- 若保留短命令别名，必须明确映射到规格阶段名，持久化状态只写规格枚举。
- `closeout` 必须作为显式 gate/status，而不是附属关闭条件。

### 4. `state.yaml` schema 过薄

计划示例只包含：

- protocol/version
- layout
- active_round
- phase
- collaborators
- constraints

规格要求还应覆盖：

- scope in/out
- participant initialization
- role bindings
- gates
- decision needed
- verify state
- review state
- closeout state
- external rules state
- carry-forward
- evidence refs

影响：

- 当前 schema 不足以支撑恢复、门禁、闭环和长周期接续。

修订方向：

- 在计划中补一个“最小权威 schema”章节。
- 后续任务、测试、CLI 均以该 schema 为准。

### 5. 协作者初始化模型过窄

计划只覆盖：

- owner
- executor
- reviewer
- observer

规格要求至少覆盖：

- sponsor
- owner agent
- orchestrator
- executor
- reviewer
- optional advisors
- 权限边界
- 输出责任
- Review 独立性要求
- 缺失角色与阻断状态

影响：

- 对个人域多 Agent、团队域多 Agent 的覆盖不足。
- 无法充分表达职责分离和团队授权边界。

修订方向：

- 增加 `participant_initialization` schema。
- 增加 required/missing roles。
- 增加 bypass 的授权、原因和影响范围，但 bypass 必须默认阻断且需外部授权。

### 6. 旧版本迁移、清理、卸载覆盖不足

计划已覆盖 detect、dry-run、confirm、cleanup、uninstall，但还不够。

规格还要求识别或处理：

- CLI/package 版本
- 项目协议版本
- active legacy change
- 未迁移 archive
- git-tracked 旧产物
- active change manifest/contract/verify/review/evidence index 的 compact 转换
- archive receipt 转换
- `.gitignore` 更新
- migration receipt
- cleanup receipt

影响：

- 旧项目升级路径不可审计。
- 清理动作存在破坏性风险。

修订方向：

- 任务 8 扩展为完整迁移测试矩阵。
- 所有破坏性动作必须有 receipt。
- git-tracked legacy files 必须要求额外确认。

## 高优先级问题

### 1. 外部规则 schema 不足

当前规则 schema 主要是 `id/kind/command/by`。规格要求还需表达：

- 适用阶段
- 失败影响：`blocking`、`warning`、`advisory`
- 暂停原因
- 暂停期限
- 影响范围
- active round 中 blocking rule 变更的更强授权要求

修订方向：

- 增加完整 rules schema。
- 增加 blocking failure、rule bypass、suspend expiry、scope 限制测试。

### 2. 防膨胀测试不足以证明长周期目标

计划中的 100 轮测试主要检查文件数，没有覆盖：

- close round
- ledger append
- multi-agent
- team domain
- 多项目
- cold history 不扫描
- 文件大小和行数预算

修订方向：

- 增加默认读取集 spy/mock 测试。
- 增加 `current-state.md < 200 行`、`state.yaml < 400 行` 等预算测试。
- 增加 ledger/evidence 大小阈值和 rotation warning。
- 增加多 Agent、多项目压力测试。

### 3. 有界阈值与规格不一致

计划写了 evidence 最近 200 条。规格实施决策是：

- evidence refs：1,000 refs 或 512 KB 警告。
- ledger：500 records 或 512 KB 警告。

修订方向：

- 以规格阈值为准，或先修订规格。
- 不允许计划与规格各写一套阈值。

### 4. 文档更新范围不闭合

规格要求更新：

- `README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/agent-playbook.md`
- `docs/glossary.md`
- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`

计划当前只覆盖部分 docs，并且因为本地已有修改暂不触碰 `.governance/AGENTS.md` 和 `.governance/agent-playbook.md`。

修订方向：

- 将“当前不碰本地修改”与“发布前必须 dogfood/update governance entry files”拆成不同阶段。
- 若发布前无法更新这些文件，应明确标记为 release blocker。

### 5. 发布步骤缺少人工授权 gate

计划已列出 tag、push、GitHub release，但没有足够突出“必须人明确授权”。

修订方向：

- 发布任务必须写成 release preparation。
- `git tag`、`git push`、`gh release create` 必须有人的明确发布授权后才能执行。

## 建议优化项

- 明确计划与规格的权威关系：若冲突，以 `docs/specs/08-v0311-lean-protocol-reset.md` 为准。
- 统一 CLI 命名策略：`ocw` 是否为主命令，`open-cowork` 是否为别名。
- 增加 legacy command shim matrix，列出旧命令如何映射、拒绝或要求 `--legacy-layout`。
- 增加个人域单 Agent、个人域多 Agent、团队域多 Agent 的端到端示例。
- 增加 open-cowork 仓库自身的 dogfood 迁移任务。
- 增加全局测试 fixture：默认流程中一旦创建 legacy heavy dirs 即测试失败。

## Gatekeeper 判断

Codex gatekeeper 判断：

- 这次 Review 有效。
- Hermes 是真实本地 Agent 调用，不是文本模拟。
- Codex Subagent 与 Hermes 的核心结论一致。
- 当前计划不得进入源码实现阶段。
- 下一步应先修订 `docs/superpowers/plans/2026-04-29-v0311-lean-protocol-reset.md`，使其与规格逐项对齐。
- 修订后应再做一次只读 Review，通过后再进入源码实现。

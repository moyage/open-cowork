# Agent-first 采用方式

open-cowork 默认面向 AI 时代的使用路径：

```text
人表达意图 -> Agent 调用 open-cowork -> open-cowork 维护结构化协作事实 -> Agent 向人反馈项目进展和决策点
```

它不假设人愿意离开 Agent 环境、阅读命令手册、再手动操作一串 CLI。CLI 存在，但默认由 Agent 调用。

## 人可以怎么说

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

```text
请按 open-cowork 的协同治理方式推进当前需求。
```

## Agent 应该怎么做

1. 识别目标项目和人的当前意图。
2. 检查 open-cowork 是否已经安装或可从本地仓库使用。
3. 如果目标项目还没有 `.governance/`，初始化它。
4. 先生成 adoption plan：目标、source docs、候选 change、bounded read set、role suggestions、active change lifecycle decision。
5. 让人确认个人域参与者和 9 步 owner / assistant / reviewer / human gate 矩阵。
6. 捕获并确认本轮真实意图：需求、优化、Bug、范围、非目标、风险和验收标准。
7. 在人确认目标、范围或 lifecycle policy 后，创建或准备当前 active change package。
8. 生成或补齐 contract 和 role bindings。
9. 生成目标项目内的 Agent 入口文件。
10. 用 step report 向人汇报当前项目目标、阶段、步骤、owner、阻断、下一步和需要人决策的事项。

v0.2.6 起，Agent 应先预览采用计划，再实际写入目标项目。这个动作属于 Agent 内部执行面；人只需要看到计划摘要、风险、参与者建议和需要确认的决策点。

如果有需求基线、dogfood 报告或审计报告，Agent 应把来源绑定到本轮采用计划，而不是把归档历史全文读进上下文。

v0.3.6 起，已实施项目推荐通过 `ocw resume` 接续；v0.3.5 起，已实施项目会生成 `.governance/agent-entry.md` 和 `.governance/index/active-changes.yaml`。任意 Agent 接手时必须先运行确定性 resume；如果同一项目存在多个并行需求，Agent 必须展示 active change 列表并让人选择要接续的需求，不得从聊天历史或自然语言关键词猜测。

v0.3.7 起，团队采用时由 Agent 推荐最小足够的协作模式：轻量协作、个人多 Agent 协作、团队标准协作或团队严格协作。人或团队只需要确认协作强度是否合适，不需要理解或填写内部 profile schema。大量资料阅读属于可叠加的内部模式，不是和团队标准 / 团队严格互斥的档位。

Agent 应用协作模式后，会在项目事实层记录成员/Agent 的职责边界。长任务、跨会话和跨 Agent 接手时，Agent 应生成接手资料索引和接手摘要；这些材料只提供“先读哪些材料”和压缩摘要，不能替代 intent、contract、bindings、verify、review 或 archive receipt 等权威事实。

v0.3.9 起，已启用 open-cowork 的项目必须先治理、后执行。Agent 收到开发任务后应先运行 activation / resume / preflight，确认 active change、contract、scope、Step 5 approval 和 Step 6 readiness；若 preflight 不允许修改项目文件，Agent 必须停止并汇报缺失项。先完成实现再询问是否补 open-cowork，不是正常流程；只能记录为 flow bypass recovery，并继续补齐缺失治理事实。

`change prepare` 只代表准备材料生成完成，不代表 Step 1-5 已完成；新 change 的默认运行位置应从 Step 1 开始。`intent confirm` 会满足 Step 1 approval；非阻塞步骤可以记录 acknowledgement；Step 8 应先记录独立 reviewer decision，再让人决定是否接受该 decision。

其他 participants、intent、step report、approve、review、archive 等命令属于 Agent 内部执行面，不应作为人类操作教程展示。对人的汇报应聚焦“谁负责、要做什么、是否确认、当前步骤能否推进、证据在哪里”，并明确说明 `gate_type`、`gate_state`、`approval_state`、review decision 和 acknowledgement。Human gate 的确认动作应尽量提供 `approve` / `revise` / `reject` 短选项，避免要求人输入长篇审批句。Step 8 review 应由独立 reviewer 完成，并记录真实 reviewer runtime evidence；reviewer mismatch 默认阻断，只有人明确接受 audited bypass，并记录 reason、recorded_by、evidence_ref 时才允许继续。若 review 返回 `revise`，Agent 应显式打开 revise loop，回到 Step 6 修订，而不是隐式跳过审查失败。

连续 dogfood 或多轮本地迭代时，Agent 应读取当前 change 的 `baseline.yaml`，向 reviewer 说明 parent archived change、dirty worktree baseline 和本轮 evidence delta 的区别。不要把上一轮已归档但未提交的 dirty baseline 自动判为本轮失败。

## 不应该怎么做

- 不要把采用过程变成人的命令教程。
- 不要把命令执行当成主要进度汇报。
- 不要在已启用 open-cowork 的项目中先改代码、再把 change package / contract / evidence 当成可选补录。
- 除非是真实项目决策，不要要求人选择内部 schema 值。
- 不要把 open-cowork 当成替代用户现有 Agent 或 IDE 的新 runtime。
- 不要默认全文扫描 `docs/archive/**`；先按接手摘要给出的建议读取顺序读取。
- 不要把接手资料索引当成新的权威事实源；它只是降低上下文成本的索引。

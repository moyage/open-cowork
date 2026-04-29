# Agent-first 采用方式

open-cowork 默认面向 AI 时代的使用路径：

```text
人表达意图 -> Agent 调用 open-cowork -> open-cowork 维护轻量协作事实 -> Agent 向人反馈项目进展和决策点
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
3. 初始化或升级 v0.3.11 lean protocol；若目标项目已有旧 heavy layout，由安装入口自动迁移并验证。
4. 生成或读取当前项目的 bounded read set。
5. 让人确认个人域参与者和 9 步 owner / assistant / reviewer / human gate 矩阵。
6. 捕获并确认本轮真实意图：需求、优化、Bug、范围、非目标、风险和验收标准。
7. 在人确认目标、范围或 lifecycle policy 后，创建或准备当前 round。
8. 生成或补齐 scope、role bindings、rules 和 evidence requirements。
9. 生成目标项目内的 Agent 入口文件。
10. 用状态摘要向人汇报当前项目目标、阶段、步骤、owner、阻断、下一步和需要人决策的事项。

v0.3.11 起，新项目默认不创建旧 heavy 布局。Agent 应围绕 `.governance/state.yaml`、`.governance/current-state.md`、`.governance/evidence.yaml`、`.governance/ledger.yaml` 和 `.governance/rules.yaml` 维护项目事实。大型输出写入默认读取集之外，只登记有界 evidence ref。

如果有需求基线、dogfood 报告或审计报告，Agent 应把来源绑定到本轮状态或 ledger，而不是把归档历史全文读进上下文。

Agent 在长任务中必须按 compact-resilient discipline 工作：只读 bounded read set；Hermes/OOSO/review/test 的完整输出写入文件；聊天中只保留 evidence ref、路径和短摘要；对大日志、session JSONL、cold history 使用定点读取或恢复 handoff。compact 或 stream 中断后，从恢复包和最后成功 evidence 继续，不重新打捞完整失败会话。

## 接手与并行需求

已实施项目推荐通过 `.governance/agent-entry.md` 接续。任意 Agent 接手时必须先运行确定性入口；如果同一项目存在多个并行需求，Agent 必须展示可接续需求并让人选择，不得从聊天历史或自然语言关键词猜测。

Agent 应用协作模式后，会在项目事实层记录成员/Agent 的职责边界。长任务、跨会话和跨 Agent 接手时，Agent 应生成接手资料索引和接手摘要；这些材料只提供“先读哪些材料”和压缩摘要，不能替代 state、scope、role bindings、verify、review 或 ledger 等权威事实。

已启用 open-cowork 的项目必须先治理、后执行。Agent 收到开发任务后应先运行 activation / status / preflight，确认当前 round、scope、Step 5 approval 和 Step 6 readiness；若 preflight 不允许修改项目文件，Agent 必须停止并汇报缺失项。先完成实现再询问是否补 open-cowork，不是正常流程；只能记录为 flow bypass recovery，并继续补齐缺失治理事实。

其他 participants、intent、step report、approve、review、closeout 等命令属于 Agent 内部执行面，不应作为人类操作教程展示。对人的汇报应聚焦“谁负责、要做什么、是否确认、当前步骤能否推进、证据在哪里”，并明确说明 gate、approval、review decision 和 acknowledgement。Human gate 的确认动作应尽量提供 `approve` / `revise` / `reject` 短选项，避免要求人输入长篇审批句。

Step 8 review 应由独立 reviewer 完成，并记录真实 reviewer runtime evidence；reviewer mismatch 默认阻断，只有人明确接受 audited bypass，并记录 reason、recorded_by、evidence_ref 时才允许继续。若 review 返回 `revise`，Agent 应显式打开 revise loop，回到 Step 6 修订，而不是隐式跳过审查失败。

连续 dogfood 或多轮本地迭代时，Agent 应读取 compact baseline，向 reviewer 说明 parent closeout、dirty worktree baseline 和本轮 evidence delta 的区别。不要把上一轮已收束但未提交的 dirty baseline 自动判为本轮失败。

## 旧版本项目处理

旧版本项目如果存在 heavy layout，Agent 应通过安装、初始化、setup 或 onboard 入口自动检测、迁移并验证，不要求人额外理解或执行迁移命令。旧历史移动到 cold history 后只作为追溯材料，不进入默认读取集。清理 cold history 和卸载治理文件属于破坏性动作，仍必须先 dry-run、再显式确认并写入 receipt，不能把 dry-run 文案说成已经物理删除。

## 不应该怎么做

- 不要把采用过程变成人的命令教程。
- 不要把命令执行当成主要进度汇报。
- 不要在已启用 open-cowork 的项目中先改代码、再把治理事实和 evidence 当成可选补录。
- 除非是真实项目决策，不要要求人选择内部 schema 值。
- 不要把 open-cowork 当成替代用户现有 Agent 或 IDE 的新 runtime。
- 不要默认全文扫描冷历史；先按接手摘要给出的建议读取顺序读取。
- 不要把接手资料索引当成新的权威事实源；它只是降低上下文成本的索引。
- 不要把 Hermes/OOSO 横幅、完整 diff、完整测试日志或完整 session 恢复内容直接灌进上下文。

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

v0.2.6 起，Agent 可以用下面的内部命令预览采用计划：

```bash
ocw --root . adopt --target . --goal "当前项目迭代目标" --dry-run
```

如果有需求基线、dogfood 报告或审计报告，Agent 应通过 `--source-doc` 绑定来源，而不是把归档历史全文读进上下文。

v0.3.4 起，`change prepare` 只代表准备材料生成完成，不代表 Step 1-5 已完成；新 change 的默认运行位置应从 Step 1 开始。`intent confirm` 会满足 Step 1 approval；非阻塞步骤可以记录 acknowledgement；Step 8 应先记录独立 reviewer decision，再让人决定是否接受该 decision。Step 5 / Step 8 / Step 9 approval 分别是执行、接受 review decision 和归档前的明确记录：

```bash
ocw --root . participants setup --profile personal --change-id <change-id>
ocw --root . intent capture --change-id <change-id> --project-intent "本轮真实迭代意图"
ocw --root . intent confirm --change-id <change-id> --confirmed-by human-sponsor
ocw --root . intent status --change-id <change-id> --format human
ocw --root . participants list --change-id <change-id> --format human
ocw --root . change status --change-id <change-id> --format human
ocw --root . step report --change-id <change-id> --step 1 --format human
ocw --root . step report --change-id <change-id> --step 5 --format human
ocw --root . step approve --change-id <change-id> --step 5 --approved-by human-sponsor
ocw --root . review --change-id <change-id> --decision approve --reviewer <independent-reviewer>
ocw --root . step approve --change-id <change-id> --step 8 --approved-by human-sponsor
ocw --root . step approve --change-id <change-id> --step 9 --approved-by human-sponsor
```

这些命令仍然是 Agent 的内部工具。对人的汇报应聚焦“谁负责、要做什么、是否确认、当前步骤能否推进、证据在哪里”，并明确说明 `gate_type`、`gate_state`、`approval_state`、review decision 和 acknowledgement。Human gate 的确认动作应尽量提供 `approve` / `revise` / `reject` 短选项，避免要求人输入长篇审批句。Step 8 review 应由独立 reviewer 完成，并记录真实 reviewer runtime evidence；reviewer mismatch 默认阻断，只有人明确接受 audited bypass，并记录 reason、recorded_by、evidence_ref 时才允许继续。若 review 返回 `revise`，Agent 应显式打开 revise loop，回到 Step 6 修订，而不是隐式跳过审查失败。

连续 dogfood 或多轮本地迭代时，Agent 应读取当前 change 的 `baseline.yaml`，向 reviewer 说明 parent archived change、dirty worktree baseline 和本轮 evidence delta 的区别。不要把上一轮已归档但未提交的 dirty baseline 自动判为本轮失败。

## 不应该怎么做

- 不要把采用过程变成人的命令教程。
- 不要把命令执行当成主要进度汇报。
- 除非是真实项目决策，不要要求人选择内部 schema 值。
- 不要把 open-cowork 当成替代用户现有 Agent 或 IDE 的新 runtime。
- 不要默认全文扫描 `docs/archive/**`；先读 adoption plan / handoff 给出的 recommended read set。

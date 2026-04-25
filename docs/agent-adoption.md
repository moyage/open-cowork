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

v0.2.7 起，Agent 应优先建立人的控制基线：

```bash
ocw --root . participants setup --profile personal --change-id <change-id>
ocw --root . intent capture --change-id <change-id> --project-intent "本轮真实迭代意图"
ocw --root . intent confirm --change-id <change-id> --confirmed-by human-sponsor
ocw --root . step report --change-id <change-id> --step 5
```

这些命令仍然是 Agent 的内部工具。对人的汇报应聚焦“谁负责、要做什么、是否确认、当前步骤能否推进”。

## 不应该怎么做

- 不要把采用过程变成人的命令教程。
- 不要把命令执行当成主要进度汇报。
- 除非是真实项目决策，不要要求人选择内部 schema 值。
- 不要把 open-cowork 当成替代用户现有 Agent 或 IDE 的新 runtime。
- 不要默认全文扫描 `docs/archive/**`；先读 adoption plan / handoff 给出的 recommended read set。

# 个人域多 Agent 试用指南

本指南面向团队成员在自己的本地项目中第一次试用 `open-cowork`。

这里的“个人域”指：同一个人使用多个 Agent、多个 AI Coding 工具、多个模型或多个 IDE/CLI，在一个本地项目中完成复杂任务的分析、设计、编码、验证、review 与接续。

`open-cowork` 不要求你统一工具链，也不要求你先进入团队多人协作。个人域单人多 Agent 是推荐的第一批试用场景。

## 1. 推荐结论

首次试用建议采用：

- 日常事务调度 Agent 或你最常用的主力 Coding Agent 负责安装与初始化；
- 每个具体 change 由一个“当前主控 Agent / Orchestrator”推进；
- 编码 Agent 只负责执行与落证据；
- 另一个 Agent 或同一 Agent 的独立 review 会话负责验证与审查；
- 人只在目标确认、风险确认、review 决策和 closeout 时介入。

也就是说，`open-cowork` 不绑定某个 Agent。只要某个 Agent 能在你的项目目录里运行 shell 命令、读写文件、遵守产物边界，它就可以完成安装、配置与流程推进。

## 2. 最小安装与激活

在任意一个你信任的 Coding Agent 会话中执行即可：

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/bootstrap.sh
source .venv/bin/activate
ocw --help
./scripts/smoke-test.sh
```

然后进入你要试用的个人项目：

```bash
cd /path/to/your-project
ocw --root . init
ocw --root . status
ocw --root . diagnose-session
```

如果你不想激活 venv，也可以直接使用 bootstrap 生成的命令路径，例如：

```bash
/path/to/open-cowork/.venv/bin/ocw --root . init
```

## 3. 个人域角色映射

个人域中可以一人多角，但不建议让同一个执行会话自审自批。

推荐最小角色如下：

| open-cowork 角色 | 个人域含义 | 常见承载者 |
| --- | --- | --- |
| Sponsor | 目标、范围、最终判断 | 人 |
| Orchestrator | 拆解、流程推进、状态维护 | 日常调度 Agent 或主力 Coding Agent |
| Analyst / Architect | 梳理需求、提出技术方案 | 擅长分析的 Agent / 模型组合 |
| Executor | 编码、修改文件、执行命令 | 主力 Coding Agent |
| Verifier | 跑测试、检查证据、发现缺陷 | 执行 Agent 或独立验证 Agent |
| Reviewer | 独立审查、交叉验证 | 另一个 Agent / 另一个会话 / 人 |
| Maintainer | closeout、archive、接续摘要 | Orchestrator 或人确认后的 Agent |

## 4. 五种个人域组合建议

### 场景 A：概要设计 + 主力编码 + 独立 review

环境：

- Antigravity + GPT-5：梳理解读和技术方案概要设计
- Claude Code：技术方案详细设计、编码、code review
- Antigravity：code review

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | Antigravity + GPT-5 |
| Analyst / Architect | Antigravity + GPT-5 |
| Executor | Claude Code |
| Verifier | Claude Code，必要时 Antigravity 复核 |
| Reviewer | Antigravity 独立 review 会话 |
| Sponsor | 人 |

推荐 sample：

```bash
ocw --root . init
ocw --root . change create scenario-a-demo-change --title "Scenario A personal multi-agent trial"
ocw --root . status
```

实践方式：

- 先让 Antigravity 生成目标、范围、风险和方案概要；
- 让 Claude Code 基于方案进行详细设计和实现；
- Claude Code 产出测试和执行证据；
- Antigravity 使用独立会话做 review；
- 人决定是否 archive 或继续增量迭代。

### 场景 B：日常调度 + 双主力 Coding Agent 交叉验证

环境：

- Openclaw：日常事务调度
- NanoClaw：简单任务、文字调研、文档输出
- Claude Code + claude mem + serena：复杂任务、方案设计、Reviewer
- Codex：复杂任务、方案设计、Reviewer

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | Openclaw |
| Analyst / Architect | Claude Code 与 Codex 双方案交叉验证 |
| Executor | Claude Code 或 Codex 中当前更适合的一方 |
| Verifier | 另一方 Coding Agent |
| Reviewer | Claude Code / Codex 交叉 review |
| Research / Docs | NanoClaw |
| Sponsor | 人 |

推荐 sample：

```bash
ocw --root . init
ocw --root . change create scenario-b-demo-change --title "Scenario B cross-review personal trial"
ocw --root . status
ocw --root . continuity digest
```

实践方式：

- Openclaw 负责创建 change、维护状态和提醒下一步；
- 复杂方案先让 Claude Code 与 Codex 各自输出技术方案；
- 人或调度 Agent 汇总成一个 contract；
- 一个 Agent 执行，另一个 Agent review；
- NanoClaw 可用于调研、文档整理和 closeout 初稿。

### 场景 C：日常调度 + Cursor 主力 + Antigravity review

环境：

- Openclaw：日常事务调度
- Cursor：主力 AI Coding，Claude Sonnet / Opus 4.6 / Codex / GPT-5.1
- Antigravity：复杂任务、方案设计、网页分析、Reviewer

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | Openclaw 或 Cursor 主控会话 |
| Analyst / Architect | Antigravity + Cursor |
| Executor | Cursor |
| Verifier | Cursor 测试会话 |
| Reviewer | Antigravity |
| Sponsor | 人 |

推荐 sample：

```bash
ocw --root . init
ocw --root . change create scenario-c-demo-change --title "Scenario C Cursor plus Antigravity trial"
ocw --root . status
ocw --root . diagnose-session
```

实践方式：

- Openclaw 或 Cursor 创建 change；
- Antigravity 做前置分析和外部资料确认；
- Cursor 执行实现与测试；
- Antigravity 独立 review；
- 人负责最终范围和取舍。

### 场景 D：日常调度 + Cursor Demo + Antigravity 交叉验证

环境：

- Openclaw：日常事务调度
- Cursor + Claude Sonnet / Opus 4.6：设计方案、评审、Demo
- Antigravity + Gemini / Claude：评审、交叉验证

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | Openclaw |
| Analyst / Architect | Cursor |
| Executor | Cursor |
| Verifier | Cursor 或 Antigravity |
| Reviewer | Antigravity |
| Demo / Acceptance | 人 + Cursor |

推荐 sample：

```bash
ocw --root . init
ocw --root . change create scenario-d-demo-change --title "Scenario D demo-oriented personal trial"
ocw --root . status
```

实践方式：

- Openclaw 维护 change 状态；
- Cursor 负责方案、实现和 Demo；
- Antigravity 做交叉验证；
- 人以 Demo 可用性和 review 结论决定是否 closeout。

### 场景 E：调度 Agent + 主力 Coding Agent + 辅助组合

环境：

- Openclaw / Hermes Agent：日常事务与 Agent 调度
- Codex：主力 AI Coding
- OOSO：OpenCode + OMOC + Superpowers + OpenSpec，辅助方案、规范、review 与交叉验证

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | Openclaw / Hermes Agent |
| Analyst / Architect | Codex + OOSO / OpenSpec |
| Executor | Codex 或 OpenCode |
| Verifier | Codex / Superpowers verification |
| Reviewer | OMOC / OpenSpec / Codex 独立会话 |
| Maintainer | Hermes Agent 或 Codex 在人确认后执行 closeout |
| Sponsor | 人 |

推荐 sample：

```bash
ocw --root . init
ocw --root . change create scenario-e-demo-change --title "Scenario E assisted governed change"
ocw --root . status
ocw --root . continuity digest
```

实践方式：

- Openclaw / Hermes 只负责调度与状态推进，不直接替代 reviewer 判断；
- Codex 作为主要执行者；
- OOSO 组合负责规范、方案辩论、review 或复杂验证；
- 若 session/context 出现压缩或 provider drop，优先运行：

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

## 5. 推荐的首次试用流程

第一轮不要追求完整复杂闭环，建议按三层逐步试：

### Level 1：只验证接入

```bash
ocw --root . init
ocw --root . status
ocw --root . diagnose-session
```

目标：确认命令可用、目录可写、个人项目不会被重型改造。

### Level 2：创建一个轻量 change

```bash
ocw --root . change create personal-demo --title "Personal domain pilot"
ocw --root . status
ocw --root . continuity digest --change-id personal-demo
```

目标：确认 open-cowork 可以描述当前任务状态，并把多 Agent 工作绑定到一个 change-id。此时如果 `contract.yaml` 还未补齐，`status / digest` 会显示 draft 指引，而不是要求你立刻跑完整主链。

### Level 3：contract ready 后尝试最小交接和复盘

当当前 change 的 `contract.yaml` 与 `bindings.yaml` 已经由主控 Agent 或人补齐后，再执行：

```bash
ocw --root . contract validate --change-id personal-demo
ocw --root . runtime-status --change-id personal-demo
ocw --root . timeline --change-id personal-demo
ocw --root . continuity handoff-package --change-id personal-demo
ocw --root . continuity increment-package --change-id personal-demo --reason "first personal pilot checkpoint" --segment-owner "current-agent" --segment-label "first-checkpoint"
ocw --root . continuity digest --change-id personal-demo
```

目标：确认当你从一个 Agent 切到另一个 Agent 时，有一份可读、可接续、可审查的上下文输入。

## 6. 不推荐的首次试用方式

- 一开始就要求所有 Agent 严格跑完整 `contract -> run -> verify -> review -> archive` 主链；
- 让执行 Agent 自己完成最终 review 并直接 archive；
- 把某个个人域工具写死成团队唯一标准；
- 把 open-cowork 当成 AI Coding Runtime 或 IDE 插件替代品；
- 每一步都产出大量长文档，而不是维护最小事实、证据和接续摘要。

## 7. 判断试用是否成功

一次个人域试用成功，不要求项目真的已经进入团队协作，只要求满足：

- 新项目可以在 5 分钟内完成 `bootstrap + init + status`；
- 任意一个 Agent 能围绕同一个 `change-id` 继续推进；
- 从一个 Agent 切换到另一个 Agent 时，接手者能通过 digest / handoff 理解当前状态；
- 人能看懂当前处于哪个阶段、下一步需要谁做什么；
- session 压缩或断裂时，可以生成恢复包，而不是只能回聊天记录里打捞上下文。

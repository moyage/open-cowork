# 快速开始与个人域试用

本指南是 `open-cowork` 的唯一上手入口，面向第一次试用的个人域使用者、团队成员和协作负责人。

目标不是一次学完全部概念，而是先用最低门槛把一个本地项目接入基本治理结构，并确认它不会替换你的现有 Agent、IDE、脚本或工作流。

## 1. 你需要准备什么

- Python 3.10+
- Git
- 一个可写的本地项目目录
- 任意一个能执行 shell、读写文件、遵守边界的 Agent 或 AI Coding 工具

## 2. 一键安装并初始化目标项目

如果你只是想快速试用，推荐先用一条命令完成安装、初始化、状态查看和 session 诊断：

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/quickstart.sh /path/to/your-project
```

`quickstart.sh` 会自动调用 `bootstrap.sh`，并在目标项目中执行：

- `ocw --root <project> init`
- `ocw --root <project> status`
- `ocw --root <project> diagnose-session`

这一步会创建最小 `.governance/` 结构和索引文件，不会强迫你改造现有仓库结构、CI/CD 或 Agent 工具链。

如果你不想在仓库根目录创建 `.venv`，可以指定虚拟环境目录：

```bash
OCW_VENV_DIR=/tmp/open-cowork-venv ./scripts/quickstart.sh /path/to/your-project
```

## 3. 手动安装路径

如果你希望分步骤执行，可以使用手动路径：

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
ocw --help
./scripts/smoke-test.sh
```

然后进入你要试用的目标项目根目录：

```bash
cd /path/to/your-project
ocw --root . init
ocw --root . status
ocw --root . diagnose-session
```

## 4. 个人域多 Agent 推荐用法

个人域中可以一人多角，但不建议让同一个执行会话自审自批。

推荐最小角色映射：

| open-cowork 角色 | 个人域含义 | 常见承载者 |
| --- | --- | --- |
| Sponsor | 目标、范围、最终判断 | 人 |
| Orchestrator | 拆解、流程推进、状态维护 | 日常调度 Agent 或主力 Coding Agent |
| Analyst / Architect | 梳理需求、提出技术方案 | 擅长分析的 Agent / 模型组合 |
| Executor | 编码、修改文件、执行命令 | 主力 Coding Agent |
| Verifier | 跑测试、检查证据、发现缺陷 | 执行 Agent 或独立验证 Agent |
| Reviewer | 独立审查、交叉验证 | 另一个 Agent / 另一个会话 / 人 |
| Maintainer | closeout、archive、接续摘要 | Orchestrator 或人确认后的 Agent |

关键原则：

- 安装和初始化可以由任意一个你信任的 Coding Agent 完成。
- 具体 change 最好有一个当前主控 Agent 负责推进状态。
- 编码 Agent 负责执行和落证据。
- Review 尽量由另一个 Agent、另一个会话或人来做。
- 人只在目标确认、风险确认、review 决策和 closeout 时介入。

## 5. 常见个人域组合样例

这些样例是匿名的工具组合模式，不代表团队成员身份。

### 场景 A：概要设计 + 主力编码 + 独立 review

适合组合：Antigravity + GPT-5 做概要设计，Claude Code 做详细设计和编码，Antigravity 独立 review。

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | Antigravity + GPT-5 |
| Analyst / Architect | Antigravity + GPT-5 |
| Executor | Claude Code |
| Verifier | Claude Code，必要时 Antigravity 复核 |
| Reviewer | Antigravity 独立 review 会话 |
| Sponsor | 人 |

```bash
ocw --root . init
ocw --root . change create scenario-a-demo-change --title "Scenario A personal multi-agent trial"
ocw --root . status
```

### 场景 B：日常调度 + 双主力 Coding Agent 交叉验证

适合组合：日常调度 Agent 负责推进状态，两个主力 Coding Agent 分别做方案、执行和交叉 review，轻量 Agent 做调研和文档整理。

推荐绑定：

| 角色 | 建议承载 |
| --- | --- |
| Orchestrator | 日常调度 Agent |
| Analyst / Architect | 两个主力 Coding Agent 双方案交叉验证 |
| Executor | 当前更适合的一方 |
| Verifier | 另一方 Coding Agent |
| Reviewer | 独立交叉 review 会话 |
| Research / Docs | 轻量调研或文档 Agent |
| Sponsor | 人 |

```bash
ocw --root . init
ocw --root . change create scenario-b-demo-change --title "Scenario B cross-review personal trial"
ocw --root . status
ocw --root . continuity digest
```

### 场景 C：日常调度 + IDE 主力 + 独立分析 review

适合组合：Openclaw 一类日常调度 Agent 管状态，Cursor 一类 IDE AI Coding 工具做执行，Antigravity 一类工具做分析和 review。

```bash
ocw --root . init
ocw --root . change create scenario-c-demo-change --title "Scenario C IDE plus independent review trial"
ocw --root . status
ocw --root . diagnose-session
```

### 场景 D：Demo 导向开发 + 交叉验证

适合组合：主力 IDE AI Coding 工具负责设计、实现和 Demo，辅助 Agent 负责交叉验证，人基于 Demo 可用性和 review 结论做 closeout 判断。

```bash
ocw --root . init
ocw --root . change create scenario-d-demo-change --title "Scenario D demo-oriented personal trial"
ocw --root . status
```

### 场景 E：调度 Agent + 主力 Coding Agent + 辅助组合

适合组合：调度 Agent 负责状态推进，Codex / Claude Code / OpenCode 等主力 Coding Agent 负责执行，OOSO / OMOC / OpenSpec / Superpowers 等组合负责方案辩论、规范、验证或 review。

```bash
ocw --root . init
ocw --root . change create scenario-e-demo-change --title "Scenario E assisted governed change"
ocw --root . status
ocw --root . continuity digest
```

## 6. 推荐首次试用流程

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

目标：确认 `open-cowork` 可以描述当前任务状态，并把多 Agent 工作绑定到一个 `change-id`。如果 `contract.yaml` 还未补齐，`status / digest` 会显示 draft 指引，而不是要求你立刻跑完整主链。

### Level 3：contract ready 后尝试交接和复盘

当当前 change 的 `contract.yaml` 与 `bindings.yaml` 已经由主控 Agent 或人补齐后，再执行：

```bash
ocw --root . contract validate --change-id personal-demo
ocw --root . runtime-status --change-id personal-demo
ocw --root . timeline --change-id personal-demo
ocw --root . continuity handoff-package --change-id personal-demo
ocw --root . continuity increment-package --change-id personal-demo --reason "first personal pilot checkpoint" --segment-owner "current-agent" --segment-label "first-checkpoint"
ocw --root . continuity digest --change-id personal-demo
```

目标：确认从一个 Agent 切换到另一个 Agent 时，有一份可读、可接续、可审查的上下文输入。

## 7. 团队试用最小约定

团队试用不要求统一本地工具链，但建议统一下面四件事：

- 每次协作都绑定一个 `change-id`。
- 每次执行都要落 evidence。
- 最终 review 不由 executor 自审自批。
- closeout 后再进入下一轮迭代。

首次团队试用建议仍从个人域开始，先让每个人在自己的本地项目上完成 `bootstrap + init + status`，再进入多人协作实践。

## 8. 常见问题

### 我只想先试，不想改现有流程？

先用 `open-cowork` 做旁路治理，不替换你现有 CI/CD、IDE 或 Agent 工作流。

### Agent 上下文爆炸怎么办？

优先生成结构化接续材料，再开启下一轮：

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

### 团队怎么统一口径？

先统一 change package、evidence schema、review gate 和 closeout 结构；暂时不要强制统一每个人的 Agent 或 IDE。

## 9. 不推荐的首次试用方式

- 一开始就要求所有 Agent 严格跑完整 `contract -> run -> verify -> review -> archive` 主链。
- 让执行 Agent 自己完成最终 review 并直接 archive。
- 把某个个人域工具写死成团队唯一标准。
- 把 `open-cowork` 当成 AI Coding Runtime 或 IDE 插件替代品。
- 每一步都产出大量长文档，而不是维护最小事实、证据和接续摘要。

## 10. 判断试用是否成功

一次个人域试用成功，不要求项目真的进入团队协作，只要求满足：

- 新项目可以在 5 分钟内完成 `bootstrap + init + status`。
- 任意一个 Agent 能围绕同一个 `change-id` 继续推进。
- 从一个 Agent 切换到另一个 Agent 时，接手者能通过 digest / handoff 理解当前状态。
- 人能看懂当前处于哪个阶段、下一步需要谁做什么。
- session 压缩或断裂时，可以生成恢复包，而不是只能回聊天记录里打捞上下文。

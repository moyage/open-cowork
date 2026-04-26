# 快速开始与个人域试用

本指南是 `open-cowork` 的唯一上手入口，面向第一次试用的个人域使用者、团队成员和协作负责人。

目标不是一次学完全部概念，而是先用最低门槛把一个本地项目接入基本治理结构，并确认它不会替换你的现有 Agent、IDE、脚本或工作流。

## 1. 默认入口：在 Agent 中说一句话

`open-cowork` 从 v0.2.5 开始把 Agent-first 作为默认使用方式；v0.2.6 起默认先生成 adoption plan；v0.2.7 起优先建立人的控制基线；v0.2.8 起把 Step 5 execution gate 接入默认推进流；v0.2.9 起进一步闭合 Step 8 review gate 和 Step 9 archive gate；v0.3.0 起把标准 Step 1-9、人类可读报告、gate 状态和归档收束审计链统一到默认协作体验。人不应该先去记命令，而应该先表达意图：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

或者：

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

你可以把这句话交给你当前个人域中的 Codex、Claude Code、Cursor、OpenClaw、Hermes、OMOC、Antigravity 或其他可信 Agent。

Agent 的职责是：理解当前项目目标，安装或定位 `open-cowork`，初始化目标项目，先生成 adoption plan，再准备当前 change，生成 contract / bindings / Agent handoff pack，并从 Step 1 开始向人汇报真实项目进展。`change prepare` 只表示准备材料已生成，不表示 Step 1-5 已完成。

## 2. 人应该看到什么反馈

Agent 不应该把命令清单当成主要汇报。推荐反馈格式是：

```text
当前项目推进状态

- 项目目标：
- 当前阶段：
- 当前步骤：
- 当前 Owner：
- 已完成：
- 当前阻断：
- 下一步建议：
- 需要你决策：
- Agent 后续动作：
```

人只需要在目标、范围、风险、review 决策和是否继续等真实判断点介入。

## 3. Agent 应该生成哪些项目入口

当 `open-cowork` 被应用到目标项目后，目标项目中应出现：

- `.governance/AGENTS.md`：给后续 Agent 的项目内入口。
- `.governance/current-state.md`：当前项目推进状态。
- `.governance/agent-playbook.md`：Agent 操作规则和人类汇报模板。
- `.governance/changes/<change-id>/contract.yaml`：执行边界。
- `.governance/changes/<change-id>/bindings.yaml`：角色和 owner 绑定。

这些文件的目的，是让下一个 Agent 不需要从聊天记录里猜项目状态。

## 4. Shell 备用路径：安装与初始化

如果你需要手动安装、排障，或帮助 Agent 定位工具，可以使用下面路径。

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/bootstrap.sh
source .venv/bin/activate
ocw version
./scripts/smoke-test.sh
```

在目标项目中初始化：

```bash
ocw onboard --target /path/to/your-project --mode quickstart --yes
```

`onboard` 会初始化 `.governance/`，输出状态和 session 诊断。它不会强迫你改造现有仓库结构、CI/CD 或 Agent 工具链。

如果你不想在仓库根目录创建 `.venv`，可以指定虚拟环境目录：

```bash
OCW_VENV_DIR=/tmp/open-cowork-venv ./scripts/quickstart.sh /path/to/your-project
```

## 5. 让 Agent 先生成 adoption plan

v0.2.6 推荐 Agent 先用 dry-run adoption plan 对齐目标、source docs、active change 生命周期和候选角色绑定，再决定是否写入 change package。

```bash
ocw --root /path/to/your-project adopt \
  --target /path/to/your-project \
  --goal "在当前项目中实施 open-cowork 协同治理框架" \
  --source-doc "docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md" \
  --agent Codex \
  --dry-run
```

adoption plan 应输出 bounded recommended read set。Agent 不应默认全文扫描 `docs/archive/plans/**`。

## 6. 建立人的控制基线

v0.3.0 推荐 Agent 在进入执行前先完成 Step 1-5 的真实确认链，并在 report/status 中展示 `gate_type`、`gate_state`、`approval_state`。在 review/archive 前继续显式记录 Step 8 和 Step 9 approval。它们仍然是 Agent 的内部工具；人看到的应该是“谁负责、做什么、是否确认、下一步能否推进”。

```bash
ocw --root /path/to/your-project participants setup \
  --profile personal \
  --change-id current-iteration

ocw --root /path/to/your-project intent capture \
  --change-id current-iteration \
  --project-intent "本轮真实迭代意图" \
  --requirement "需求项" \
  --acceptance "验收标准"

ocw --root /path/to/your-project intent confirm \
  --change-id current-iteration \
  --confirmed-by human-sponsor

ocw --root /path/to/your-project step report \
  --change-id current-iteration \
  --step 1 \
  --format human

ocw --root /path/to/your-project step report \
  --change-id current-iteration \
  --step 5 \
  --format human

ocw --root /path/to/your-project step approve \
  --change-id current-iteration \
  --step 5 \
  --approved-by human-sponsor
```

推荐在 Step 6 执行前至少确认：

- 9 步 owner / assistant / reviewer / human gate 是否符合当前个人域 Agent 组合；
- 本轮需求、优化、Bug、范围、非目标和验收标准是否清楚；
- 当前 step report 是否说明 owner、输入、输出、完成标准和需要人的决策。
- Human gate 是否提供 `approve` / `revise` / `reject` 这类短选项，避免确认动作歧义。
- Step 5 approval 是否已经记录，避免 Agent 静默进入执行。
- Step 8 / Step 9 approval 是否会在 review / archive 前明确记录；reviewer mismatch 默认会阻断，除非人明确接受 audited bypass，并记录 reason、recorded_by、evidence_ref。

## 7. 让 Agent 准备一个可执行 change

如果需要准备一个完整的个人域试用 change，Agent 可以使用 `pilot` 或 `change prepare`。这些命令是 Agent 的内部工具，不是人的默认任务清单。

```bash
ocw pilot \
  --target /path/to/your-project \
  --change-id "current-iteration" \
  --title "Current iteration" \
  --goal "在当前项目中试用 open-cowork 主链" \
  --scope-in "src/**" \
  --scope-in "tests/**" \
  --verify-command "<本项目测试命令>" \
  --yes
```

如果已经创建过 change，只补齐主链准备文件：

```bash
ocw --root /path/to/your-project change prepare current-iteration \
  --goal "在当前项目中试用 open-cowork 主链" \
  --scope-in "src/**" \
  --scope-in "tests/**" \
  --source-doc "docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md" \
  --verify-command "<本项目测试命令>"
```

这会填充：

- `intent.md`
- `requirements.md`
- `design.md`
- `tasks.md`
- `contract.yaml`
- `bindings.yaml`
- `.governance/AGENTS.md`
- `.governance/agent-playbook.md`
- `.governance/current-state.md`

## 8. 升级和干净重装

如果你已经安装过 V0.2.4 或更早版本，先在 `open-cowork` 仓库根目录执行：

```bash
git pull --ff-only
./scripts/update.sh
source .venv/bin/activate
ocw version
```

如果遇到旧 venv、旧命令路径或安装残留，使用干净重装：

```bash
git pull --ff-only
./scripts/bootstrap.sh --clean
source .venv/bin/activate
ocw version
./scripts/smoke-test.sh
```

排查当前 shell 是否还在使用旧版本：

```bash
which ocw
which open-cowork
ocw version
```

你也可以直接对 Agent 说：

```text
请帮我把本地 open-cowork 升级到最新版，并确认当前项目仍可正常使用这套协同治理框架。
```

## 7. 个人域多 Agent 推荐用法

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

## 8. 常见个人域组合样例

这些样例是匿名的工具组合模式，不代表团队成员身份。

### 场景 A：概要设计 + 主力编码 + 独立 review

适合组合：一个分析型 Agent 做概要设计，一个主力 Coding Agent 做详细设计和编码，再由分析型 Agent 的独立会话做 review。

### 场景 B：日常调度 + 双主力 Coding Agent 交叉验证

适合组合：日常调度 Agent 负责推进状态，两个主力 Coding Agent 分别做方案、执行和交叉 review，轻量 Agent 做调研和文档整理。

### 场景 C：日常调度 + IDE 主力 + 独立分析 review

适合组合：日常调度 Agent 管状态，IDE AI Coding 工具做执行，独立分析工具做方案复核和 review。

### 场景 D：Demo 导向开发 + 交叉验证

适合组合：主力 IDE AI Coding 工具负责设计、实现和 Demo，辅助 Agent 负责交叉验证，人基于 Demo 可用性和 review 结论做 closeout 判断。

### 场景 E：调度 Agent + 主力 Coding Agent + 辅助规范组合

适合组合：调度 Agent 负责状态推进，主力 Coding Agent 负责执行，辅助组合负责方案辩论、规范、验证或 review。

## 9. 推荐首次试用流程

### Level 1：只验证接入

Agent 应完成初始化、状态输出和 session 诊断。Shell 备用命令是：

```bash
ocw --root . init
ocw --root . status
ocw --root . diagnose-session
```

目标：确认命令可用、目录可写、个人项目不会被重型改造。

### Level 2：生成 adoption plan

Agent 应先生成当前任务的 adoption plan，并向人解释它对应的项目目标、source docs、已有 active change 风险和需要确认的角色绑定。Shell 备用命令是：

```bash
ocw --root . adopt --target . --goal "在当前项目中实施 open-cowork 协同治理框架" --dry-run
ocw --root . status
```

目标：确认 `open-cowork` 可以描述当前任务状态，并在写入 change package 前对齐边界和下一步。

### Level 3：准备可执行 change

Agent 应准备 contract、bindings 和 handoff pack。Shell 备用命令是：

```bash
ocw pilot --target . --change-id current-iteration --title "Current iteration" --goal "在当前项目中试用 open-cowork 主链" --scope-in "src/**" --scope-in "tests/**" --verify-command "<本项目测试命令>" --yes
```

目标：让执行 Agent 可以读取边界并开始受控执行。

### Level 4：contract ready 后尝试交接和复盘

当当前 change 的 `contract.yaml` 与 `bindings.yaml` 已经补齐后，再让 Agent 验证、生成接续包和 digest。Shell 备用命令是：

```bash
ocw --root . contract validate --change-id current-iteration
ocw --root . runtime-status --change-id current-iteration
ocw --root . timeline --change-id current-iteration
ocw --root . continuity handoff-package --change-id current-iteration
ocw --root . continuity digest --change-id current-iteration
ocw --root . hygiene
```

目标：确认从一个 Agent 切换到另一个 Agent 时，有一份可读、可接续、可审查的上下文输入。

## 10. 团队试用最小约定

团队试用不要求统一本地工具链，但建议统一下面四件事：

- 每次协作都绑定一个 `change-id`。
- 每次执行都要落 evidence。
- 最终 review 不由 executor 自审自批。
- closeout 后再进入下一轮迭代。

首次团队试用建议仍从个人域开始，先让每个人在自己的本地项目上完成 Agent-first 采用，再进入多人协作实践。

## 11. 常见问题

### 我只想先试，不想改现有流程？

先用 `open-cowork` 做旁路治理，不替换你现有 CI/CD、IDE 或 Agent 工作流。

### Agent 上下文爆炸怎么办？

优先生成结构化接续材料，再开启下一轮。Shell 备用命令是：

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

### 团队怎么统一口径？

先统一 change package、evidence schema、review gate 和 closeout 结构；暂时不要强制统一每个人的 Agent 或 IDE。

## 12. 不推荐的首次试用方式

- 一开始就要求所有 Agent 严格跑完整 `contract -> run -> verify -> review -> archive` 主链。
- 让执行 Agent 自己完成最终 review 并直接 archive。
- 把某个个人域工具写死成团队唯一标准。
- 把 `open-cowork` 当成 AI Coding Runtime 或 IDE 插件替代品。
- 让人先背命令、schema 和内部文件路径。
- 每一步都产出大量长文档，而不是维护最小事实、证据和接续摘要。

## 13. 判断试用是否成功

一次个人域试用成功，不要求项目真的进入团队协作，只要求满足：

- 新项目可以由 Agent 在 5 分钟内完成安装、初始化和当前状态输出。
- 任意一个 Agent 能围绕同一个 `change-id` 继续推进。
- 从一个 Agent 切换到另一个 Agent 时，接手者能通过 `.governance/AGENTS.md`、`.governance/current-state.md` 和 digest / handoff 理解当前状态。
- 人能看懂当前处于哪个阶段、下一步需要谁做什么。
- session 压缩或断裂时，可以生成恢复包，而不是只能回聊天记录里打捞上下文。

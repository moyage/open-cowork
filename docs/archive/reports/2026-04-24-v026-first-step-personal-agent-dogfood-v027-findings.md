# V0.2.6 第一条指令 Dogfood：V0.2.7 需求输入

日期：2026-04-24
模拟角色：团队成员个人域中的 Codex
用户提供的个人域环境：

- Agent 日常调度系统：Openclaw、Hermes agent
- AI Coding 环境：Codex（ChatGPT 5.5）、OOSO（Opencode + OMOC + Superpowers + Openspec）

用户第一条指令：

```text
根据这个Open-cowork项目（https://github.com/moyage/open-cowork ）的指引，进行安装和配置，在我当前的个人域环境中针对Open-cowork这个项目的迭代实施这套框架的规范和流程
```

约束：本次模拟只基于用户提供的预设背景与指令，不额外补充团队背景、工具关系或目标范围。

## 1. 第一条指令真实执行过程

### 1.1 识别当前项目与仓库状态

执行：

```bash
pwd
git status --short --branch
git remote -v
git log --oneline --decorate -3
```

观察：

- 当前目录是 `/Users/mlabs/Programs/open-cowork`。
- 远端是 `https://github.com/moyage/open-cowork.git`。
- 当前版本在 `main`，HEAD 为 `v0.2.5`。
- 工作区已有未跟踪文件：
  - `.governance/AGENTS.md`
  - `.governance/agent-playbook.md`
  - `.governance/current-state.md`
  - `docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md`
  - `docs/archive/reports/2026-04-24-v025-agent-first-dogfood-findings.md`

团队成员视角反馈：

- 第一眼就看到仓库不是干净状态，但不知道这些文件是框架应提交的协作入口、运行时产物，还是上一轮测试残留。
- 对首次试用者来说，这会直接削弱“可以放心安装和配置”的信心。

### 1.2 读取项目指引

读取：

- `AGENTS.md`
- `README.md`
- `docs/getting-started.md`
- `docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md`

观察：

- 文档明确说默认入口是 Agent-first，人可以只说一句话。
- 但落地时仍需要 Agent 自己推导：目标项目、change-id、goal、scope-in、verify-command、active change 策略。
- V0.2.6 需求文档已经列出这些问题，但当前版本还没有解决。

团队成员视角反馈：

- 项目理念能理解，但“我说一句话以后具体发生什么”仍不透明。
- 对当前个人域组合（Openclaw / Hermes / Codex / OOSO），文档没有给出如何分工落地：谁做 orchestrator、谁维护状态、谁 review、谁 archive。

### 1.3 执行安装

执行：

```bash
./scripts/bootstrap.sh
```

结果：

- bootstrap 完成。
- 输出提示：`local pip/setuptools does not support editable pyproject installs. Creating a local ocw shim instead.`
- 安装完成后提示：
  - `source "/Users/mlabs/Programs/open-cowork/.venv/bin/activate"`
  - `ocw --help`
  - `open-cowork --help`
  - `ocw --root . init`
  - `ocw --root . status`

团队成员视角反馈：

- `local pip/setuptools does not support editable pyproject installs` 很容易被理解成安装不完整或降级失败。
- 安装完成后仍然把人带回命令清单，与 README 的 Agent-first 承诺不一致。
- 对“个人域 Codex 正在帮我安装”这个场景来说，用户更想看到“当前安装状态、是否可用、下一步我是否需要决策”，而不是一串命令。

### 1.4 检查版本、状态和 session 诊断

执行：

```bash
./bin/ocw version
./bin/ocw --root . status
./bin/ocw --root . diagnose-session
```

结果：

- 版本是 `open-cowork 0.2.5`。
- `status` 显示当前阶段是 Phase 3 / Step 7。
- 但 `project_summary` 仍显示 Step 5：`Confirm contract.yaml and bindings.yaml are acceptable.`
- `diagnose-session` 发现 full scan 约 288k tokens，推荐 read set 约 1508 tokens。

团队成员视角反馈：

- `status` 同时显示 Step 7 和 Step 5，会让人不知道当前到底在哪一步。
- session 诊断很有价值，但它没有自动约束后续读取行为，也没有自然地进入 Agent handoff pack。
- 作为用户，我不知道 Codex 下一步应该继续 Step 7、回到 Step 5，还是先处理上下文预算问题。

### 1.5 执行 onboard

执行：

```bash
./bin/ocw onboard --target . --mode quickstart --yes
```

结果：

- onboard 完成。
- 输出仍然是 `Next commands you can run:`。
- 建议执行：
  - `change create personal-demo`
  - `status`
  - `continuity digest --change-id personal-demo`
- 但当前项目并没有 active change `personal-demo`。

团队成员视角反馈：

- 这一步明显退回 CLI-first。
- 固定的 `personal-demo` 会误导 Agent，也会误导人。
- 如果我只是说“请根据项目指引安装和配置”，我不希望看到一个与当前项目迭代无关的 demo change 建议。

### 1.6 尝试按“一句话”方式启动 pilot

执行：

```bash
./bin/ocw pilot --target . --yes
```

结果：

- 命令失败，提示缺少必填参数 `--goal`。

团队成员视角反馈：

- README 说人可以一句话，但当前工具没有一个对应的自然语言入口。
- Agent 必须自己把一句话拆成 `change-id/title/goal/scope/verify-command`，这意味着 open-cowork 还没有真正承接“一句话实施”的关键能力。
- 这不是人不会用，而是工具还没有提供适合 Agent 调用的 adoption 层。

### 1.7 检查 continuity digest 与 current-state

执行：

```bash
./bin/ocw --root . continuity digest --change-id dogfood-v025-agent-first
sed -n '1,140p' .governance/current-state.md
```

结果：

- `digest` 仍显示 `step5-prepared / Phase 2`。
- `status` 显示 Phase 3 / Step 7。
- `.governance/current-state.md` 仍显示 Step 5。

团队成员视角反馈：

- 这会让 Agent 接手时读到错误状态。
- 人看到不同入口给出不同状态，会认为流程没有闭环。
- 这是比文档体验更严重的信任问题：框架自己的事实层不一致。

## 2. 第一条指令暴露的问题

### V027-F001：Agent-first 入口和实际命令入口之间缺少 adoption 层

现象：

- 人的一句话无法直接被 open-cowork CLI 承接。
- `ocw pilot --target . --yes` 仍要求 `--goal`。
- `change-id/title/scope/verify-command` 都需要 Agent 自己推导。

影响：

- 团队成员看到的是“文档说一句话，实际需要 Agent 自己拼命令”。
- 不同 Agent 会生成不同参数，造成协作口径漂移。

V0.2.7 需求：

- 提供真正的 Agent adoption 入口，例如 `ocw adopt --target . --goal "..."`。
- 支持从自然语言目标生成 adoption plan。
- 支持 `--dry-run`、`--format json`、`--confirm`，方便 Agent 先向人汇报再执行。

优先级：P0

### V027-F002：安装完成后的反馈仍是命令清单，不是 Agent-first 状态摘要

现象：

- `bootstrap.sh` 成功后输出多条命令。
- 没有输出“安装状态、目标项目状态、下一步由 Agent 做什么、是否需要人决策”。

影响：

- 人仍然感觉自己需要懂命令。
- Agent 可以继续，但用户体验没有从 CLI-first 真正切换。

V0.2.7 需求：

- bootstrap/update/onboard 输出应提供 Agent-readable + human-readable 的状态摘要。
- 命令清单可保留为 fallback，但不能作为主反馈。

优先级：P1

### V027-F003：bootstrap shim fallback 文案容易让人误解为安装失败

现象：

- 输出：`local pip/setuptools does not support editable pyproject installs. Creating a local ocw shim instead.`

影响：

- 对非 Python 工具链用户来说，这像是失败或降级。
- 用户不知道 shim 是否等价可用、是否影响后续升级。

V0.2.7 需求：

- 改写安装反馈：明确“已安装为本地 shim，可正常使用”。
- 如需保留技术细节，应放在诊断段落，不作为主状态。

优先级：P2

### V027-F004：已有工作区产物让首次试用者无法判断仓库是否干净

现象：

- 第一眼 `git status` 出现 `.governance/AGENTS.md`、`.governance/current-state.md`、V0.2.6 需求文件等 untracked。

影响：

- 团队成员无法判断这些是必须提交、应忽略、还是临时残留。
- 这会影响后续 review、commit、archive 决策。

V0.2.7 需求：

- open-cowork 应提供 `ocw hygiene` 或 `ocw doctor`，明确哪些文件是 runtime、哪些是 pending docs、哪些建议提交。
- `.governance` generated handoff 文件需要明确 gitignore/commit 策略。

优先级：P1

### V027-F005：onboard 仍建议不存在的 `personal-demo`

现象：

- `onboard` 后输出 `continuity digest --change-id personal-demo`。
- 当前项目没有该 change。

影响：

- 新 Agent 如果照做会失败。
- 人会觉得工具在给“示例命令”，不是在处理当前真实项目。

V0.2.7 需求：

- onboard 必须基于真实 current change 输出下一步。
- 没有 active change 时，输出“尚未创建 change”，而不是虚构 demo ID。

优先级：P0

### V027-F006：status、current-state、digest 三个入口状态不一致

现象：

- `status`：Phase 3 / Step 7。
- `current-state.md`：Phase 2 / Step 5。
- `continuity digest`：`step5-prepared / Phase 2`。

影响：

- Agent 接手时会读到错误状态。
- 人无法判断当前流程是否真的被治理。
- 这是事实层可信度问题。

V0.2.7 需求：

- 所有状态入口必须由同一 projection 生成，或在输出中明确 stale。
- 每次 run/verify/review/archive 后自动刷新 current-state 和 digest projection。
- 增加一致性测试。

优先级：P0

### V027-F007：diagnose-session 给出 read set，但没有转化为 Agent 行为约束

现象：

- diagnose-session 明确 full scan 超预算，推荐 read set 约 1508 tokens。
- 但 AGENTS/current-state/onboard 输出没有强制或引导 Agent 使用该 read set。

影响：

- Agent 仍可能全仓扫描，触发 context 压缩或 provider drop。
- 用户之前遇到的 Hermes session 爆炸问题仍可能复现。

V0.2.7 需求：

- 将 recommended read set 写入 `.governance/current-state.md` 或 `.governance/AGENTS.md`。
- 在 diagnose-session 判定超预算时，onboard/pilot/adopt 输出必须给出 bounded context 模式。

优先级：P1

### V027-F008：个人域多 Agent 组合没有进入角色绑定

现象：

- 用户明确提供个人域环境：Openclaw、Hermes、Codex、OOSO。
- 当前 open-cowork 没有询问或识别这些工具如何映射到 Sponsor/Orchestrator/Executor/Reviewer/Maintainer。
- 生成的 role binding 仍是 `orchestrator-agent`、`executor-agent` 等通用占位。

影响：

- 对团队成员来说，“我的个人域组合如何落到框架里”仍需要自己理解和配置。
- open-cowork 没有把用户最关键的上下文转化为协作事实。

V0.2.7 需求：

- adoption plan 应允许 Agent 记录个人域 agent/tool inventory。
- 支持从用户提供的组合映射角色建议，例如：Openclaw/Hermes 可作为 orchestrator 候选，Codex/OOSO 可作为 executor/reviewer 候选。
- 该映射需要人确认后写入 bindings。

优先级：P1

### V027-F009：V0.2.6 需求输入没有被自动识别为当前迭代来源

现象：

- 用户指出需求来源之一是 `docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md`。
- 当前 open-cowork 没有命令把该文档登记为 change source / requirement source。

影响：

- Agent 只能靠聊天上下文记住该文件重要。
- 后续 change package 可能没有明确引用需求来源。

V0.2.7 需求：

- `ocw adopt/change prepare` 支持 `--source-doc`。
- 生成的 intent/requirements/contract 应引用 source docs。
- status/digest 应显示当前 change 的需求来源。

优先级：P1

## 3. 第一条指令后的团队成员反馈

作为团队成员，我的第一步体验是：

1. 项目定位和 README 让我相信这是 Agent-first 的框架。
2. 但真实执行时，Codex 仍要在多个命令之间摸索，且需要自行补齐大量参数。
3. 安装能完成，但输出仍偏工程工具，不像“个人域 Agent 帮我完成了配置”。
4. 当前项目状态出现多处冲突，我不知道该信 `status`、`current-state` 还是 `digest`。
5. 我提供了个人域 Agent 组合，但框架没有把这组信息转成 role binding 或实施建议。
6. 我能感受到 open-cowork 的方向是对的，但第一步还没有真正做到“人一句话，Agent 闭环实施”。

## 4. 建议纳入 V0.2.7 的第一批需求

P0：V027-F001、V027-F005、V027-F006

P1：V027-F002、V027-F004、V027-F007、V027-F008、V027-F009

P2：V027-F003

## 5. 本次第一步结论

这次第一条指令没有失败在“能不能安装”，而是失败在“安装和实施之间缺少真正的 Agent-first adoption 层”。

对于用户来说，问题不是命令跑不起来，而是：我已经把意图告诉了个人域 Codex，也告诉了我的个人域 Agent 组合，但 open-cowork 还不能把这些自然语言和环境信息自动转成受控的 change、bindings、状态面和下一步闭环。

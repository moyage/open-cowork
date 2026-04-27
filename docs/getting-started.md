# 快速开始与个人域试用

本指南面向第一次试用 open-cowork 的个人域使用者、团队成员和协作负责人。目标不是让人学习一套 CLI，而是让 Agent 能把项目意图、范围、执行证据、review 和接续状态维护成可审计的项目事实。

## 1. 默认入口

你可以直接对当前可信 Agent 说：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

或者：

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

Agent 的职责是理解项目目标，安装或定位 open-cowork，初始化 `.governance/`，准备当前 change package，并用人能理解的话汇报当前步骤、owner、阻断、下一步和需要你决策的事项。

## 2. 已实施项目如何接续

如果项目已经实施过 open-cowork，新会话或另一个 Agent 应先做项目激活检查。Agent 会在内部选择或确认当前 change，然后读取目标项目中的：

- `.governance/AGENTS.md`
- `.governance/current-state.md`
- `.governance/index/active-changes.yaml`
- `.governance/open-cowork-skill.md`
- `.governance/agent-playbook.md`
- 当前 change 的 `contract.yaml`
- 当前 change 的 `bindings.yaml`
- 当前 step report

不要从聊天历史或历史 archive 里重新猜状态。

如果同一个项目里同时有需求 1 和需求 2，人的说法应该是：

```text
请用 open-cowork 接续需求 1 的 change。
```

或者：

```text
请查看这个项目当前有哪些 active changes，并接续我指定的那个。
```

## 3. 人应该看到什么

Agent 不应该把命令清单当成主要汇报。推荐汇报形状是：

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

人只需要在目标、范围、风险、执行批准、review 决策和是否归档等真实判断点介入。

## 4. 9 步主链

| Step | 名称 | 人类判断点 |
| --- | --- | --- |
| 1 | 明确意图 / Clarify intent | 目标、背景和输入是否说清楚。 |
| 2 | 确定范围 / Lock scope | 要做什么、不做什么、验收标准是什么。 |
| 3 | 方案设计 / Shape approach | 方案、风险和取舍是否可接受。 |
| 4 | 组装变更包 / Assemble change package | 需求、方案、任务和边界是否装进同一工作单元。 |
| 5 | 批准开工 / Approve execution | 是否允许进入真实执行。 |
| 6 | 执行变更 / Execute change | Agent 是否在 contract 范围内执行并记录 evidence。 |
| 7 | 验证结果 / Verify result | 状态验证和产品验证证据是否清楚。 |
| 8 | 独立审查 / Independent review | 接受、要求修订或拒绝 reviewer decision。 |
| 9 | 归档接续 / Archive and handoff | 是否归档，并把接续状态留给下一轮。 |

`intent confirm` 会满足 Step 1 approval。非阻塞 step 可以记录 human acknowledgement，例如 Step 4 的任务拆解确认。Step 8 的 review decision 可以先记录，之后再由人决定是否接受该 decision。

## 5. Shell 备用路径

Shell 只用于安装、排障或帮助 Agent 定位工具。普通人只需要知道有两类备用动作：

- 安装 / 更新 open-cowork。
- 检查当前机器上的 open-cowork 版本和路径。

这些动作由 Agent 执行和汇报结果。不要把安装命令、初始化命令和诊断命令当成人的日常任务清单。

## 6. 准备一个可执行 change

Agent 会生成或补齐当前 change 的主链材料：

- `intent.md`
- `requirements.md`
- `design.md`
- `tasks.md`
- `contract.yaml`
- `bindings.yaml`
- `.governance/AGENTS.md`
- `.governance/agent-playbook.md`
- `.governance/current-state.md`

如果 change 已经有 intent 或 contract，`change prepare` 可以复用已有目标；只有完全没有 goal 来源时才需要补充目标。

## 7. 个人域多 Agent 建议

个人域中可以一人多角，但不建议让同一个执行会话自审自批。

| open-cowork 角色 | 个人域含义 | 常见承载者 |
| --- | --- | --- |
| Sponsor | 目标、范围、最终判断 | 人 |
| Orchestrator | 拆解、流程推进、状态维护 | 日常调度 Agent 或主力 Coding Agent |
| Executor | 编码、修改文件、执行命令 | 主力 Coding Agent |
| Verifier | 跑测试、检查证据、发现缺陷 | 执行 Agent 或独立验证 Agent |
| Reviewer | 独立审查、交叉验证 | 另一个 Agent / 另一个会话 / 人 |
| Maintainer | closeout、archive、接续摘要 | Orchestrator 或人确认后的 Agent |

关键原则：

- 安装和初始化可以由任意可信 Coding Agent 完成。
- 当前 change 最好有一个主控 Agent 推进状态。
- Review 尽量由另一个 Agent、另一个会话或人完成。
- 人只在目标确认、风险确认、review 决策和 closeout 时介入。

## 8. 三类典型落地场景

### 场景 A：个人域单一 Agent 系统

适合一个人长期主要使用一个 AI Coding 环境的情况，例如只用 Codex 或只用 Claude Code 推进项目。

open-cowork 在这个场景里的重点是：

- 把需求、范围、任务拆解、执行边界和验证结果沉淀到项目事实中。
- 让同一个 Agent 在新会话中可以从 `.governance/current-state.md` 和当前 change 接续。
- 把长任务拆成可审查、可恢复、可归档的 increment。
- 避免“任务做到一半，聊天上下文没了就只能重讲一遍”。

人的自然语言入口：

```text
请用 open-cowork 管理这个项目当前需求，后续新会话也要能接续。
```

### 场景 B：本地个人域多个 Agent 系统调度协同

适合一个人同时使用 Codex、Claude Code、Hermes、OMOC / OpenCode、OpenClaw 等多个本地 Agent 的情况。

open-cowork 在这个场景里的重点是：

- 项目是协作中心，不是某个 Agent 的私有会话。
- 所有 Agent 接手前都读取 `.governance/open-cowork-skill.md`。
- 多个需求可以同时存在于 `.governance/index/active-changes.yaml`。
- Agent 必须显式选择或确认 change_id，不能从聊天历史猜测。
- Executor、Verifier、Reviewer 可以由不同 Agent 或不同会话承担。

人的自然语言入口：

```text
Codex 正在做需求 1；请让 Claude Code 按 open-cowork 接续需求 2，并先确认 active changes。
```

### 场景 C：团队多人域协作

适合多名团队成员各自拥有不同个人域 Agent、AI Coding 环境和工作习惯的情况。

open-cowork 在这个场景里的重点是：

- 不强制统一 runtime、IDE、Agent 或工作台。
- 用项目级 contract 对齐范围、允许动作和禁止动作。
- 用 bindings 明确 owner、assistant、reviewer 和 human gate。
- 用 evidence / verify / review 让协作结果可追溯。
- 用 archive / continuity 让项目可以跨人、跨 Agent、跨阶段持续推进。

人的自然语言入口：

```text
请按 open-cowork 的团队协作方式推进这个项目，让不同成员的 Agent 都能从项目事实接续。
```

## 9. 项目级 Skill 使用方式

`.governance/open-cowork-skill.md` 是目标项目里的 Agent 接手说明。它适合以下情况：

- 新会话不知道旧会话进度。
- 另一个 Agent 要接手同一项目。
- 同一项目里有多个 active changes。
- 团队成员希望自己的本地 Agent 按同一套流程工作。

使用方式很简单：让 Agent 先读取这个文件，再做 activation，并只读取 activation 给出的 recommended read set。

人的自然语言入口：

```text
这个项目已经实施 open-cowork，请按项目里的 open-cowork 接手规则接续当前需求。
```

如果项目里有多个并行需求，可以说：

```text
请先列出这个项目当前正在进行的 open-cowork 需求，我选择后再接续。
```

如果 Agent 环境支持自定义 Skill，也可以把该文件内容注册成项目级 Skill；如果不支持，直接作为项目内接手文档读取即可。

## 10. 上下文压缩或中断恢复

如果会话过长、自动压缩失败或 Agent 中断，优先让 Agent 生成结构化恢复包。

如果有 Codex session jsonl，可以让 Agent 带上 `--session-log`，恢复包会记录 remote compact、最后 token 计数和最后错误事件。

恢复时只读取恢复包的 recommended read set，不要重新全文扫描仓库历史和 archive。

## 11. 判断试用是否成功

一次个人域试用成功，不要求项目立刻进入复杂团队协作，只要求满足：

- Agent 能在几分钟内完成安装、初始化和当前状态输出。
- 任意一个 Agent 能围绕同一个 `change-id` 继续推进。
- 从一个 Agent 切换到另一个 Agent 时，接手者能通过 `.governance/AGENTS.md`、`.governance/current-state.md` 和 handoff / digest 理解状态。
- 人能看懂当前处于哪个阶段、下一步需要谁做什么。
- session 压缩或断裂时，可以生成恢复包，而不是只能回聊天记录里打捞上下文。

## 12. 不推荐的首次试用方式

- 让人先背命令、schema 和内部文件路径。
- 让执行 Agent 自己完成最终 review 并直接 archive。
- 把某个个人域工具写死成团队唯一标准。
- 一开始就要求所有 Agent 严格跑完整主链。
- 每一步都产出大量长文档，而不是维护最小事实、证据和接续摘要。

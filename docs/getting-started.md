# 快速开始与个人域试用

本指南面向第一次试用 open-cowork 的个人域使用者、团队成员和协作负责人。目标不是让人学习 CLI，而是让 Agent 能把项目意图、范围、执行证据、review 和接续状态维护成可审计的项目事实。

## 1. 默认入口

你可以直接对当前可信 Agent 说：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

或者：

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

Agent 的职责是理解项目目标，安装或定位 open-cowork，初始化或升级 `.governance/` 当前状态，准备当前 round，并用人能理解的话汇报当前步骤、owner、阻断、下一步和需要你决策的事项。若项目曾安装旧版本，Agent 会在 setup/onboard 入口内部自动检测、迁移并验证，不要求你额外学习迁移命令。

## 2. v0.3.11 当前状态文件

新项目默认只把当前协作事实放进一组小而可读的文件：

- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`
- `.governance/state.yaml`
- `.governance/current-state.md`
- `.governance/evidence.yaml`
- `.governance/ledger.yaml`
- `.governance/rules.yaml`

这些文件分别承载接手入口、权威状态、可读摘要、证据引用、收束接续和项目规则。大型日志、长输出、历史包和冷数据不应该进入默认读取集。

## 3. 已实施项目如何接续

如果项目已经实施过 open-cowork，新会话或另一个 Agent 应先做项目激活检查。Agent 会在内部选择或确认当前 round，然后只读取项目入口推荐的 bounded read set。

不要从聊天历史或历史材料里重新猜状态。如果同一个项目里同时有需求 1 和需求 2，人的说法应该是：

```text
请用 open-cowork 接续需求 1。
```

或者：

```text
请查看这个项目当前有哪些可接续需求，并接续我指定的那个。
```

## 4. 人应该看到什么

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

人只需要在目标、范围、风险、执行批准、review 决策和是否收束等真实判断点介入。

## 5. 9 步主链

| Step | 名称 | 人类判断点 |
| --- | --- | --- |
| 1 | 明确意图 / Clarify intent | 目标、背景和输入是否说清楚。 |
| 2 | 确定范围 / Lock scope | 要做什么、不做什么、验收标准是什么。 |
| 3 | 方案设计 / Shape approach | 方案、风险和取舍是否可接受。 |
| 4 | 组装执行范围 / Assemble working round | 需求、方案、任务和边界是否装进同一 round。 |
| 5 | 批准开工 / Approve execution | 是否允许进入真实执行。 |
| 6 | 执行变更 / Execute change | Agent 是否在 scope 范围内执行并记录 evidence refs。 |
| 7 | 验证结果 / Verify result | 状态验证和产品验证证据是否清楚。 |
| 8 | 独立审查 / Independent review | 接受、要求修订或拒绝 reviewer decision。 |
| 9 | 归档接续 / Close out and hand off | 是否收束，并把接续状态留给下一轮。 |

`intent confirm` 会满足 Step 1 approval。非阻塞 step 可以记录 human acknowledgement。Step 8 的 review decision 可以先记录，之后再由人决定是否接受该 decision。

## 6. Shell 备用路径

Shell 只用于安装、排障或帮助 Agent 定位工具。普通人只需要知道有三类备用动作：

- 安装 / 更新 open-cowork。
- 检查当前机器上的 open-cowork 版本和路径。
- 旧项目自动升级失败、清理或卸载时查看 dry-run 摘要。

这些动作由 Agent 执行和汇报结果。不要把安装命令、初始化命令和诊断命令当成人的日常任务清单。

## 7. 准备一个可执行 round

Agent 会生成或补齐当前 round 的主链事实：

- 目标、背景和范围。
- 非目标、风险和验收标准。
- 当前 owner、assistant、verifier、reviewer 和 human gate。
- Step 5 approval evidence。
- Step 6 evidence refs。
- Step 7 verify result。
- Step 8 review decision。
- Step 9 closeout / handoff record。

这些事实默认聚合在 `state.yaml`、`current-state.md`、`evidence.yaml`、`ledger.yaml` 和 `rules.yaml` 中，而不是每轮创建大量目录。

## 8. 个人域多 Agent 建议

个人域中可以一人多角，但不建议让同一个执行会话自审自批。

| open-cowork 角色 | 个人域含义 | 常见承载者 |
| --- | --- | --- |
| Sponsor | 目标、范围、最终判断 | 人 |
| Orchestrator | 拆解、流程推进、状态维护 | 日常调度 Agent 或主力 Coding Agent |
| Executor | 编码、修改文件、执行命令 | 主力 Coding Agent |
| Verifier | 跑测试、检查证据、发现缺陷 | 执行 Agent 或独立验证 Agent |
| Reviewer | 独立审查、交叉验证 | 另一个 Agent / 另一个会话 / 人 |
| Maintainer | closeout、ledger、接续摘要 | Orchestrator 或人确认后的 Agent |

关键原则：

- 安装和初始化可以由任意可信 Coding Agent 完成。
- 当前 round 最好有一个主控 Agent 推进状态。
- Review 尽量由另一个 Agent、另一个会话或人完成。
- 人只在目标确认、风险确认、review 决策和 closeout 时介入。

## 9. 三类典型落地场景

### 场景 A：个人域单一 Agent 系统

适合一个人长期主要使用一个 AI Coding 环境的情况，例如只用 Codex 或只用 Claude Code 推进项目。

open-cowork 在这个场景里的重点是：

- 把需求、范围、任务拆解、执行边界和验证结果沉淀到项目事实中。
- 让同一个 Agent 在新会话中可以从 `current-state.md` 和 `state.yaml` 接续。
- 把长任务拆成可审查、可恢复、可收束的 round。
- 避免“任务做到一半，聊天上下文没了就只能重讲一遍”。

人的自然语言入口：

```text
请用 open-cowork 管理这个项目当前需求，后续新会话也要能接续。
```

### 场景 B：本地个人域多个 Agent 系统调度协同

适合一个人同时使用 Codex、Claude Code、Hermes、OMOC / OpenCode、OpenClaw 等多个本地 Agent 的情况。

open-cowork 在这个场景里的重点是：

- 项目是协作中心，不是某个 Agent 的私有会话。
- 所有 Agent 接手前都读取 `.governance/agent-entry.md`。
- 多个需求可以同时存在于 `state.yaml` 的 rounds / current round 视图。
- Agent 必须显式选择或确认需求，不能从聊天历史猜测。
- Executor、Verifier、Reviewer 可以由不同 Agent 或不同会话承担。

人的自然语言入口：

```text
Codex 正在做需求 1；请让 Claude Code 按 open-cowork 接续需求 2，并先确认当前可接续需求。
```

### 场景 C：团队多人域协作

适合多名团队成员各自拥有不同个人域 Agent、AI Coding 环境和工作习惯的情况。

open-cowork 在这个场景里的重点是：

- 不强制统一 runtime、IDE、Agent 或工作台。
- 用项目级 scope 和 rules 对齐范围、允许动作和禁止动作。
- 用 role bindings 明确 owner、assistant、reviewer 和 human gate。
- 用 evidence refs / verify / review 让协作结果可追溯。
- 用 ledger / continuity 让项目可以跨人、跨 Agent、跨阶段持续推进。

人的自然语言入口：

```text
请按 open-cowork 的团队协作方式推进这个项目，让不同成员的 Agent 都能从项目事实接续。
```

## 10. 项目级 Agent Entry 使用方式

`.governance/agent-entry.md` 是目标项目里的 Agent 接手说明。它适合以下情况：

- 新会话不知道旧会话进度。
- 另一个 Agent 要接手同一项目。
- 同一项目里有多个可接续需求。
- 团队成员希望自己的本地 Agent 按同一套流程工作。

使用方式很简单：让 Agent 先读取这个文件，再做 activation / status，并只读取入口给出的 recommended read set。

人的自然语言入口：

```text
这个项目已经实施 open-cowork，请按项目里的 open-cowork 接手规则接续当前需求。
```

如果项目里有多个并行需求，可以说：

```text
请先列出这个项目当前正在进行的 open-cowork 需求，我选择后再接续。
```

如果 Agent 环境支持自定义 Skill，也可以把该文件内容注册成平台 Skill；如果不支持，直接作为项目内接手文档读取即可。项目权威入口仍然是 `.governance/agent-entry.md`。

## 11. 旧版本迁移、清理和卸载

旧版本项目可能已经生成大量历史治理目录。v0.3.11 的原则是先保留、再迁移、最后由人确认是否清理：

1. Agent 先检测旧版目录、git 跟踪状态和潜在风险。
2. Agent 先做 dry-run，说明会移动哪些历史、会保留哪些文件。
3. 人确认后，Agent 执行迁移并写入 receipt。
4. Agent 运行 verify，检查 receipt、当前状态文件和旧历史状态。
5. 清理动作也必须先 dry-run，再经人确认。
6. 卸载默认拒绝破坏性删除；只有显式确认并记录卸载前 audit 时才执行。

## 12. 上下文压缩或中断恢复

如果会话过长、自动压缩失败或 Agent 中断，优先让 Agent 生成结构化恢复包。

如果有 Codex session jsonl，可以让 Agent 带上 session log，恢复包会记录 remote compact、最后 token 计数和最后错误事件。

恢复时只读取恢复包的 recommended read set，不要重新全文扫描仓库历史和冷历史。

长任务默认采用 compact-resilient discipline：Agent 只读当前 bounded read set；大型命令输出、独立 review、session 恢复内容和日志写入文件；对话里只保留路径、evidence ref、关键结论和失败证据。遇到 remote compact 或 stream 断裂时，从恢复包和最后成功 evidence 继续，而不是把失败会话全文重新读入上下文。

## 13. 判断试用是否成功

一次个人域试用成功，不要求项目立刻进入复杂团队协作，只要求满足：

- Agent 能在几分钟内完成安装、初始化和当前状态输出。
- 任意一个 Agent 能围绕同一个 round 继续推进。
- 从一个 Agent 切换到另一个 Agent 时，接手者能通过 `.governance/AGENTS.md`、`.governance/agent-entry.md`、`current-state.md` 和 handoff / digest 理解状态。
- 人能看懂当前处于哪个阶段、下一步需要谁做什么。
- session 压缩或断裂时，可以生成恢复包，而不是只能回聊天记录里打捞上下文。

## 14. 不推荐的首次试用方式

- 让人先背命令、schema 和内部文件路径。
- 让执行 Agent 自己完成最终 review 并直接 closeout。
- 把某个个人域工具写死成团队唯一标准。
- 一开始就要求所有 Agent 严格跑完整主链。
- 每一步都产出大量长文档，而不是维护最小事实、证据和接续摘要。

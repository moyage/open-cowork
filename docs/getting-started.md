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

如果项目已经实施过 open-cowork，新会话或另一个 Agent 应先运行项目激活检查：

```bash
ocw activate
```

然后读取目标项目中的：

- `.governance/AGENTS.md`
- `.governance/current-state.md`
- `.governance/agent-playbook.md`
- 当前 change 的 `contract.yaml`
- 当前 change 的 `bindings.yaml`
- 当前 step report

不要从聊天历史或历史 archive 里重新猜状态。

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

Shell 只用于安装、排障或帮助 Agent 定位工具：

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

`onboard` 会初始化 `.governance/`，输出状态和 session 诊断。它不会替换你的 IDE、CI/CD、脚本或 Agent 工具链。

## 6. 准备一个可执行 change

Agent 可以用 `pilot` 或 `change prepare` 生成当前 change 的主链材料。它们是内部工具，不是人的默认任务清单。

```bash
ocw pilot \
  --target /path/to/your-project \
  --change-id current-iteration \
  --title "Current iteration" \
  --goal "在当前项目中试用 open-cowork 主链" \
  --scope-in "src/**" \
  --scope-in "tests/**" \
  --verify-command "<本项目测试命令>" \
  --yes
```

这会生成或补齐：

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

## 8. 上下文压缩或中断恢复

如果会话过长、自动压缩失败或 Agent 中断，优先生成结构化恢复包：

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

如果有 Codex session jsonl，可以让 Agent 带上 `--session-log`，恢复包会记录 remote compact、最后 token 计数和最后错误事件。

恢复时只读取恢复包的 recommended read set，不要重新全文扫描仓库历史和 archive。

## 9. 判断试用是否成功

一次个人域试用成功，不要求项目立刻进入复杂团队协作，只要求满足：

- Agent 能在几分钟内完成安装、初始化和当前状态输出。
- 任意一个 Agent 能围绕同一个 `change-id` 继续推进。
- 从一个 Agent 切换到另一个 Agent 时，接手者能通过 `.governance/AGENTS.md`、`.governance/current-state.md` 和 handoff / digest 理解状态。
- 人能看懂当前处于哪个阶段、下一步需要谁做什么。
- session 压缩或断裂时，可以生成恢复包，而不是只能回聊天记录里打捞上下文。

## 10. 不推荐的首次试用方式

- 让人先背命令、schema 和内部文件路径。
- 让执行 Agent 自己完成最终 review 并直接 archive。
- 把某个个人域工具写死成团队唯一标准。
- 一开始就要求所有 Agent 严格跑完整主链。
- 每一步都产出大量长文档，而不是维护最小事实、证据和接续摘要。

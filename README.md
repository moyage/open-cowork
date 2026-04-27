# open-cowork

`open-cowork` 是一个面向个人域、团队多人、多 Agent 与多 AI Coding 场景的协同治理框架与协议体系。

它不要求每个人统一 Agent、模型、IDE、CLI 或 workflow，而是把复杂任务中的意图、边界、角色、执行证据、审查门、归档和接续状态沉淀为可读、可验证、可交接的项目事实。

一句话：`open-cowork` 不是让人去学习一套新的命令行流程，而是让个人域 Agent 和团队协作 Agent 能用统一协议，把复杂项目稳定推进下去。

## 默认使用方式：对你的 Agent 说一句话

在 AI 时代，`open-cowork` 的默认入口不是让人离开 Agent 环境去手动敲命令，而是让人用自然语言表达意图，让 Agent 负责安装、初始化、准备 change、维护状态和汇报进展。

你可以对当前个人域里的 Codex、Claude Code、Cursor、OpenClaw、Hermes、OMOC、Antigravity 或其他可信 Agent 说：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

或者：

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

Agent 应该做的是：理解当前项目目标，安装或定位 `open-cowork`，在目标项目中生成 `.governance/`，准备当前 change，维护 contract / bindings / evidence / review / archive / continuity，并用人能理解的方式汇报“当前项目推进到哪里、谁负责、卡在哪里、下一步是什么、需要人做什么决策”。

CLI 仍然存在，但它是给 Agent 和排障场景使用的内部工具，不是要求普通使用者记忆的主界面。

## 为什么需要 open-cowork

AI 大模型、Agent 和 AI Coding 工具正在把个体能力快速放大。一个人可以在个人域中同时使用多个模型、多个 coding agent、多个 IDE 和多个工具链，成为某种意义上的“超级个体”。

但复杂项目的真正难点，往往不是单个 Agent 是否足够强，而是：

- 意图如何从聊天记录进入结构化项目事实；
- 多个 Agent 如何分工、接力、交叉验证，而不互相覆盖；
- 执行结果如何留下 evidence，而不是只停留在“我已经做了”的描述里；
- review、archive、closeout 如何成为明确的门，而不是靠记忆和口头约定；
- 当 session 被压缩、上下文爆炸或 provider 断开时，如何恢复推进；
- 当从个人域走向多人协作时，如何不强迫所有人统一工具链。

`open-cowork` 解决的是这些协作治理问题。

## 项目定位

`open-cowork` 是：

- Agent-first 协作协议层：默认由 Agent 读取和维护协作事实，人用自然语言发起和决策。
- 低侵入框架：接入现有项目和现有 Agent，不强制替换工具链。
- 多 Agent 协作骨架：让不同 Agent 有明确角色、边界、输入和输出。
- 个人域到团队域的桥：先支持单人多 Agent，再自然扩展到多人多 Agent。
- docs-as-code / governance-as-code 实践：把关键协作事实落到文件和索引里。

`open-cowork` 不是：

- 不是 IDE。
- 不是新的 AI Coding runtime。
- 不是任务管理 SaaS。
- 不是要求所有成员统一使用某个 Agent 的团队平台。
- 不是让人背诵命令、schema 或流程术语的 CLI-first 工具。
- 不是替代人的最终判断和 sponsor 责任。

## 目标

`open-cowork` 的目标是覆盖“意图 -> 落地产物 -> 可持续迭代维护”的闭环：

1. 让复杂任务有明确入口和边界。
2. 让执行前有 contract，执行后有 evidence。
3. 让 verify / review / archive 成为明确治理门。
4. 让 handoff、owner transfer、increment、closeout、sync 成为可追踪接续原语。
5. 让人可以通过 4 阶段视图理解项目进展。
6. 让 Agent 可以通过结构化文件读取当前状态。
7. 让个人域工具异构，但协作协议统一。
8. 让首次试用从“一句话”开始，而不是从命令手册开始。

## 适用场景

### 个人域单人多 Agent

一个人同时使用 Claude Code、Codex、Cursor、Antigravity、OpenCode、OpenSpec、调度 Agent 或其他 AI Coding 工具，希望让它们围绕同一个 change-id 分工、验证和接续。

### 个人项目复杂任务治理

一个本地项目需要更清楚地管理需求、方案、执行、验证、review、复盘和下一轮接续，但暂时还没有多人协作。

### 多人多 Agent 协作

多个成员各自保留自己的个人域和工具链，但围绕同一个复杂项目协作，需要统一任务入口、状态、证据、review 和 closeout。

### Agent session 恢复

当 Agent 遇到 context/session 爆炸、频繁压缩、provider drop 或无法继续推进时，需要生成最小恢复包，而不是从聊天历史里打捞上下文。

## 核心概念

| 概念 | 含义 |
| --- | --- |
| change package | 一个变更或任务的工作单元，承载 intent、requirements、design、tasks、contract、evidence 等。 |
| execution contract | 执行前的边界契约，定义目标、scope、允许动作、禁止动作、验证对象和证据要求。 |
| bindings | 当前 change 的角色和 owner 绑定，避免“谁负责”只存在于聊天里。 |
| evidence | 执行结果的证据，包括命令输出、测试输出、文件变更、执行摘要等。 |
| verify | 对 evidence 和状态一致性进行验证。 |
| review | 独立审查并作出 approve / revise / reject 决策。 |
| archive | 将完成的 change 收束为可追溯历史事实。 |
| continuity | 交接、owner transfer、increment、closeout、sync、digest 等接续能力。 |
| current-state | 给人和下一个 Agent 看的当前状态快照。 |
| timeline | 运行时事件流，记录关键状态变化。 |

## 4 阶段与 9 步流程

人默认看 4 个阶段，底层保留 9 个治理步骤。

| 人类阶段 | 底层步骤 | 目标 | 典型产物 |
| --- | --- | --- | --- |
| 定义与对齐 | 1. Clarify the goal | 明确意图、背景、目标和输入 | intent / goal notes |
| 定义与对齐 | 2. Lock the scope | 明确范围、非目标和边界 | requirements / scope |
| 方案与准备 | 3. Shape the approach | 形成方案方向和风险判断 | design |
| 方案与准备 | 4. Assemble the change | 组装 change package | manifest / tasks |
| 方案与准备 | 5. Approve the start | 准备 contract、角色和 gate | contract / bindings / current-state |
| 执行与验证 | 6. Execute the change | 在受控边界内执行 | evidence / execution summary |
| 执行与验证 | 7. Verify the result | 验证结果与状态一致性 | verify result |
| 审查与收束 | 8. Review and decide | 独立 review 并决策 | review decision |
| 审查与收束 | 9. Archive and carry forward | 归档并生成接续输入 | archive / closeout / digest |

默认建议：第一次试用只要求 Agent 完成初始化、当前 change 准备、contract 校验和状态输出；不要一上来强制跑完整 9 步。

## 当前版本完成度

当前 `v0.3.1` 是“Human Participation Runtime Hardening”。重点是在 v0.3.0 的人类可见 Step 1-9 与 Step 5 / Step 8 / Step 9 hard gates 之上，修复实践中暴露的“前置步骤不可见、prepare 像是已完成 Step 1-5、状态面过于 CLI-first、review 失败后恢复路径不清、独立 review 调度证据不足”等问题。

v0.3.1 的原则是：新 change 默认从 Step 1 开始；`change prepare` 只生成材料，不代表 Step 1-5 已完成；Agent 应通过 intent / participants / change status / step report 向人汇报“当前在哪一步、谁负责、证据是什么、下一步需要谁批准”。

已经具备：

- 根目录 `AGENTS.md`：告诉各类 Agent 如何以 Agent-first 方式采用 `open-cowork`。
- `docs/agent-adoption.md`：说明“一句话触发 -> Agent 实施 -> 结构化事实 -> 人类进展反馈”的采用路径。
- `docs/agent-playbook.md`：给 Agent 的操作规则和人类进展汇报模板。
- `ocw init` 初始化 `.governance/` 结构。
- `ocw status` 输出人类可读状态面。
- `ocw change create` 创建 change package。
- `ocw change prepare` 自动填充主链准备文件，并生成目标项目 Agent handoff pack。
- `ocw adopt --dry-run` 根据自然语言目标、source docs 和个人域 agent inventory 生成 adoption plan。
- `ocw change prepare --source-doc` 将需求来源绑定进 change package。
- `ocw participants setup` 生成个人域参与者 profile 和 9 步 owner / assistant / reviewer / human gate 矩阵。
- `ocw intent capture` / `ocw intent confirm` 捕获并确认需求、优化、Bug、范围、风险和验收标准。
- `ocw step report` 为 4 阶段 9 步生成可读阶段报告。
- `ocw step report --format human` 输出人类可读步骤报告，包含标准 Step、传统映射、owner、输入、输出、完成标准、下一步进入条件、框架约束、Agent 已做动作、Agent 预期动作和短确认选项。
- `ocw intent status` / `ocw participants list` / `ocw change status` / `ocw status --last-archive` 输出更适合 Agent 汇报的人类可读状态面。
- `ocw step approve` 记录 human gate approval；Step 5 / Step 8 / Step 9 approval 分别会被 `ocw run` / `ocw review` / `ocw archive` 消费。
- `ocw contract validate` 检查 confirmed intent 与 contract scope 是否漂移。
- `ocw review` 默认阻止 reviewer mismatch；只有显式 bypass 才会写入审计记录。
- `ocw review` 可记录真实独立 reviewer 的 runtime evidence；`ocw revise` 可把 `review-revise` 决策显式带回 Step 6 修订。
- `ocw status` 输出 9-step progress table，显示每一步 report、`gate_type`、`gate_state` 和 `approval_state`。
- `ocw archive` 生成最终状态一致性快照、Step 9 report traceability，以及 Step 5 / Step 8 / Step 9 human gate summary，便于归档审计。
- `ocw pilot` 完成个人域试用 change 的初始化、准备、校验、状态输出和 Agent handoff pack。
- 目标项目 `.governance/AGENTS.md`：给后续接手 Agent 的项目内入口。
- 目标项目 `.governance/agent-playbook.md`：给后续接手 Agent 的操作规则。
- 目标项目 `.governance/current-state.md`：给人和 Agent 的当前项目推进状态。
- `ocw contract validate` 校验 execution contract。
- `ocw run` 写入执行证据。
- `ocw verify` 写入验证结果。
- `ocw review` 写入审查决策。
- `ocw archive` 归档完成变更。
- `ocw runtime-status` 输出机器可读状态。
- `ocw timeline` 输出运行时事件流。
- `ocw continuity ...` 支持 handoff、owner transfer、increment、closeout、sync、history、export、digest。
- `ocw diagnose-session` 和 `ocw session-recovery-packet` 支持 session/context 恢复诊断。
- `ocw hygiene` / `ocw doctor` 分类 runtime generated、Agent handoff、pending docs、tracked truth source、ignored artifacts，并检查人类可读状态与机器状态的一致性。
- `scripts/bootstrap.sh`、`scripts/update.sh`、`scripts/bootstrap.sh --clean` 支持安装、升级和干净重装。
- `scripts/smoke-test.sh` 支持最小健康检查。

还没有覆盖：

- `open-cowork` 自身作为完整自带 Agent / TUI / Dashboard 运行。
- 对所有主流 Agent / IDE 的专用插件。
- 复杂企业级审批流。
- 云端协作服务。
- 自动替你判断业务目标是否正确。

## 快速开始

### 推荐路径：让 Agent 帮你实施

在你的项目或个人域 Agent 会话中，说：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

Agent 应该完成：

1. 确认当前目标项目。
2. 安装或定位 `open-cowork`。
3. 初始化 `.governance/`。
4. 创建或准备当前 change package。
5. 生成 `contract.yaml`、`bindings.yaml` 和 Agent handoff pack。
6. 输出“当前项目推进状态”，而不是把命令清单丢给你。

人只需要确认目标、范围、风险、review 决策和是否继续。

### Shell 备用路径：安装与健康检查

如果你需要手动安装、排障或帮助 Agent 定位工具，可以使用：

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/bootstrap.sh
source .venv/bin/activate
ocw version
./scripts/smoke-test.sh
```

在目标项目中执行一次最小初始化：

```bash
ocw onboard --target /path/to/your-project --mode quickstart --yes
ocw --root /path/to/your-project adopt --target /path/to/your-project --goal "Describe the project iteration to govern" --dry-run
```

### 升级路径

如果你已经安装过早期版本，推荐在 `open-cowork` 仓库根目录执行：

```bash
git pull --ff-only
./scripts/update.sh
source .venv/bin/activate
ocw version
```

如果怀疑本地虚拟环境残留或命令路径混乱，使用干净重装：

```bash
git pull --ff-only
./scripts/bootstrap.sh --clean
source .venv/bin/activate
ocw version
./scripts/smoke-test.sh
```

### Agent 继续推进时读取哪里

目标项目完成采用后，后续 Agent 应优先读取：

- `.governance/AGENTS.md`
- `.governance/current-state.md`
- `.governance/agent-playbook.md`
- `.governance/changes/<change-id>/contract.yaml`
- `.governance/changes/<change-id>/bindings.yaml`

这几份文件就是为了防止上下文压缩、会话断裂或 Agent 接力时重新从聊天记录里考古。

## Roadmap

### v0.2.x：试用体验与文档稳定

- 强化 README、Agent-first 入口和上手路径。
- 简化安装、初始化、诊断命令。
- 清理文档结构，降低首次理解成本。
- 补更多个人域和多 Agent 试用样例。

### v0.3：协议执行体验增强（已发布）

- 明确 prepare-state 与标准 Step 状态分离。
- 增强 Step 1-9 的人类可读报告、gate 状态和确认体验。
- 改善 review、verify、archive 的人类可读输出和审计链。
- 提供更稳定的 Agent handoff current-state / playbook / status 语义。

### v0.4：多 Agent / 多人协作适配

- 增强不同 Agent / AI Coding 工具的接入说明和 adapter pattern。
- 提供团队协作样例项目。
- 提供更清晰的跨个人域 handoff / sync 实践。

### 更长期方向

- 可视化状态面。
- 团队级 dashboard。
- 更强的策略层和治理规则配置。
- 与外部 issue tracker / PR / CI 系统集成。

## 文档索引

- `AGENTS.md`：仓库级 Agent-first 入口。
- `docs/getting-started.md`：唯一上手入口，包含 Agent-first 采用、个人域试用和 Shell 备用路径。
- `docs/agent-adoption.md`：Agent-first 采用方式。
- `docs/agent-playbook.md`：Agent 操作规则与人类进展汇报模板。
- `docs/README.md`：完整文档地图。
- `docs/specs/00-top-level-whitepaper.md`：顶层白皮书。
- `docs/specs/01-prd.md`：产品定义和能力模型。
- `docs/specs/04-change-package-spec.md`：change package 规格。
- `docs/specs/05-execution-contract-spec.md`：execution contract 规格。
- `docs/specs/06-evidence-verify-review-schema.md`：evidence / verify / review 规格。
- `docs/specs/07-standard-9-step-runtime-flow.md`：标准 9 步流程。
- `docs/specs/08-role-binding-spec.md`：角色绑定规则。
- `docs/archive/`：历史迭代计划、设计记录、closeout 和复盘材料。

## 贡献与安全

- `CONTRIBUTING.md`：贡献指南。
- `CODE_OF_CONDUCT.md`：行为准则。
- `SECURITY.md`：安全反馈和隐私注意事项。

## 一句话总结

`open-cowork` 的核心价值不是让某个 Agent 更强，也不是让人多学一套命令，而是让多个强个人域和多个 Agent 在复杂项目中通过统一协议形成高质量协作。

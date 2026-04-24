# open-cowork

`open-cowork` 是一个面向个人域与团队协作的复杂协作底层框架与协议体系。

它不要求每个人统一 Agent、模型、IDE、CLI 或 workflow，而是用统一的任务入口、角色边界、执行证据、审查门和接续机制，把多个强个人域或多个 Agent 的工作组织成可分工、可验证、可协同、可持续维护的过程。

一句话：`open-cowork` 不是替代你的个人域，而是让多个个人域和多个 Agent 可以围绕复杂任务稳定协作。

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

- 协作协议层：统一 change、contract、evidence、review、archive、continuity 的语义。
- 低侵入框架：接入现有项目和现有 Agent，不强制替换工具链。
- 多 Agent 协作骨架：让不同 Agent 有明确角色、边界、输入和输出。
- 个人域到团队域的桥：先支持单人多 Agent，再自然扩展到多人多 Agent。
- docs-as-code / governance-as-code 实践：把关键协作事实落到文件和索引里。

`open-cowork` 不是：

- 不是 IDE。
- 不是新的 AI Coding runtime。
- 不是任务管理 SaaS。
- 不是要求所有成员统一使用某个 Agent 的团队平台。
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
| evidence | 执行结果的证据，包括命令输出、测试输出、文件变更、执行摘要等。 |
| verify | 对 evidence 和状态一致性进行验证。 |
| review | 独立审查并作出 approve / revise / reject 决策。 |
| archive | 将完成的 change 收束为可追溯历史事实。 |
| continuity | 交接、owner transfer、increment、closeout、sync、digest 等接续能力。 |
| runtime status | 面向人和工具的当前状态快照。 |
| timeline | 运行时事件流，记录关键状态变化。 |

## 4 阶段与 9 步流程

人默认看 4 个阶段，底层保留 9 个治理步骤。

| 人类阶段 | 底层步骤 | 目标 | 典型产物 |
| --- | --- | --- | --- |
| 定义与对齐 | 1. Clarify the goal | 明确意图、背景、目标和输入 | intent / goal notes |
| 定义与对齐 | 2. Lock the scope | 明确范围、非目标和边界 | requirements / scope |
| 方案与准备 | 3. Shape the approach | 形成方案方向和风险判断 | design |
| 方案与准备 | 4. Assemble the change | 组装 change package | manifest / tasks |
| 方案与准备 | 5. Approve the start | 准备 contract、角色和 gate | contract / bindings |
| 执行与验证 | 6. Execute the change | 在受控边界内执行 | evidence / execution summary |
| 执行与验证 | 7. Verify the result | 验证结果与状态一致性 | verify result |
| 审查与收束 | 8. Review and decide | 独立 review 并决策 | review decision |
| 审查与收束 | 9. Archive and carry forward | 归档并生成接续输入 | archive / closeout / digest |

默认建议：第一次试用只跑到 `init -> status -> diagnose -> change create -> status`，不要一上来强制跑完整 9 步。

## 当前版本完成度

当前 `v0.2.3` 是“带 onboarding/setup 入口的可试用协议框架与 CLI 基线”，重点是让个人域和团队成员能低门槛开始实践。

已经具备：

- `ocw init` 初始化 `.governance/` 结构。
- `ocw status` 输出人类可读状态面。
- `ocw change create` 创建 change package。
- `ocw contract validate` 校验 execution contract。
- `ocw run` 写入执行证据。
- `ocw verify` 写入验证结果。
- `ocw review` 写入审查决策。
- `ocw archive` 归档完成变更。
- `ocw runtime-status` 输出机器可读状态。
- `ocw timeline` 输出运行时事件流。
- `ocw continuity ...` 支持 handoff、owner transfer、increment、closeout、sync、history、export、digest。
- `ocw diagnose-session` 和 `ocw session-recovery-packet` 支持 session/context 恢复诊断。
- `scripts/bootstrap.sh` 支持本地安装。
- `ocw onboard` / `ocw setup` 支持交互式或脚本式初始化。
- `open-cowork onboard` 提供更直观的 console script alias。
- `scripts/quickstart.sh` 保留为一键脚本入口，并调用 `ocw onboard`。
- `scripts/smoke-test.sh` 支持最小健康检查。

还没有覆盖：

- 完整图形化界面或团队看板。
- 对所有主流 Agent / IDE 的专用插件。
- 复杂企业级审批流。
- 云端协作服务。
- 自动替你判断业务目标是否正确。

## Quick Start

### 一键试用推荐路径

在 `open-cowork` 仓库根目录执行：

```bash
./scripts/quickstart.sh /path/to/your-project
```

或者安装后直接运行：

```bash
ocw onboard --target /path/to/your-project --mode quickstart --yes
ocw setup --target /path/to/your-project --yes
open-cowork onboard --target /path/to/your-project --yes
```

这些命令会：

1. 自动安装 / 激活本地 `ocw` 命令。
2. 在目标项目中执行 `ocw init`。
3. 执行 `ocw status`。
4. 执行 `ocw diagnose-session`。
5. 输出下一步建议。

### 手动安装路径

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/bootstrap.sh
source .venv/bin/activate
ocw --help
./scripts/smoke-test.sh
```

在你的目标项目中初始化：

```bash
cd /path/to/your-project
ocw --root . init
ocw --root . status
ocw --root . diagnose-session
```

### 创建一个轻量 change

```bash
ocw --root . change create personal-demo --title "Personal domain pilot"
ocw --root . status
ocw --root . continuity digest --change-id personal-demo
```

如果 `contract.yaml` 还未补齐，`status / digest` 会显示 draft 指引，而不是要求你立刻跑完整主链。

## Roadmap

### v0.2.x：试用体验与文档稳定

- 强化 README 和上手路径。
- 简化安装、初始化、诊断命令。
- 清理文档结构，降低首次理解成本。
- 补更多个人域和多 Agent 试用样例。

### v0.3：协议执行体验增强

- 提供更友好的 contract / bindings 生成辅助。
- 增强 change package 模板。
- 改善 review、verify、archive 的人类可读输出。
- 提供更稳定的 Agent handoff prompt / packet。

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

- `docs/getting-started.md`：唯一上手入口，包含个人域和团队试用说明。
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

`open-cowork` 的核心价值不是让某个 Agent 更强，而是让多个强个人域和多个 Agent 在复杂项目中通过统一协议形成高质量协作。

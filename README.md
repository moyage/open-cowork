# open-cowork

`open-cowork` 是一个 Agent-first collaboration governance protocol。它把复杂项目里的意图、范围、角色、证据、审查、归档和接续状态落成轻量项目事实，让不同 AI Coding 环境和本地个人域 Agent 可以围绕同一个项目继续工作。

它的默认入口不是让人学习命令行，而是让人把目标讲给 Agent。**CLI 是 Agent 内部工具**，用于维护结构化事实、排障和接力。

v0.3.11 起，open-cowork 的默认项目模型是 lean protocol：目标项目默认只需要一组小文件，例如 `.governance/AGENTS.md`、`.governance/agent-entry.md`、`.governance/agent-playbook.md`、`.governance/state.yaml`、`.governance/current-state.md`、`.governance/evidence.yaml`、`.governance/ledger.yaml` 和 `.governance/rules.yaml`。旧版本的重目录布局只作为迁移来源和兼容对象存在。

## 人只需要对 Agent 说

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

或者：

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

如果这个项目已经实施过 open-cowork，人不需要知道内部文件怎么读，只需要告诉新会话或另一个 Agent：

```text
这个项目已经实施 open-cowork，请按项目里的 open-cowork 接手规则接续当前需求。
```

如果同一个项目里有多个并行需求，可以说：

```text
请先列出这个项目当前正在进行的 open-cowork 需求，我选择后再接续。
```

Agent 会在内部运行确定性 resume / status 入口、读取项目事实、确认要接续的 round，然后继续当前步骤。对旧版项目，这相当于先做 activate 后接续；对 v0.3.11 lean 项目，则是先恢复当前 round 再执行。自然语言只是请求 Agent 运行项目入口；协议触发点是项目内的确定性入口，不是靠关键词猜测。open-cowork 的应用对象是项目，不是某个单独 Agent。

## 典型使用场景

### 个人域单一 Agent 系统

一个人只使用 Codex、Claude Code 或其他单一 AI Coding 环境时，open-cowork 主要解决“长任务不断线”的问题。Agent 把本轮需求、范围、执行证据、验证结果和下一步接续状态写入项目里的轻量治理文件，即使会话压缩、重开窗口或隔天继续，也可以从项目事实恢复，而不是靠聊天记录回忆。

### 本地个人域多个 Agent 系统调度协同

一个人同时使用 Codex、Claude Code、Hermes、OMOC / OpenCode 等多个本地 Agent 时，open-cowork 主要解决“同一项目、多个 Agent 不互相猜状态”的问题。不同 Agent 进入项目后都先按 `.governance/agent-entry.md` 使用确定性入口，再围绕同一个 active round、scope、role bindings 和 evidence refs 协作。多个需求可以同时存在于 `state.yaml` 的 rounds / current round 视图中，接手时必须显式选择要继续的需求。

### 团队多人域场景

多人团队中，每个人可以有自己的个人域 Agent 和熟悉的 AI Coding 环境。open-cowork 不要求团队统一 runtime 或工作台，而是在项目层提供共同事实面：谁负责、当前范围是什么、何时允许执行、证据在哪里、谁做独立审查、是否可以收束归档。这样每个“超级个体”可以保持自己的工具组合，同时通过项目级 state、rules、evidence、review 和 ledger 形成可持续协作的“超级组织”。

## 项目级接手规则（Skill）怎么用

open-cowork 会在已实施项目中生成 `.governance/agent-entry.md`。它放在 `.governance/` 下，是因为它属于“这个项目的协作事实和接手规则”，需要跟项目一起走；它不是某个 Agent 平台专属的安装型 Skill，也不是给人背命令的教程。

如果某个 Agent 环境支持自定义 Skill，可以把这份文件注册进去；如果不支持，Agent 直接把它当成项目内接手说明读取即可。

使用场景：

- 新会话接续：让当前 Agent 按项目接手规则恢复进度。
- 跨 Agent 接续：从 Codex 切到 Claude Code、Hermes、OMOC 或其他 Agent 时，让新 Agent 按同一份接手规则读取项目事实。
- 并行需求选择：当同一项目有多个正在进行的需求，让 Agent 先列出可接续项，再由人选择。
- 团队成员接入：团队成员在自己的个人域 Agent 中打开项目后，使用同一份接手规则遵守相同流程和边界。

## 一张图

```mermaid
flowchart TD
    Human["人：说明目标、确认范围、批准关键门"] --> Agent["Agent：实施 open-cowork"]
    Agent --> Facts["项目事实层 .governance/"]
    Facts --> State["state.yaml：紧凑权威状态"]
    Facts --> Current["current-state.md：可读状态摘要"]
    Facts --> Evidence["evidence.yaml：有界证据引用"]
    Facts --> Ledger["ledger.yaml：收束与接续记录"]
    State --> Scope["Round scope：目标、范围、验收"]
    State --> Roles["Role bindings：owner / reviewer / gates"]
    Evidence --> Verify["Verify：验证结果"]
    Verify --> Review["Independent review：独立审查"]
    Review --> Ledger
    Current --> NextAgent["新会话 / 另一个 Agent：按 agent-entry 接续"]
    State --> NextAgent
```

## 9 个步骤的清晰名称

| Step | 名称 | 人需要关心什么 |
| --- | --- | --- |
| 1 | 明确意图 / Clarify intent | 目标、背景、输入是否说清楚。 |
| 2 | 确定范围 / Lock scope | 要做什么、不做什么、验收标准是什么。 |
| 3 | 方案设计 / Shape approach | 方案方向、风险和取舍是否可接受。 |
| 4 | 组装执行范围 / Assemble working round | Agent 把需求、方案、任务和边界装进同一个 round。 |
| 5 | 批准开工 / Approve execution | 人批准按当前范围进入真实执行。 |
| 6 | 执行变更 / Execute change | Agent 在 scope 范围内工作并记录 evidence refs。 |
| 7 | 验证结果 / Verify result | 测试、检查和一致性验证。 |
| 8 | 独立审查 / Independent review | 非执行者给出 approve / revise / reject。 |
| 9 | 归档接续 / Close out and hand off | 收束本轮，写入 ledger，留下下一轮可恢复状态。 |

## 核心能力

open-cowork 的 README 只说明当前框架和流程，不承担版本发布说明。具体版本变化请看 `CHANGELOG.md` 和 GitHub Release。

- 项目事实层：把意图、范围、角色、证据、审查、归档和接续状态落到 `.governance/`。
- Lean 默认模型：用少量可读、可验证、可轮转的文件承载当前事实，避免每轮工作生成大量目录。
- 9 步协作主链：从明确意图到归档接续，区分人类决策、Agent 执行、验证和独立审查。
- 项目级接续：新会话、另一个 Agent 或另一个团队成员都从项目事实继续，而不是从聊天历史猜状态。
- 团队协作模式：Agent 推荐轻量、个人多 Agent、团队标准或团队严格协作，人只确认协作强度是否合适。
- 接手摘要：为当前 round 生成内部接手资料索引和短摘要，帮助长任务在上下文压缩后恢复。
- 并行需求管理：同一项目可以同时登记多个 round，接手时先选择要继续的需求。
- 执行边界：通过 round scope、role bindings 和 rules 明确允许范围、禁止动作、验证要求和证据要求。
- 完整实现约束：已确认的需求、范围和验收标准默认要求完整实现；未经人明确批准，Agent 不得自行降级为最小实现、部分实现或延期实现。
- 执行前检查：已启用 open-cowork 的项目，Agent 修改项目文件前必须先确认当前 round、scope、approval、reviewer 独立性和 readiness；事后补录只能作为 recovery，不能伪装成正常 evidence。
- 证据与审查：执行结果、测试输出、review decision 和 human gate 都可追溯。
- 低侵入协同：不强制统一 IDE、Agent runtime、工作台或团队成员的个人域工具组合。

## 核心概念

- `round` / 工作轮次：一轮可执行、可验证、可收束的工作单元。
- `scope` / 执行范围：说明目标、允许范围、禁止范围、验证对象和证据要求。
- `role bindings` / 角色绑定：说明每一步由谁负责、谁协助、谁审查、哪些步骤需要人确认。
- `evidence refs` / 证据引用：执行输出、测试结果、修改摘要和其他可审查材料的有界引用。
- `review` / 独立审查：非执行者给出 approve / revise / reject。
- `ledger` / 接续账本：收束本轮工作，留下下一轮可恢复的状态。

## `.governance/` 里放什么

`.governance/` 是目标项目里的协作事实层，不是普通文档目录，也不是所有过程材料的堆放处。v0.3.11 默认只把小而关键的事实放在第一屏可读位置：

| 内容 | 典型位置 | 主要消费者 |
| --- | --- | --- |
| Agent 接手入口 | `.governance/AGENTS.md`、`.governance/agent-entry.md`、`.governance/agent-playbook.md` | Agent |
| 权威状态 | `.governance/state.yaml` | Agent + Reviewer |
| 可读状态摘要 | `.governance/current-state.md` | 人 + Agent |
| 证据引用 | `.governance/evidence.yaml` | Agent + Reviewer |
| 规则与策略 | `.governance/rules.yaml` | Agent + Reviewer |
| 收束与接续记录 | `.governance/ledger.yaml` | Agent + 审计 |

旧版本项目可能仍有重目录布局。v0.3.11 对这类项目的默认处理方式是：Agent 在安装、初始化或 setup/onboard 时自动检测旧布局，生成 lean state，把旧重目录迁移到 cold history，并运行验证。人不需要额外理解或执行迁移命令。只有清理 cold history 或卸载治理文件这类破坏性动作，才需要显式确认和 receipt。

人和团队通常只需要读 `current-state.md`、当前状态报告、review 摘要和 closeout 摘要；Agent 才需要消费 YAML 状态、证据引用和 rules。

## 旧版本如何升级、清理和卸载

Agent 负责处理旧版本项目，人不需要记命令。默认顺序是：

1. 安装、初始化、setup 或 onboard 入口自动识别旧 heavy 布局和协议版本。
2. 自动创建或升级 lean 文件，把旧历史迁移到 cold history，并写入 migration receipt。
3. 自动运行 verify，确认 lean 文件、receipt 和 legacy 状态一致；失败时停止后续 setup/onboard。
4. 如需清理 cold history，再做 dry-run 并经人确认后执行 cleanup。
5. 如需卸载，默认拒绝破坏性删除；只有显式确认并记录卸载前 audit 时才移除治理文件。

## 人类最小操作面

普通使用者只需要做四类决策：

1. 确认意图和范围。
2. 批准是否进入执行。
3. 选择 review 结论。
4. 批准收束或要求继续修订。

Agent 负责运行内部命令、维护 `.governance/`、汇报当前步骤、owner、阻断、下一步和需要人决定的事项。人类不需要学习 CLI；只有安装或排障时才需要让 Agent 展示少量备用命令。

## 文档入口

- `AGENTS.md`：给 Agent 的仓库级入口，强调不要把人带回 CLI-first。
- `docs/README.md`：文档地图，说明普通读者、Agent、规格读者和历史追溯者各看哪里。
- `docs/glossary.md`：术语表。
- `docs/getting-started.md`：上手细节、迁移恢复和个人域多 Agent 建议。
- `docs/agent-skill.md`：说明项目级 Agent Entry 与平台 Skill 适配关系。
- `docs/agent-playbook.md`：Agent 实施 open-cowork 时的操作规则。
- `docs/specs/`：当前有效协议规格。
- `docs/archive/`：历史证据，不是当前实施入口。

## 一句话总结

`open-cowork` 的价值不是让人多背一套流程，而是让多个 Agent 和多个 AI Coding 环境在同一个项目里，按同一套轻量、可验证的项目事实协作和接续。

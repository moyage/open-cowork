# v0.3.7 团队采用模式与接手摘要

本规格定义 v0.3.7 的设计基线：在 v0.3.6 的确定性接续和可合并治理布局之上，为团队采用、成员边界和长任务接手提供最小可执行能力。

v0.3.7 的目标不是把 open-cowork 做成统一 Agent runtime、GUI 平台或 skills/commands 仓库，而是让多个拥有个人域 AI 能力的“超级个体”能围绕同一个项目事实层持续协作。

## 外露原则

v0.3.7 增加的英文名主要是 Agent 内部结构名，不应成为团队日常操作语言。

| 内部名 | 对人/团队的说法 | 是否需要人操作 |
| --- | --- | --- |
| Adoption Profile | 协作模式 | 通常由 Agent 推荐，人只确认协作强度是否合适。 |
| Participant Profile | 成员/Agent 职责边界 | 人只确认关键 owner、reviewer 和权限，不填写 schema。 |
| Context Pack | 接手资料索引 | 不需要人读；给新会话或另一个 Agent 降低上下文成本。 |
| Compact Handoff | 接手摘要 | 人可读，但默认由 Agent 消费。 |
| recommended read set | 建议先读哪些材料 | Agent 内部读取顺序。 |
| activation payload / Agent instruction | 接手入口返回值 / Agent 操作提示 | Agent 内部协议，不面向普通团队成员。 |

## 目标

- 提供固定协作模式，帮助 Agent 为个人、多 Agent 和团队任务选择最小足够治理控制。
- 提供成员职责边界，记录参与者角色、权限、审查资格和工作边界。
- 提供接手资料索引和接手摘要，降低长任务、跨会话和跨 Agent 接续时的上下文负担。
- 让接续入口优先推荐读取接手资料索引，再指向当前 change 的权威事实。

## 非目标

- 不引入 OMOC / OMC / OMX 类 runtime。
- 不引入 GUI、desktop app、web platform 或中心化服务。
- 不实现 profile inheritance DSL、复杂 policy engine 或外部事件 ingestion。
- 不让接手资料索引取代 intent、contract、bindings、verify、review、archive receipt 等权威事实。

## 协作模式

协作模式是 Agent 为当前项目选择治理强度时使用的基础档位。它必须固定、可审计、易解释，而不是任意脚本或运行时插件。

基础档位包括：

- `core` / 轻量协作：低风险单人或单 Agent 工作。
- `personal-multi-agent` / 个人多 Agent 协作：一个人调度多个个人域 Agent。
- `team-standard` / 团队标准协作：普通团队任务的默认选择。
- `team-strict` / 团队严格协作：发布、安全、数据、合规或影响面较大的任务。

大量资料阅读不是一个基础档位，而是可叠加模式。Agent 可以在上述任意基础档位上启用“大量资料阅读模式”，用于缩小先读材料、分批阅读和设置压缩检查点。

选择原则：

- 默认由 Agent 根据项目风险、参与人数、资料量和变更影响面推荐。
- 人或团队只需要确认“轻量 / 标准 / 严格”的治理强度是否合适。
- 团队不需要记忆 profile id；id 是 Agent 和 CLI 的内部标识。

实现要求：

- `ocw profile list` 必须列出可用 profile。
- `ocw profile show <profile-id>` 必须展示 profile 的控制、默认项和禁止项。
- `ocw profile apply <profile-id>` 必须写入 `.governance/profiles/adoption.yaml`。

## 成员职责边界

成员职责边界记录参与者能力和边界。它描述“谁可以做什么”，但不替代 active change 的 `bindings.yaml`。

最小字段应覆盖：

- participant id 和类型。
- 可承担角色。
- 审查资格，尤其是不能审查自己的最终执行。
- authority，例如是否可批准 Step 5、是否可记录 evidence、是否可 archive。
- working boundaries，例如 allowed paths 和 forbidden paths。

默认实现应在 `.governance/participants/` 下生成 human sponsor 与当前 Agent 的职责边界文件，且不能覆盖已有自定义文件。

## 接手资料索引

接手资料索引是当前 change 的压缩索引。它只能指向权威事实，不能成为新的权威事实。

最小内容包括：

- `context_pack_version`
- `change_id`
- `pack_level`
- `authoritative_reads`
- `supporting_reads`
- `optional_deep_reads`
- `summary`
- `compression_notes`

实现要求：

- `ocw context-pack create --change-id <id>` 写入 `.governance/changes/<id>/context/context-pack.yaml` 和 `.governance/changes/<id>/context/context-pack.md`。
- `authoritative_reads` 必须优先包含 manifest、intent confirmation、contract、bindings、verify 和 review 中已存在的文件。
- `optional_deep_reads` 可以指向 source docs，但 Agent 不应默认全文展开。
- `compression_notes` 必须明确接手资料索引不是权威事实。

## 接手摘要

接手摘要是给新会话或另一个 Agent 的短摘要。它可以让人读懂状态，但默认由 Agent 消费。

实现要求：

- `ocw handoff --compact --change-id <id>` 写入 `.governance/changes/<id>/context/handoff-compact.md`。
- handoff 必须包含当前 step、status、owner、blocked、next decision 和 recommended read set。
- recommended read set 必须先指向 context pack，再指向权威事实。

## 接续入口集成

当当前 change 已存在接手资料索引或接手摘要时，接续入口返回的建议读取顺序必须优先包含这些文件，再包含 contract、bindings、step report 等权威材料。

Agent 操作提示必须提醒：接手资料索引只是权威事实的索引和压缩摘要，不是权威事实本身。

## 验收要求

v0.3.7 必须满足：

- 可以列出、查看和应用协作模式。
- 应用协作模式后生成协作模式和成员职责边界文件。
- 可以为 active change 生成接手资料索引和接手摘要。
- 接续入口的建议读取顺序会包含接手资料索引。
- 全量测试通过，并覆盖上述行为。

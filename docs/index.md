# open-cowork 文档地图

本目录只保留当前使用 open-cowork 所需的说明和规格。历史计划、过程报告和中间产出物不应成为新用户和 Agent 的默认入口；需要追溯演进时请查看 Git 历史、release artifacts 或明确指定的冷历史材料。

## 普通读者先看

| 文件 | 用途 |
| --- | --- |
| `../README.md` | 一页理解 open-cowork 是什么、怎么让 Agent 使用、9 个步骤叫什么。 |
| `glossary.md` | 解释 Round、Scope、Evidence refs、Role bindings、Continuity、Gate、Digest 等术语。 |
| `getting-started.md` | 安装、试用、升级、恢复和个人域多 Agent 建议。 |
| `agent-skill.md` | 说明目标项目中 `.governance/agent-entry.md` 与平台 Skill 适配的关系。 |

## Agent 执行面

| 文件 | 用途 |
| --- | --- |
| `../AGENTS.md` | 仓库级 Agent-first 入口。 |
| `agent-playbook.md` | Agent 如何维护 `.governance/` 当前状态、汇报进展、处理 handoff。 |
| `agent-adoption.md` | Agent 如何把 open-cowork 应用到目标项目。 |
| 目标项目 `.governance/AGENTS.md` | 已实施项目里的 Agent 入口。 |
| 目标项目 `.governance/agent-entry.md` | 任意 Agent 进入项目后的固定激活与汇报规则。 |
| 目标项目 `.governance/current-state.md` | 新会话或另一个 Agent 接续时优先读取的当前状态摘要。 |
| 目标项目 `.governance/state.yaml` | 当前 round、角色、gate 和 lifecycle 的 compact 权威状态。 |
| 目标项目 `.governance/evidence.yaml` | 有界证据引用。 |
| 目标项目 `.governance/ledger.yaml` | closeout、迁移 receipt 和接续记录。 |

旧版项目中的 `active-changes.yaml` 只作为兼容读取和迁移识别对象出现；v0.3.11 新项目默认使用 `state.yaml` / `current-state.md` / `evidence.yaml` / `ledger.yaml`。

## 当前有效规格

`docs/specs/` 是当前协议规格，不是历史过程记录。

| 文件 | 用途 |
| --- | --- |
| `specs/00-overview.md` | 协议定位、目标和项目事实层。 |
| `specs/01-runtime-flow.md` | 4 阶段 / 9 步运行流、gate 与 acknowledgement 语义。 |
| `specs/02-change-package-and-contract.md` | 旧模型与 contract 兼容语义；v0.3.11 后新项目默认使用 round scope。 |
| `specs/03-evidence-review-archive.md` | Evidence、Verify、Review、Closeout 和 review lifecycle。 |
| `specs/04-agent-adoption-and-doc-governance.md` | Agent-first 实施、project activation 和文档治理。 |
| `specs/08-v0311-current-state-reset.md` | v0.3.11 当前状态收敛与迁移规格。 |

## 真相源优先级

1. 目标项目 `.governance/**`：运行时项目事实。
2. `README.md`、`AGENTS.md`、`docs/agent-playbook.md`：当前人类和 Agent 入口。
3. `docs/specs/08-v0311-current-state-reset.md`：当前状态收敛与迁移规格。
4. 其他规格、Git 历史 / release artifacts：兼容背景和历史演进。

## 历史证据，不是当前实施入口

不要默认全文扫描历史材料。Agent 应读取当前项目入口给出的 recommended read set，只在需要追溯来源时按明确路径打开历史文件。旧版大量历史治理目录迁移后的 cold history 也遵守同一原则。

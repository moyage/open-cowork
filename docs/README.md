# open-cowork 文档地图

本目录只保留当前使用 open-cowork 所需的说明和规格。历史计划、过程报告和中间产出物已经从主文档树清理；需要追溯演进时请查看 Git 历史或 release artifacts。

## 普通读者先看

| 文件 | 用途 |
| --- | --- |
| `../README.md` | 一页理解 open-cowork 是什么、怎么让 Agent 使用、9 个步骤叫什么。 |
| `glossary.md` | 解释 Contract、Evidence、Bindings、Continuity、Gate、Digest 等术语。 |
| `getting-started.md` | 安装、试用、升级、恢复和个人域多 Agent 建议。 |
| `agent-skill.md` | 说明目标项目中 `.governance/agent-entry.md` 与平台 Skill 适配的关系。 |

## Agent 执行面

| 文件 | 用途 |
| --- | --- |
| `../AGENTS.md` | 仓库级 Agent-first 入口。 |
| `agent-playbook.md` | Agent 如何维护 `.governance/`、汇报进展、处理 handoff。 |
| `agent-adoption.md` | Agent 如何把 open-cowork 应用到目标项目。 |
| 目标项目 `.governance/AGENTS.md` | 已实施项目里的 Agent 入口。 |
| 目标项目 `.governance/current-state.md` | 新会话或另一个 Agent 接续时优先读取的当前状态。 |
| 目标项目 `.governance/index/active-changes.yaml` | 同一项目内并行需求 / 并行 change 的列表。 |
| 目标项目 `.governance/agent-entry.md` | 任意 Agent 进入项目后的固定激活与汇报规则。 |

## 当前有效规格

`docs/specs/` 是当前协议规格，不是历史过程记录。

| 文件 | 用途 |
| --- | --- |
| `specs/00-overview.md` | 协议定位、目标和项目事实层。 |
| `specs/01-runtime-flow.md` | 4 阶段 / 9 步运行流、gate 与 acknowledgement 语义。 |
| `specs/02-change-package-and-contract.md` | 变更包、Contract、scope 和 baseline separation。 |
| `specs/03-evidence-review-archive.md` | Evidence、Verify、Review、Archive 和 review lifecycle。 |
| `specs/04-agent-adoption-and-doc-governance.md` | Agent-first 实施、project activation 和文档治理。 |

## 真相源优先级

1. 目标项目 `.governance/**`：运行时项目事实。
2. `README.md`、`AGENTS.md`、`docs/agent-playbook.md`：当前人类和 Agent 入口。
3. `docs/specs/`：当前协议规格。
4. Git 历史 / release artifacts：历史计划、历史报告和 dogfood 过程记录。

## 历史证据，不是当前实施入口

不要默认全文扫描历史材料。Agent 应读取当前 active change 的 recommended read set，只在需要追溯来源时按明确路径打开历史文件。

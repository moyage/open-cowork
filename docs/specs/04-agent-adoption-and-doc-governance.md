# 04. Agent Adoption and Doc Governance

## Agent-first 使用方式

人的默认入口是对 Agent 说：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

Agent 负责安装、初始化、准备 change package、维护 `.governance/`、运行内部 CLI，并用人能理解的语言汇报当前状态。

## Project activation

已实施 open-cowork 的项目应使用 `ocw activate` 接续。activation 输出：

- project scope
- active change
- current step
- owner / waiting_on / next_decision
- recommended read set
- Agent instructions

这保证 open-cowork 作用在项目上，而不是绑定在某个 Agent 会话上。

v0.3.5 起，项目级 activation 支持并行 active changes：

- `.governance/index/active-changes.yaml` 记录所有未归档、未废弃、未 supersede 的 change。
- 如果只有一个 active change，Agent 可以直接接续。
- 如果有多个 active changes，Agent 必须显式选择 change_id，或让人指定“需求 1 / 需求 2”对应的 change。
- `ocw activate --change-id <change-id>` 可以在 Codex、Claude Code、Hermes、OMOC 或新会话中接续同一个项目事实。
- Agent 不得从聊天历史猜测当前 change。

## 文档治理

仓库文档分三层：

1. 人类入口：`README.md`、`docs/index.md`、`docs/glossary.md`、`docs/getting-started.md`
2. Agent 执行面：`AGENTS.md`、`docs/agent-skill.md`、`docs/agent-playbook.md`、`docs/agent-adoption.md`
3. 当前规格：`docs/specs/`

历史 plans、reports 和中间产出物不再保留在主仓库文档树中。需要追溯历史时应通过 Git 历史或 release artifacts 查看。

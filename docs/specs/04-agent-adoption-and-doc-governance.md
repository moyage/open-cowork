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

## 文档治理

仓库文档分三层：

1. 人类入口：`README.md`、`docs/README.md`、`docs/glossary.md`、`docs/getting-started.md`
2. Agent 执行面：`AGENTS.md`、`docs/agent-playbook.md`、`docs/agent-adoption.md`
3. 当前规格：`docs/specs/`

历史 plans、reports 和中间产出物不再保留在主仓库文档树中。需要追溯历史时应通过 Git 历史或 release artifacts 查看。

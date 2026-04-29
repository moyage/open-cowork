# v0311-docs-agent-entry 验证结果

时间：2026-04-29 15:24:07 HKT

## 恢复方式

- 失败会话：`019dd7aa-04a5-7570-9556-a04285ed177e`
- 恢复工具：`/Users/mlabs/.codex/bin/codex-session-recover 019dd7aa-04a5-7570-9556-a04285ed177e`
- 恢复产物：`/Users/mlabs/.codex/recovery/session-019dd7aa-04a5-7570-9556-a04285ed177e-handoff.md`
- 本轮没有回读失败会话 JSONL 全文，只读取 handoff 摘要并继续任务 12 文档收口。

## 范围

本轮文档收口覆盖：

- `README.md`
- `docs/README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/agent-playbook.md`
- `docs/agent-skill.md`
- `docs/glossary.md`
- `.governance/AGENTS.md`
- `.governance/README.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`
- `.governance/current-state.md`

## 扫描结果

定向扫描当前入口文档：

```text
rg -n "\.governance/(changes|archive|runtime|index|local)" README.md docs/README.md docs/getting-started.md docs/agent-adoption.md docs/agent-playbook.md docs/agent-skill.md docs/glossary.md .governance/AGENTS.md .governance/agent-entry.md .governance/agent-playbook.md .governance/current-state.md .governance/README.md || true
```

结果：无输出。当前入口文档没有把旧 heavy layout 描述为 v0.3.11 默认操作模型。

宽扫描：

```text
rg -n "\.governance/(changes|archive|runtime|index|local)" README.md docs .governance -g '*.md' || true
```

结果：仍有命中，但命中位于历史规格、旧 review、旧模板和 v0.3.11 reset 计划 / 规格中的兼容、迁移或历史说明，不属于当前默认入口文档。

## 测试结果

v0.3.11 专项测试：

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'
```

结果：31 tests OK。

v0.34 / v0.35 文档兼容测试：

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v03[45].py'
```

结果：14 tests OK。

全量测试：

```text
PYTHONPATH=src python3 -m unittest discover -s tests
```

结果：278 tests OK。

## 已知兼容事实

- 当前仓库处于 v0.3.11 lean reset 过渡期，旧规格和历史 review 中仍会提到旧 heavy layout。
- `.governance/state.yaml`、`.governance/evidence.yaml`、`.governance/ledger.yaml`、`.governance/rules.yaml` 尚未在本仓库 dogfood 迁移中落地；文档按 v0.3.11 目标模型说明，新会话进入时若缺失应走迁移 / verify 流程。
- 本轮未创建旧 `.governance/index/**`，也未把旧目录恢复为默认模型。

## Hermes revise 后复验证据

Hermes 第一轮 review 返回 `revise`，要求：

1. `.governance/current-state.md` 从 Step 6 / review 前语态更新为 Step 8 / 独立审查修订状态，并明确历史批次 approve 与当前批次 review 状态的区别。
2. `.governance/agent-entry.md` 精确区分单 active round 可直接接续与多 active rounds 需要选择目标。

修正后复验：

```text
rg -n "\.governance/(changes|archive|runtime|index|local)" README.md docs/README.md docs/getting-started.md docs/agent-adoption.md docs/agent-playbook.md docs/agent-skill.md docs/glossary.md .governance/AGENTS.md .governance/agent-entry.md .governance/agent-playbook.md .governance/current-state.md .governance/README.md || true
```

结果：无输出。

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'
```

结果：31 tests OK。

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v03[45].py'
```

结果：14 tests OK。

```text
PYTHONPATH=src python3 -m unittest discover -s tests
```

结果：278 tests OK。

# v0311-docs-agent-entry closeout

## 结果

本批次完成 open-cowork v0.3.11 lean protocol reset 的文档与 Agent-first 入口收口。

完成内容：

- `README.md` 重写为 v0.3.11 lean 默认模型入口，保留 Agent-first 使用方式。
- `docs/getting-started.md`、`docs/agent-adoption.md`、`docs/agent-playbook.md`、`docs/agent-skill.md`、`docs/glossary.md`、`docs/README.md` 更新为当前文档入口。
- `.governance/AGENTS.md`、`.governance/agent-entry.md`、`.governance/agent-playbook.md`、`.governance/README.md`、`.governance/current-state.md` 更新为 lean 接手规则和当前状态。
- 旧 heavy layout、`active-changes.yaml`、contract / change package 仅保留为兼容、迁移或术语背景，不再作为当前默认模型。

## 验证

- 定向入口文档扫描旧 heavy layout 默认路径：无输出。
- `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'`：31 tests OK。
- `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v03[45].py'`：14 tests OK。
- `PYTHONPATH=src python3 -m unittest discover -s tests`：278 tests OK。

详见 `.agent-state/tasks/v0311-docs-agent-entry/verify-result.md`。

## Review

- 第一轮 Hermes review：`revise`
- 修正后 Hermes 复审：`approve`

详见 `.agent-state/tasks/v0311-docs-agent-entry/hermes-review.md`。

## Carry-forward

建议下一段继续处理：

1. open-cowork 自身 dogfood 迁移，落地 lean `state.yaml`、`evidence.yaml`、`ledger.yaml`、`rules.yaml`。
2. 处理 `ocw resume` 在仅有 lean `.governance/`、缺少旧 `.governance/index/current-change.yaml` 时的兼容行为。
3. 根据 release checklist 准备 v0.3.11 发布前验证、版本标记和变更说明。

## 收束状态

本批次已完成执行、验证和独立 review，可进入下一段 dogfood / release-prep 工作。

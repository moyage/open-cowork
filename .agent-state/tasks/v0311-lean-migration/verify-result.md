# v0.3.11 lean migration 验证结果

## 范围

- 本轮任务：`v0311-lean-migration`
- 目标：补齐旧安装 detect、dry-run migrate、confirm migrate、migration verify、cleanup receipt 与 uninstall 基础能力。

## 已执行命令

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_migration.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_cli.py'
PYTHONPATH=src python3 -m unittest discover -s tests
```

## 结果

- `tests/test_v0311_migration.py`：7 个测试通过。
- `tests/test_v0311_*.py`：27 个测试通过。
- `tests/test_cli.py`：55 个测试通过。
- 完整测试套件：274 个测试通过。

## 备注

- `python3 -m unittest discover` 形式是本仓库当前可用的稳定测试入口。
- 本轮迁移实现默认保守：`dry-run` 不移动文件；`--confirm` 才执行迁移或卸载；cleanup 默认保留 cold legacy 审计文件并写 receipt。
- Hermes 首轮独立 review 给出 `revise` 后，已补强 migration verify、cleanup 输出语义与 uninstall receipt 审计信息，并重新跑通完整测试。

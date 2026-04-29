# v0.3.11 pressure guards 验证结果

## 范围

- 本轮任务：`v0311-pressure-guards`
- 目标：补齐上下文预算、默认读取集和 legacy heavy 目录回归守卫。

## 已执行命令

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_pressure.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_cli.py'
PYTHONPATH=src python3 -m unittest discover -s tests
```

## 结果

- `tests/test_v0311_pressure.py`：4 个测试通过。
- `tests/test_v0311_*.py`：31 个测试通过。
- `tests/test_cli.py`：55 个测试通过。
- 完整测试套件：278 个测试通过。

## 覆盖点

- 模拟 100 轮 compact ledger/evidence 历史后，默认读取集仍固定为 4 个文件。
- `current-state.md` 保持 200 行以内，`state.yaml` 保持 400 行以内。
- cold legacy history 不进入默认读取集。
- lean init/status 不创建 `changes`、`archive`、`runtime`、`index`、`local` legacy heavy 目录。
- execution gate 在直接入口和 status 入口中结果一致。

## 独立 Review

- Hermes 独立复核 decision：`approve`。
- Hermes 复跑 `test_v0311_pressure.py`：4 个测试通过。
- Hermes 实测默认读取集总字节数：2929。
- Hermes 实测 `current-state.md` 行数：13。
- Hermes 实测 `state.yaml` 行数：137。

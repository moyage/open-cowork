# Milestone 2：Sync History Target Layer Summary 实施计划

## 范围

本次只实现：
- `--summary-by target_layer`
- 对应 continuity grouped summary 支持
- 对应 CLI 文本输出支持

## 实施步骤

1. 先补失败测试
- continuity：跨月 grouped summary 支持 `target_layer`
- CLI：文本输出支持 `target_layer`

2. 最小实现
- 扩展 `--summary-by` 允许值
- 复用现有 grouped summary helper

3. 回归验证
- `test_continuity.py`
- `test_cli.py`
- 全量 `unittest discover`

## 风险控制

1. 不修改底层事件结构。
2. 不新增命令。
3. 不改变已有 grouped summary 字段模型，只增加一个合法维度。

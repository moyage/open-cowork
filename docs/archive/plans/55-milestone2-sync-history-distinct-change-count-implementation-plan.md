# Milestone 2：Sync History Distinct Change Count 实施计划

## 范围

本次只实现：
- grouped summary 增加 `distinct_change_count`
- 文本 grouped summary 增加 `distinct_changes=...`

## 实施步骤

1. 先补失败测试
- continuity：grouped summary 暴露 `distinct_change_count`
- CLI：文本 grouped summary 打印 `distinct_changes=...`

2. 最小实现
- grouped helper 内部统计每组的唯一 `change_id`
- 在最终 payload 中输出 `distinct_change_count`
- 文本输出增加该字段

3. 回归验证
- `test_continuity.py`
- `test_cli.py`
- 全量 `unittest discover`

## 风险控制

1. 不修改底层 sync-history 事件结构。
2. 不改变 grouped summary 现有字段语义。
3. 只增加一个新的派生统计字段。

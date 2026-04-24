# Milestone 2：Sync History Group Latest Metadata 实施计划

## 范围

本次只实现：
- grouped summary 增加 `latest_change_id`
- grouped summary 增加 `latest_sync_kind`
- 文本输出显示这两个字段

## 实施步骤

1. 先补失败测试
- continuity：grouped summary 暴露 `latest_change_id/latest_sync_kind`
- CLI：文本 grouped summary 打印这两个字段

2. 最小实现
- 在 grouped summary helper 中，当最新事件更新时，同步更新：
  - `latest_change_id`
  - `latest_sync_kind`
- 在 CLI 文本输出中补打印

3. 回归验证
- `test_continuity.py`
- `test_cli.py`
- 全量 `unittest discover`

## 风险控制

1. 不新增命令。
2. 不修改底层 sync-history 事件 schema。
3. 只扩 grouped summary 的派生字段，不改变默认查询语义。

# Milestone 2：Sync History Summary Only 实施计划

## 范围

本次只实现：
- `sync-history-query` 新增 `--summary-only`
- continuity 查询层支持 `summary_only`
- 文本输出在 `summary_only` 下不再打印事件列表

## 实施步骤

1. 先补失败测试
- continuity：`summary_only=True` 时 `events=[]`
- CLI：文本输出只保留 grouped summary，不再输出原始事件行

2. 实现 continuity 参数透传
- `read_sync_history(..., summary_only=False)`
- `read_sync_history_across_months(..., summary_only=False)`

3. 实现 CLI 参数
- `--summary-only`

4. 调整文本输出
- 保留 `grouped summary by: ...`
- 跳过原始事件列表打印

5. 全量回归
- 目标：全量 `unittest discover`

## 风险控制

1. 不修改底层 sync-history 文件结构。
2. 默认行为保持不变。
3. JSON/YAML 消费方只有显式传入时才收到 `events=[]` 的轻量视图。

# Milestone 2 digest grouped sync summary 实施计划

## 1. 目标

为 `continuity digest` 增加 `recent_sync_grouped_summary`，并在文本输出中展示最小 grouped sync 摘要。

## 2. 实施步骤

### Step 1. 先写失败测试

新增：

1. `test_resolve_continuity_digest_includes_grouped_sync_summary_by_target_layer`
2. `test_continuity_digest_text_output_includes_grouped_sync_summary`

先确认：

1. payload 中当前不存在该字段
2. 文本输出当前不存在该段落

### Step 2. 实现最小派生逻辑

在 `continuity.py` 中新增：

1. `_recent_sync_grouped_summary_for_change(...)`

实现方式：

1. 直接复用 `read_sync_history_across_months(...)`
2. 固定 `summary_by=\"target_layer\"`
3. 使用 `summary_only=True`

### Step 3. 接入 digest payload

在 active / archived digest 两条路径中：

1. 如果 grouped summary 存在，则写入 `recent_sync_grouped_summary`

### Step 4. 接入文本输出

在 `cmd_continuity_digest` 中：

1. 打印 `recent sync groups: target_layer`
2. 逐组打印最小摘要字段

## 3. 验证

1. 先跑新增的两个定向测试
2. 再跑全量：

```bash
python3 -m unittest discover -s tests -v
```

## 4. 退出条件

满足以下条件即可结束：

1. `digest` payload 新增 grouped sync 摘要
2. 文本输出可直接阅读该摘要
3. 不修改任何底层 `sync-history` 文件结构
4. 全量测试保持通过

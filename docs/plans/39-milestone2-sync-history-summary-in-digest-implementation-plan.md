# open-cowork Milestone 2 Sync History Summary in Digest 实施计划

## 1. 文档目的

本实施计划用于指导 `continuity digest` 中最小 `sync-history` 聚合摘要的实现。

## 2. 本轮目标

完成后应具备：

1. `resolve_continuity_digest(...)` 在匹配事件存在时输出 `recent_sync_summary`
2. `continuity digest --format text` 输出最近同步摘要
3. 不新增新的事实文件与命令入口

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `src/governance/cli.py`
3. `tests/test_continuity.py`
4. `tests/test_cli.py`
5. `docs/README.md`

### 3.2 不纳入

1. 新增独立 summary 命令
2. 趋势/图表
3. 多 change 聚合摘要

## 4. 设计约束

1. 继续保持 `digest` 为只读派生层。
2. 只复用现有 `sync-history` 数据。
3. 没有事件时必须省略 `recent_sync_summary`，而不是输出空壳。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_resolve_continuity_digest_includes_recent_sync_summary_when_history_exists`
2. `test_continuity_digest_text_output_includes_recent_sync_summary`

### Step 2. 实现 helper

建议新增：

1. `_recent_sync_summary_for_change(...)`

### Step 3. 接入 digest

1. `resolve_continuity_digest(...)` 补 `recent_sync_summary`
2. `cmd_continuity_digest(...)` 补文本输出

### Step 4. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. 有历史时能看到最近同步摘要
2. 无历史时保持静默省略
3. 全量测试通过

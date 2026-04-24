# open-cowork Milestone 2 Digest Recent Runtime Events 实施计划

## 1. 文档目的

本实施计划用于指导 `continuity digest` 中最近关键运行事件压缩视图的最小实现。

## 2. 本轮目标

完成后应具备：

1. `resolve_continuity_digest(...)` 在有 runtime timeline 时输出 `recent_runtime_events`
2. `continuity digest --format text` 输出最近关键运行事件摘要
3. 不新增新的命令与事实文件

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `src/governance/cli.py`
3. `tests/test_continuity.py`
4. `tests/test_cli.py`
5. `docs/README.md`

### 3.2 不纳入

1. 跨月事件历史摘要
2. 独立 runtime event summary 命令
3. dashboard / TUI

## 4. 设计约束

1. 继续保持 `digest` 为只读派生层。
2. 只复用现有 `runtime/timeline` 文件。
3. 没有事件时必须省略 `recent_runtime_events`。
4. 默认最多展示最近 3 条。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_resolve_continuity_digest_includes_recent_runtime_events_when_timeline_exists`
2. `test_continuity_digest_text_output_includes_recent_runtime_events`

### Step 2. 实现 helper

建议新增：

1. `_recent_runtime_events_for_change(...)`

### Step 3. 接入 digest

1. active / archived digest 都可挂 `recent_runtime_events`
2. text 输出补摘要行

### Step 4. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. 有 timeline 时能看到最近关键事件
2. 无 timeline 时保持静默省略
3. 全量测试通过

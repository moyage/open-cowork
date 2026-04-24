# open-cowork Milestone 2 Continuity / Sync Digest 实施计划

## 1. 文档目的

本实施计划用于指导 continuity / sync digest 的最小实现。

## 2. 本轮目标

完成后应具备：

1. `resolve_continuity_digest(...)`
2. `ocw continuity digest`
3. 自动选择 current active / last archived
4. `text / yaml / json` 输出

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `src/governance/cli.py`
3. `tests/test_continuity.py`
4. `tests/test_cli.py`
5. `docs/README.md`

### 3.2 不纳入

1. 批量 digest
2. dashboard / tui
3. 新 packet schema
4. runtime status 改写

## 4. 设计约束

1. digest 必须是只读派生层。
2. 不新增新的事实写入文件。
3. 当前 active 优先于 last archived。
4. 若无 current active 且无 last archived，应 fail fast。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_resolve_continuity_digest_prefers_current_active_change`
2. `test_resolve_continuity_digest_falls_back_to_last_archived_change`
3. `test_continuity_digest_command_supports_json_output`
4. `test_continuity_digest_command_supports_text_output`

### Step 2. 实现 helper

建议新增：

1. `_select_digest_change(...)`
2. `resolve_continuity_digest(...)`

### Step 3. 实现 CLI

新增：

1. `cmd_continuity_digest(args)`
2. `continuity digest` parser

### Step 4. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. active / archived 两条路径都能生成 digest
2. 自动选择逻辑成立
3. 输出可用
4. 全量测试通过

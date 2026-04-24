# open-cowork Milestone 2 Sync History And External Export 实施计划

## 1. 文档目的

本实施计划用于指导 `Milestone 2` 中 `sync history / external export` 的最小实现。

目标不是做完整上层同步平台，而是先把：

- `sync-packet` 的项目内 append-only 历史
- `sync-packet` 的显式外部导出

做成可运行、可测试、可持续扩展的一层协议增强。

## 2. 目标

本轮实现完成后，应具备：

1. `append_sync_history(...)`
2. `export_sync_packet(...)`
3. `ocw continuity sync-history ...`
4. `ocw continuity export-sync-packet ...`
5. 最小 history 与 export 测试覆盖

## 3. 范围

### 3.1 纳入

1. sync history 追加逻辑
2. 最小去重逻辑
3. external export 目录生成
4. README / export-manifest 最小输出
5. CLI 与测试

### 3.2 不纳入

1. history list / query
2. 远端推送
3. 自动投递到其他系统
4. export 版本管理
5. 可视化界面

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/paths.py`
   - 新增 sync history 路径函数
2. `src/governance/continuity.py`
   - 新增 history / export 原语
3. `src/governance/cli.py`
   - 新增 `continuity sync-history`
   - 新增 `continuity export-sync-packet`
4. `tests/test_continuity.py`
   - 新增 history / export 单元测试
5. `tests/test_cli.py`
   - 新增 history / export CLI 测试
6. `docs/README.md`
   - 接入索引

## 5. 设计约束

实现时必须遵守：

1. `sync-history` 必须是 append-only 的。
2. 同一 `sync-packet` 不应重复写入相同 history 事件。
3. external export 必须显式指定输出目录。
4. export 只导出最小文件集，不复制完整 `.governance`。
5. export README 只能是说明层，不能成为新 truth-source。

## 6. 推荐实现步骤

### Step 1. 扩展路径层

新增建议：

1. `sync_history_month_file(month_key: str | None = None) -> Path`
2. `external_export_dir(output_root: str | Path, change_id: str) -> Path`（如需要可做辅助函数）

### Step 2. 在 continuity.py 中新增 history 原语

建议新增：

1. `append_sync_history(...)`
2. `_merge_sync_history_events(...)`

### Step 3. 在 continuity.py 中新增 export 原语

建议新增：

1. `export_sync_packet(...)`
2. `_render_sync_export_readme(...)`

### Step 4. 新增 CLI 命令

建议新增：

```bash
ocw continuity sync-history ...
ocw continuity export-sync-packet ...
```

### Step 5. 单元测试

建议至少新增以下测试：

1. `test_append_sync_history_from_closeout_sync_packet`
2. `test_append_sync_history_deduplicates_same_packet`
3. `test_export_sync_packet_writes_minimum_external_bundle`
4. `test_export_sync_packet_fails_when_source_packet_missing`

### Step 6. CLI 测试

建议新增以下测试：

1. `test_continuity_sync_history_command_appends_output`
2. `test_continuity_export_sync_packet_command_materializes_external_bundle`

## 7. 测试命令

```bash
python3 -m unittest discover -s tests -v
```

## 8. 退出条件

满足以下条件即可视为本轮成立：

1. sync-packet 可被写入项目内 history
2. 同一 packet 不重复写 history
3. 可显式导出最小 external bundle
4. 全量测试通过

## 9. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. sync history list / query
2. 更高层只读消费接口
3. export 与 sponsor-facing 阅读入口整合

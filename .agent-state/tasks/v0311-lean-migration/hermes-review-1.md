# Hermes 独立 Review 记录 1

## 调度

- Reviewer：Hermes Agent v0.11.0
- 调度方式：`hermes chat -q`
- 范围：`src/governance/lean_migration.py`、`src/governance/cli.py` 中迁移/清理/卸载相关变更、`tests/test_v0311_migration.py`、本任务目录。
- 模式：只读 review，未授权修改文件。

## Decision

`revise`

## 阻断项摘要

1. `verify_migration()` 只检查 lean 文档和 migration receipt 是否存在，没有校验 receipt 中 `moved` 条目与磁盘状态一致，也没有检查 live legacy heavy 目录是否仍存在。
2. `cleanup_legacy()` 实际保留 cold legacy 审计文件并写 receipt，但 CLI 输出“清理完成”，容易让人误以为执行了物理删除。
3. `uninstall_governance()` 的 receipt 审计信息过薄，只记录 `.governance` 被移除，缺少卸载前 detect 报告、协议版本和 legacy 状态概貌。

## 已处理

- migration verify 已补强：校验 live legacy heavy 目录、receipt `moved` 条目完整性、source 不再存在、target 仍存在。
- cleanup CLI 输出已改为“清理确认已记录，未执行物理删除”。
- uninstall receipt 已加入 `pre_uninstall_detect_report`，记录卸载前 protocol version、legacy dirs、active legacy change、archive 与 cleanup candidates。
- 新增测试覆盖上述修复。

## 修复后验证

```text
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_migration.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_cli.py'
PYTHONPATH=src python3 -m unittest discover -s tests
```

结果：274 个完整测试通过。

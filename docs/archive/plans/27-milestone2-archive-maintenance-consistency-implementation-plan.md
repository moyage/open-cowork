# open-cowork Milestone 2 Archive Map / Maintenance Status Consistency 实施计划

## 1. 文档目的

本实施计划用于指导 `archive-map` 与 `maintenance-status` 最近归档基线交叉一致性的最小实现。

目标不是做完整索引修复器，而是先把：

1. `last_archived_change` 必须存在于 `archive-map`
2. `last_archive_at` 必须和 `archive-map` 对齐

做成可测试、可解释、可继续扩展的一层约束。

## 2. 目标

本轮实现完成后，应具备：

1. `set_maintenance_status(...)` 对最近归档基线的 archive-map 存在性校验
2. `set_maintenance_status(...)` 对 `archived_at` 的最小一致性校验
3. 对应单元测试
4. 文档索引与 Baseline 同步

## 3. 范围

### 3.1 纳入

1. `archive-map` 查找辅助逻辑
2. maintenance recent archive baseline consistency check
3. 测试与文档

### 3.2 不纳入

1. archive-map 文件系统真实性扫描
2. 自动修复逻辑
3. 多 entry 冲突治理
4. continuity / retrospective / recovery 的额外补救逻辑

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/index.py`
   - 扩展 `set_maintenance_status(...)`
2. `tests/test_governance_index.py`
   - 新增最近归档基线一致性测试
3. `docs/README.md`
   - 接入索引

## 5. 设计约束

实现时必须遵守：

1. 不影响 archive 主链的现有执行顺序；
2. 不触碰最近归档基线字段的普通 maintenance 更新不应受影响；
3. 一致性校验只在最近归档基线更新时触发；
4. 错误信息要能直接说明是 archive-map 缺失还是时间不一致。

## 6. 推荐实现步骤

### Step 1. 先写失败测试

新增建议：

1. `last_archived_change` 指向 archive-map 中不存在的 change -> 失败
2. `last_archive_at` 与 archive-map entry 不一致 -> 失败

### Step 2. 补合法通过测试

新增建议：

1. 与 archive-map 对齐的最近归档基线更新 -> 通过
2. 不触碰最近归档字段的普通 maintenance 更新 -> 通过

### Step 3. 实现最小 archive-map 交叉校验

建议新增：

1. `_ensure_archive_baseline_resolves_in_archive_map(...)`
2. `_find_archive_entry_by_change_id(...)`

### Step 4. 回归验证

先定向：

```bash
python3 -m unittest discover -s tests -p 'test_governance_index.py' -v
```

再全量：

```bash
python3 -m unittest discover -s tests -v
```

## 7. 退出条件

满足以下条件即可视为本轮成立：

1. 最近归档基线不能指向 archive-map 中不存在的对象
2. 最近归档时间不能与 archive-map 自相矛盾
3. archive 主链与普通 maintenance 更新不受影响
4. 全量测试通过

## 8. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. continuity / closeout / sync refs 的一致性收紧
2. archive-map 与实际 archive receipt 的更强一致性

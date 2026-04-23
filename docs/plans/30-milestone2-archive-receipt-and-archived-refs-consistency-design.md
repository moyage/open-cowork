# open-cowork Milestone 2 Archive Receipt / Archived Refs Consistency 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 下一段最小工作包正式收口为：

> `archive receipt / archive-map / archived continuity refs consistency`

上一轮我们已经完成：

1. `maintenance-status` 的最近归档锚点必须能回指到 `archive-map`
2. `continuity / closeout / sync` 的 runtime refs 必须真实可解析，不能静默漂移

但 archived continuity 这条线上还缺最后一层关键约束：

- archived change 目录里的文件“存在”，不等于它已经形成可信归档锚点；
- `closeout-packet` 与 `sync-packet(source=closeout)` 目前仍可能只依赖 archive 目录中的孤立文件，而不确认：
  - `archive-map` 中是否真的登记了这个归档对象；
  - `archive-map.receipt` 是否真的回指到同一个 `archive-receipt.yaml`；
  - `archive-map.archived_at` 是否与 `archive-receipt.archived_at` 对齐。

本轮要做的，就是把 archived continuity 对象也收进这条归档锚点链。

## 2. 设计目标

本轮目标如下：

1. 让 archived continuity 对象不能脱离 `archive-map + archive-receipt` 单独成立。
2. 对 `closeout-packet` 增加最小归档锚点一致性约束。
3. 对 `sync-packet(source=closeout)` 增加最小归档锚点一致性约束。
4. 不把这轮扩张成“全 archive 文件系统扫描器”。

## 3. 边界

### 3.1 本轮纳入

1. `resolve_closeout_packet(...)` 的 archive-map / archive-receipt 一致性校验
2. `resolve_sync_packet(..., source_kind="closeout")` 的 archive-map / archive-receipt 一致性校验
3. 对应 helper、测试、文档索引与 Baseline 同步

### 3.2 本轮不纳入

1. archive-map 全量文件系统扫描
2. 自动修复 archive-map 或 archive-receipt
3. increment source 的额外归档一致性约束
4. sync history / export bundle 的归档 ref 重写

## 4. 推荐方案

推荐采用：

> `archived continuity objects must resolve through archive-map and archive-receipt`

也就是：

1. 只要是 archived continuity 对象：
   - `closeout-packet`
   - `sync-packet(source=closeout)`
2. 则对应 `change_id` 必须能在 `archive-map` 中找到 entry；
3. 且这个 entry 必须满足：
   - `archive_path` 指向当前 archived change 目录；
   - `receipt` 指向当前 archived change 的 `archive-receipt.yaml`；
   - 如果 `archived_at` 存在，则必须与 receipt 中一致。

如果不满足，直接失败。

## 5. 规则

### 5.1 archived continuity 对象必须能解析到 archive-map entry

当为 archived change 生成：

1. `closeout-packet`
2. `sync-packet(source=closeout)`

时，必须满足：

1. `archive-map.archives[]` 中存在 `change_id == target change_id` 的 entry。

否则拒绝生成。

### 5.2 archive_path 必须与 archived change 目录一致

如果 archive-map entry 声明了 `archive_path`，则它必须等于：

```text
.governance/archive/<change-id>/
```

否则拒绝生成。

### 5.3 receipt 必须与 archive-receipt.yaml 一致

如果 archive-map entry 声明了 `receipt`，则它必须等于：

```text
.governance/archive/<change-id>/archive-receipt.yaml
```

并且该文件必须真实存在。

否则拒绝生成。

### 5.4 archived_at 必须和 archive-receipt 对齐

如果同时满足：

1. archive-map entry 含有 `archived_at`
2. `archive-receipt.yaml` 含有 `archived_at`

则两者必须一致，否则拒绝生成。

## 6. authoritative source 关系

本轮明确：

1. `archive-map` 仍是归档导航索引的权威来源。
2. `archive-receipt` 仍是单个 archived change 的归档执行锚点。
3. `closeout-packet` 和 `sync-packet(source=closeout)` 都不是新的归档权威事实。
4. 它们只能建立在：
   - `archive-map`
   - `archive-receipt`
   彼此一致的前提之上。

## 7. helper 设计

建议在 `continuity.py` 中新增一个内部 helper：

1. `_resolve_archived_change_anchor(paths, change_id) -> dict`
   - 读取 `archive-map`
   - 查找 `change_id` 对应 entry
   - 读取 `archive-receipt.yaml`
   - 校验 `archive_path / receipt / archived_at`
   - 返回对齐后的最小 anchor 信息

它的职责不是“修复”，而是：

- fail fast
- 给 archived continuity 对象提供可信锚点

## 8. 测试建议

至少新增：

1. `test_closeout_packet_rejects_when_archive_map_entry_missing`
2. `test_closeout_packet_rejects_when_archive_map_receipt_mismatches_archived_change`
3. `test_closeout_packet_rejects_when_archive_map_archived_at_mismatches_receipt`
4. `test_sync_packet_from_closeout_rejects_when_archive_anchor_is_inconsistent`
5. 更新现有 closeout/sync 正常路径测试，使其显式带上合法 archive-map entry

## 9. 退出条件

满足以下条件即可视为本轮成立：

1. archived continuity 对象不能脱离 archive-map / archive-receipt 单独成立；
2. closeout 与 sync(closeout) 都已接入最小 archive anchor 校验；
3. 全量测试通过；
4. Baseline 文档同步完成。

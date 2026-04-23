# open-cowork Milestone 2 Archive Map / Maintenance Status Consistency 设计

## 1. 文档目的

本设计文档用于把 `archive-map` 与 `maintenance-status` 的交叉一致性，收口成一层最小可执行约束。

上一轮我们已经补强了：

1. `maintenance-status` 的活动姿态不可回退；
2. `last_archived_change / last_archive_at` 的 sticky 保护。

但现在还缺一层很关键的保证：

> `maintenance-status` 指向的最近归档基线，必须在 `archive-map` 中有对应落点，并且时间锚点不能自相矛盾。

## 2. 设计目标

本轮目标如下：

1. 防止 `maintenance-status.last_archived_change` 指向一个 `archive-map` 中不存在的 change。
2. 防止 `maintenance-status.last_archive_at` 与 `archive-map` 的 `archived_at` 明显不一致。
3. 保持 archive 主链正常通过。
4. 不把本轮扩张成重型全量索引一致性检查器。

## 3. 边界

### 3.1 本轮纳入

1. `set_maintenance_status(...)` 在设置归档基线时读取 `archive-map`
2. 对 `last_archived_change` 做存在性约束
3. 对 `last_archive_at` 做最小一致性约束
4. 对应测试、文档索引和 Baseline 同步

### 3.2 本轮明确不做

1. `archive-map` 全量字段 schema 校验
2. `archive-map` 与真实文件系统的全面比对
3. continuity / retrospective / recovery 的额外修正逻辑
4. 历史多条 archive entry 的复杂排序和冲突解决

### 3.3 但必须兼容

1. `archive_change(...)` 先写 `archive-map`，再写 `maintenance-status` 的现有顺序不变
2. 不涉及最近归档基线的 `maintenance-status` 更新不应受影响
3. 只要 `archive-map` 中存在对应 entry，且 `archived_at` 一致，更新应通过

## 4. 推荐方案

推荐采用：

> `maintenance archived baseline must resolve through archive-map`

也就是：

1. 当 `set_maintenance_status(...)` 写入非空 `last_archived_change` 时，必须能在 `archive-map` 中找到同 `change_id` 的 entry；
2. 如果同时写入 `last_archive_at`，且 `archive-map` entry 自带 `archived_at`，则两者必须一致；
3. 如果只更新普通活动姿态字段，不触碰最近归档基线，则不做额外阻断。

不推荐：

1. 现在就要求 `archive_path / receipt / archived_at` 三者都逐项核对真实文件  
   - 这轮会过重，而且容易把简单约束拖成修复工具。
2. 把这层逻辑散落到 retrospective / recovery / continuity 各自实现里  
   - 会造成多处各自兜底，而不是在写入口一次收住。

## 5. 规则

### 5.1 最近归档 change 必须能解析到 archive-map entry

当写入：

1. `last_archived_change = <non-empty>`

时，`archive-map.archives[]` 中必须存在：

1. `change_id == last_archived_change`

否则拒绝写入。

### 5.2 最近归档时间必须和 archive-map 对齐

当同时满足：

1. 写入了 `last_archived_change`
2. 写入了 `last_archive_at`
3. `archive-map` 对应 entry 也存在 `archived_at`

则：

1. `last_archive_at == archive_entry.archived_at`

否则拒绝写入。

### 5.3 允许的情况

以下情况允许：

1. 未更新最近归档基线字段；
2. `archive-map` entry 存在，但没有 `archived_at`，此时只校验存在性；
3. archive 主链中先写 `archive-map` 再写 `maintenance-status`；
4. 不同归档 change 的新非空基线覆盖旧基线，只要能在 `archive-map` 里解析。

## 6. authoritative source 与生成规则

1. `archive-map` 仍是归档导航索引的权威来源。
2. `maintenance-status` 仍是维护上下文的权威来源。
3. 本轮增加的不是新的 truth-source，而是：
   - 要求 `maintenance-status` 的最近归档锚点，必须能回指到 `archive-map`。

## 7. 最小测试建议

建议至少覆盖：

1. `last_archived_change` 指向不存在的 archive entry 时失败
2. `last_archive_at` 与 archive-map `archived_at` 不一致时失败
3. 匹配的 archive baseline 正常通过
4. 不触碰最近归档基线时普通 maintenance 更新仍通过

## 8. 价值

这份设计的价值在于：

1. 让 retrospective / continuity / hermes recovery 共用同一条最近归档基线；
2. 减少“maintenance 写了一个最近归档 change，但 archive-map 并没有它”的漂移；
3. 让 archive 主链之外的错误写入更早暴露在入口层；
4. 保持本轮范围小、收益直接、容易回归验证。

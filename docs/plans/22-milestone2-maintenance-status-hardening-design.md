# open-cowork Milestone 2 Maintenance Status Hardening 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / Workstream A` 的下一段硬边界工作收口为：

> `maintenance-status` 的活动姿态不可回退 + 最近归档基线不可被空写覆盖

这一轮不重写 `maintenance-status` 的全部语义，也不引入新的索引文件。

它只解决两个当前最影响 continuity / retrospective / recovery 可信度的问题：

1. 同一活动 `change` 的 `maintenance-status` 仍可能被更低活动姿态覆盖；
2. 已经建立的 `last_archived_change / last_archive_at` 基线仍可能被显式空写抹掉。

## 2. 设计目标

本轮目标如下：

1. 为同一活动 `change` 增加最小不可回退保护；
2. 为最近归档基线增加最小 sticky 保护；
3. 保持 archive 之后切回 `idle/none` 的行为不受影响；
4. 保持现有 CLI 主链、retrospective、continuity、hermes recovery 的调用方式不变。

## 3. 边界

### 3.1 本轮纳入

1. `set_maintenance_status(...)` 的同 change 活动态回退阻断
2. `last_archived_change` 不可空写回退
3. `last_archive_at` 不可空写回退
4. 对应测试、文档索引和 Baseline 同步

### 3.2 本轮明确不做

1. `maintenance-status` 的完整状态字典重构
2. `residual_followups` 的语义验证
3. `archive-map` / `maintenance-status` 的交叉一致性强校验
4. 时间戳新旧比较和多归档顺序判断
5. 多 active change 并行模型

### 3.3 但必须兼容

1. `change create` 继续把 `maintenance-status` 从 `idle/none` 切到新活动 change
2. `verify` / `review` / `run` 继续推进同一活动 change
3. `archive` 继续把 active posture 切回 `idle/none`，同时刷新最近归档基线
4. 其他仅读取 `maintenance-status` 的模块不需要改用新接口

## 4. 推荐方案

推荐采用：

> `同 change 单调推进 + 归档基线 sticky`

也就是：

1. 如果 `current_change_id` 没变，则 `status/current_change_active` 不得从更后置状态回写为更前置状态；
2. 如果 `current_change_id` 被清空到 `None`，且 `status=idle`、`current_change_active=none`，则视为 archive 之后的合法收束；
3. 一旦已经存在 `last_archived_change / last_archive_at`，后续显式写 `None` 应被拒绝；
4. 新的非空归档基线允许覆盖旧值。

不推荐：

1. 现在就把 `maintenance-status` 做成完整状态机  
   - 范围太大，会把这一轮从“补硬边界”拉成“重构维护模型”。
2. 现在就把所有字段都做成不可变  
   - 会妨碍后续增量维护，例如 followups 刷新。

## 5. 最小不可回退规则

### 5.1 保护对象

本轮只保护：

1. `status`
2. `current_change_active`
3. `current_change_id`
4. `last_archived_change`
5. `last_archive_at`

### 5.2 活动姿态回退规则

当 `existing.current_change_id == incoming.current_change_id != None` 时：

1. `status` 不得从更高活动姿态回写为更低活动姿态；
2. `current_change_active` 不得从更高活动姿态回写为更低活动姿态；
3. 如果姿态未知，则保守跳过细排序，不误伤正常流程。

### 5.3 合法例外

以下情况允许：

1. 不同 `change_id` 的活动切换；
2. `archive` 之后切回：
   - `current_change_id = None`
   - `status = idle`
   - `current_change_active = none`
3. 从 `idle/none` 激活一个新的 change。

## 6. 最近归档基线 sticky 规则

### 6.1 一旦建立，不允许显式空写

如果当前已有：

1. `last_archived_change`
2. `last_archive_at`

则后续显式更新：

1. `last_archived_change = None`
2. `last_archive_at = None`

都应被拒绝。

### 6.2 允许的更新

以下情况允许：

1. 首次写入归档基线；
2. 用新的非空值覆盖旧归档基线；
3. 不传这两个字段，保留现值。

## 7. 最小状态顺序

本轮沿用已有最小状态顺序，并补上 `idle / draft` 映射：

1. `idle`
2. `draft`
3. `drafting`
4. `step6-executed-pre-step7`
5. `step7-blocked`
6. `step7-verified`
7. `review-revise`
8. `review-rejected`
9. `review-approved`
10. `archived`

说明：

- `draft` 与 `drafting` 语义相近，主要为了兼容 `maintenance-status.current_change_active=draft` 的现有写法。
- 这不是产品级完整状态字典，只是本轮用于不可回退保护的最小排序。

## 8. authoritative source 与生成规则

1. `maintenance-status.yaml` 仍是维护上下文的权威索引视图。
2. 本轮新增保护的目标，不是让它变成更重的事实层，而是防止其关键锚点被低可信或无意回写破坏。
3. `archive-map` 仍承担归档导航职责，本轮不把两者强绑定成更复杂的双向校验。

## 9. 最小测试建议

建议至少覆盖：

1. 同一活动 `change` 的 `status` 回退被拒绝
2. 同一活动 `change` 的 `current_change_active` 回退被拒绝
3. 切换到不同 `change_id` 允许
4. `idle/none` 清空允许
5. `last_archived_change=None` 回退被拒绝
6. `last_archive_at=None` 回退被拒绝
7. 用新的非空归档基线覆盖旧值允许

## 10. 价值

这份设计的价值在于：

1. 稳住 `maintenance-status` 作为 continuity / retrospective / recovery 上游维护锚点的可信度；
2. 让“最近归档基线”不再轻易丢失；
3. 为后续更完整的维护上下文约束提供一层小而稳的基础；
4. 保持本轮范围小、收益直接、与现有主链兼容。

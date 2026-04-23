# open-cowork Milestone 2 Boundary Hardening Round 2 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / Workstream A` 的下一段硬边界工作收口为：

> `治理保留区写边界 + 索引状态不可回退`

这一轮不追求操作系统级真实写入拦截，也不重构整套生命周期状态机。

它只解决两个当前最影响后续稳定性的问题：

1. `Step 6 executor` 仍可能通过 artifacts 声明触碰治理内部保留区或 change truth-source；
2. 同一 `change` 的索引状态仍可能被低阶状态静默回写，导致 current/index 口径回退。

## 2. 设计目标

本轮目标如下：

1. 明确 `executor` 不可触碰的治理保留区。
2. 阻断 `executor` 对 change truth-source / 协议文件的写入声明。
3. 为 `current-change` 与 `changes-index` 增加最小状态回退保护。
4. 保持现有 CLI 主链与 continuity primitives 不需要改用新的调用方式。

## 3. 边界

### 3.1 本轮纳入

1. `.governance/index/**` 写边界阻断
2. `.governance/runtime/**` 写边界阻断
3. `.governance/archive/**` 写边界阻断
4. `.governance/changes/<change-id>/*.yaml` truth-source / protocol 文件写边界阻断
5. `current-change` 与 `changes-index` 的最小状态回退保护
6. 对应测试与文档索引更新

### 3.2 本轮明确不做

1. 操作系统级文件写入拦截
2. Git diff 级真实写入探针
3. 全部治理目录的细粒度 ACL 模型
4. 完整生命周期状态机重写
5. `maintenance-status` 的复杂不可逆约束

### 3.3 但必须兼容

1. `evidence` 继续由治理层写入 `.governance/changes/<change-id>/evidence/**`
2. continuity / sync / closeout 现有对象继续作为派生层工作
3. 已有 `run -> verify -> review -> archive` 主链不改变调用习惯

## 4. 推荐方案

推荐采用：

> `保留区模式匹配阻断 + 索引更新时最小单调性保护`

也就是：

1. `run_change(...)` 在现有 `allowed_write_scope + scope_out` 检查之外，再增加一层治理保留区阻断；
2. `set_current_change(...)` 与 `upsert_change_entry(...)` 在写入同一 `change` 时，拒绝把更高 step/status 写回更低 step/status；
3. 对归档后的 `idle` 清空与不同 change 切换保留例外。

不推荐：

1. 现在就做完整状态图引擎  
   - 范围过大，会把这轮从“补硬边界”拉成“重写生命周期内核”。
2. 现在就禁止 `.governance/changes/**` 下全部文件  
   - 过于粗暴，会让未来非 truth-source 辅助文件没有扩展空间。

## 5. 治理保留区规则

### 5.1 必须阻断的目录

`executor` 声明的 artifacts 不能触碰：

1. `.governance/index/**`
2. `.governance/runtime/**`
3. `.governance/archive/**`

### 5.2 必须阻断的 change truth-source / protocol 文件

`executor` 声明的 artifacts 不能触碰：

```text
.governance/changes/<change-id>/*.yaml
```

这包括但不限于：

1. `manifest.yaml`
2. `contract.yaml`
3. `bindings.yaml`
4. `verify.yaml`
5. `review.yaml`
6. `handoff-package.yaml`
7. `owner-transfer-continuity.yaml`
8. `increment-package.yaml`
9. `sync-packet.yaml`
10. `continuity-launch-input.yaml`
11. `ROUND_ENTRY_INPUT_SUMMARY.yaml`

### 5.3 明确保留的例外

以下内容不属于 `executor` artifacts 的禁止目标：

1. `src/**`
2. `tests/**`
3. 其他 contract 明确允许的非治理代码路径
4. 治理层自己写入的 `.governance/changes/<change-id>/evidence/**`

说明：

- `evidence/**` 由治理层物化，不是 `executor` 直接写 truth-source。
- 如果未来需要允许 `executor` 产出辅助说明文件，应在后续版本里显式增加新的非 truth-source 子目录，而不是复用现有 YAML truth-source。

## 6. 状态回退保护规则

### 6.1 保护对象

本轮只保护：

1. `.governance/index/current-change.yaml`
2. `.governance/index/changes-index.yaml`

### 6.2 最小单调性规则

对于同一 `change_id`：

1. `current_step` 不得从更高值回写为更低值；
2. 当 step 相同时，状态不得从更后置状态回写为更前置状态；
3. 不同 `change_id` 切换时不适用该限制；
4. 归档后的 `idle` 清空不适用该限制。

### 6.3 本轮最小状态顺序

建议按以下顺序比较：

1. `drafting`
2. `step6-executed-pre-step7`
3. `step7-blocked`
4. `step7-verified`
5. `review-revise`
6. `review-rejected`
7. `review-approved`
8. `archived`

说明：

- 这不是完整产品状态字典，只是本轮用于索引保护的最小顺序。
- 若出现未知状态，则回退到“仅按 step 判断，不做同 step 细排序”。

## 7. authoritative source 与生成规则

1. `manifest.yaml` 仍是 change 生命周期的权威事实源。
2. `current-change.yaml` 与 `changes-index.yaml` 是权威事实的活动索引视图。
3. 本轮新增保护的目标，不是创造新的 truth-source，而是防止这些索引和 truth-source 被低可信写入污染。

## 8. 最小测试建议

建议至少覆盖：

1. `run_change` 阻断写入 `.governance/index/current-change.yaml`
2. `run_change` 阻断写入 `.governance/runtime/status/change-status.yaml`
3. `run_change` 阻断写入 `.governance/archive/<change-id>/manifest.yaml`
4. `run_change` 阻断写入 `.governance/changes/<change-id>/manifest.yaml`
5. `set_current_change` 对同一 change 拒绝 step 回退
6. `upsert_change_entry` 对同一 change 拒绝 step 回退
7. 不同 change 切换仍可正常写入
8. `archive` 清空 active change 到 `idle` 不受影响

## 9. 价值

这份设计的价值在于：

1. 让 `executor` 更难污染治理 truth-source；
2. 让 continuity / runtime / sync 对象的上游事实层更可信；
3. 让后续更强的写边界与生命周期硬化建立在更稳定的索引层之上；
4. 继续保持本轮范围小、收益直接、返工风险低。

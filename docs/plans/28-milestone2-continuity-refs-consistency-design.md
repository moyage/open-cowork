# open-cowork Milestone 2 Continuity / Closeout / Sync Refs 一致性设计

## 1. 文档目的

本设计文档用于收口 `Milestone 2` 下一段最小工作包：

> `continuity / closeout / sync refs consistency`

这一段不新增新的 continuity 对象，而是收紧现有对象中的 `refs` 语义，让它们从“字符串级引用”推进到“受控、可解析、不会静默漂移的引用层”。

它重点解决的问题是：

1. `handoff / increment / closeout / sync` 已经都能生成，但它们内部的 `refs` 还不完全区分：
   - 哪些是必需引用；
   - 哪些是可选引用；
   - 哪些必须确认路径真实存在；
   - 哪些还要确认引用对象语义没有漂移。
2. 当前 `closeout-packet` 与 `sync-packet` 可能带出“路径字符串存在，但实际文件不存在或语义已不再对应当前 change”的 ref。
3. 如果现在不收紧，后续做更高层消费、外部导出或历史查询时，会把不稳定 ref 继续扩散出去。

## 2. 设计目标

本轮目标如下：

1. 为 continuity primitives 中的 `refs` 建立统一的最小一致性规则。
2. 把 `refs` 分成：
   - required refs
   - optional refs
   - source-derived refs
3. required refs：
   - 必须存在；
   - 必须能解析到仓库内真实文件；
   - 否则直接失败。
4. optional refs：
   - 只有在目标存在时才输出；
   - 不允许输出指向不存在目标的占位字符串。
5. source-derived refs：
   - 当从上游 packet 继承时，必须再次检查是否可解析；
   - 不允许无条件透传。
6. 对少量“语义敏感 ref”增加额外校验：
   - 例如 `runtime/status/change-status.yaml` 必须确认 `change_id` 与目标 change 一致，才能被 closeout/handoff 等对象镜像引用。

## 3. 边界

### 3.1 本轮纳入

1. `continuity.py` 中现有对象的 refs 语义收紧：
   - `handoff-package`
   - `increment-package`
   - `closeout-packet`
   - `sync-packet`
2. 一组统一的内部 helper，用于：
   - 解析 ref 对应路径；
   - 校验目标存在；
   - 在必要时校验 payload 语义。
3. 最小测试补强。

### 3.2 本轮不纳入

1. 外部 export bundle 的 ref 重写
2. sync history 内事件 payload 追加 refs 校验
3. 全仓库级 ref schema 注册中心
4. runtime timeline 事件粒度进一步收缩或扩展

## 4. 当前问题归纳

### 4.1 closeout-packet 的 runtime refs 可能静默漂移

`closeout-packet` 当前会尝试写入：

- `maintenance_status`
- `runtime_change_status`
- `runtime_timeline`

其中：

1. `maintenance_status` 通常稳定存在，可视为治理锚点的一部分。
2. `runtime_timeline` 属于 runtime 层 append-only 轨迹，只有在对应文件真实存在时才应写入。
3. `runtime_change_status` 是 **active change 快照**，并不天然属于 archived change 的稳定引用。

如果 `runtime_change_status` 已切到别的 change，但 closeout 仍把它写进 `refs`，就会形成“路径存在但语义错了”的引用。

### 4.2 sync-packet 会透传 source packet 中的 refs

`sync-packet` 目前会从 `closeout-packet` 或 `increment-package` 中继承诸如 `runtime_timeline` 之类的 ref。

如果 source packet 中记录的是：

- 已不存在的文件；
- 未来被清理或根本未生成的路径；

当前实现可能继续透传，导致 sync 侧看到的是“源里说有 ref，所以我也写一个”，而不是“我确认过它仍然可解析”。

### 4.3 optional refs 当前语义还不够统一

现有实现里，部分 optional refs 已按“存在才写入”处理，但仍然不够系统：

1. 有的可选 ref 直接根据路径文件是否存在决定；
2. 有的从 source payload 直接拷贝；
3. 还缺少统一的 helper 与统一的失败/省略规则。

## 5. 推荐方案

推荐采用：

> `required fail-fast + optional emit-only-when-resolved + source-derived revalidate`

也就是：

1. **required ref**
   - 必须存在；
   - 必须可解析；
   - 不满足时直接失败。
2. **optional ref**
   - 只在目标实际存在且符合语义时写入；
   - 否则整体省略。
3. **source-derived ref**
   - 即使来自 source packet，也必须再次解析和校验；
   - 不允许直接信任 source packet 的字符串。

这个方案比“把所有 ref 都当作最佳努力提示”更稳，也比“所有 ref 都缺一不可”更实用。

## 6. 一致性规则

### 6.1 required refs

required refs 的规则：

1. 只能指向仓库根目录内的相对路径；
2. 路径必须存在；
3. 若是 payload 级 required ref，生成函数应直接报错；
4. required ref 不能被自动降级为 optional。

本轮至少包括：

1. `sync-packet.refs.<source_kind>_packet`
2. `closeout-packet.refs.archive_receipt`
3. `closeout-packet.refs.archived_manifest`
4. `closeout-packet.refs.archived_verify`
5. `closeout-packet.refs.archived_review`

### 6.2 optional refs

optional refs 的规则：

1. 目标文件不存在时，整个字段省略；
2. 不输出空字符串占位；
3. 不输出仅“逻辑上应该存在”的路径。

本轮至少包括：

1. `handoff.refs.verify`
2. `handoff.refs.review`
3. `increment.refs.owner_transfer`
4. `closeout.refs.handoff_package`
5. `closeout.refs.owner_transfer`
6. `closeout.refs.increment_package`
7. `sync.refs.owner_transfer`
8. `sync.refs.runtime_timeline`

### 6.3 语义敏感 refs

本轮新增一类特殊校验：

> `path exists` 还不够，payload 语义也必须匹配。

首个纳入对象：

1. `runtime/status/change-status.yaml`
   - 只有当 payload 内 `change_id == target change_id` 时，才允许被引用。
   - 否则应整体省略，而不是引用一个“属于别的 active change”的快照。

## 7. 对各对象的具体影响

### 7.1 handoff-package

`handoff-package` 已经在生成前 materialize 对应 change 的 runtime status，因此其 runtime refs 默认是可靠的。

本轮仅要求：

1. 保持 `verify/review` 为 optional refs；
2. 不引入新的平行状态字段；
3. 不需要额外行为变化。

### 7.2 increment-package

`increment-package` 的：

- `handoff_package`
- `runtime_change_status`
- `runtime_timeline`
- `verify`
- `owner_transfer`

应分成：

1. `handoff_package`：required（生成前已确保 materialize）
2. `runtime_change_status`：required（通过 runtime materialization 保证）
3. `runtime_timeline`：optional，只有真实存在才写入
4. `verify`：optional
5. `owner_transfer`：optional

### 7.3 closeout-packet

`closeout-packet` 的 refs 应收紧为：

1. required
   - `archive_receipt`
   - `archived_manifest`
   - `archived_verify`
   - `archived_review`
2. optional
   - `archived_contract`
   - `maintenance_status`
   - `runtime_timeline`
   - `handoff_package`
   - `owner_transfer`
   - `increment_package`
3. semantic optional
   - `runtime_change_status`
     - 只有存在且 `change_id` 与 archived change 一致时才写入。

也就是说：

- `closeout-packet` 不再默认写入 `runtime_change_status`；
- 它只有在 runtime 快照仍然确实属于该 change 时才会出现。

### 7.4 sync-packet

`sync-packet` 的 refs 应收紧为：

1. required
   - `closeout_packet` 或 `increment_package`
2. optional
   - `owner_transfer`
3. source-derived optional
   - `runtime_timeline`
     - 只在 source payload 中声明了 ref，且该 ref 能解析到真实文件时才透传。

因此：

- source payload 中的 ref 不再天然可信；
- `sync-packet` 要重新验证后再写入。

## 8. helper 设计

建议在 `continuity.py` 中新增一组内部 helper：

1. `_ref_path_if_exists(root: Path, ref: str | None) -> str | None`
   - 输入相对 ref 字符串
   - 若能解析到仓库内真实文件，则返回原 ref
   - 否则返回 `None`

2. `_append_existing_ref(refs: dict, key: str, path: Path, root: Path) -> None`
   - 用于本地 path 构建的 optional ref

3. `_append_resolved_payload_ref(refs: dict, key: str, ref: str | None, root: Path) -> None`
   - 用于从 source payload 继承的 optional ref

4. `_runtime_change_status_ref_if_matching(paths: GovernancePaths, change_id: str) -> str | None`
   - 只有当前 runtime change-status 文件存在且其中 `change_id` 匹配时，才返回 ref

## 9. 测试建议

本轮至少新增以下测试：

1. `test_closeout_packet_omits_runtime_change_status_when_active_snapshot_belongs_to_other_change`
2. `test_closeout_packet_omits_runtime_timeline_ref_when_file_missing`
3. `test_sync_packet_omits_runtime_timeline_when_source_ref_target_missing`
4. `test_sync_packet_keeps_runtime_timeline_when_source_ref_resolves`
5. `test_increment_package_omits_runtime_timeline_when_file_missing`

## 10. 退出条件

满足以下条件即可视为本轮成立：

1. continuity / closeout / sync 的 refs 规则被统一到 required / optional / source-derived 三类语义中；
2. `closeout-packet` 不再静默引用别的 active change 的 runtime snapshot；
3. `sync-packet` 不再无条件透传 source packet 内失效 ref；
4. 全量测试通过；
5. 对外 Baseline 文档同步完成。

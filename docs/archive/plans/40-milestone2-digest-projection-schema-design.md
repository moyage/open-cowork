# open-cowork Milestone 2 Digest Projection Schema 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 下一段最小工作包正式收口为：

> 为 `continuity digest` 增补显式 projection schema。

上一轮我们已经有：

1. `continuity digest` 的 active / archived 默认入口
2. 最近同步摘要 `recent_sync_summary`

但当前还存在一个结构性缺口：

- `digest` 虽然已经是只读派生层；
- 但它还没有显式告诉消费者：`summary.status / phase / step / headline` 这些字段分别投影自哪里。

本轮要做的，是把这层“投影来源”写出来，而不是让消费者靠阅读实现猜测。

## 2. 设计目标

1. `digest` 输出显式的 `projection_sources`
2. 为关键镜像字段声明：
   - `source_ref`
   - `source_field`
3. 不改动现有 truth-source schema
4. 不新增新的事实文件

## 3. 边界

### 3.1 本轮纳入

1. `resolve_continuity_digest(...)` 增补 `projection_sources`
2. active / archived 两种分支都提供最小映射
3. 最小测试覆盖

### 3.2 本轮不纳入

1. 全字段映射
2. 自动 schema 校验器
3. 跨 packet 的复杂 lineage graph

## 4. 推荐方案

推荐采用：

> `digest carries explicit projection metadata`

也就是：

1. `digest.summary` 保持当前简洁结构
2. 额外增加 `projection_sources.summary`
3. 只对最关键字段做投影说明：
   - `title`
   - `status`
   - `phase`
   - `step`
   - `headline`
   - `next_attention`

## 5. 建议结构

```yaml
projection_sources:
  summary:
    title:
      source_ref: .governance/changes/CHG-.../manifest.yaml
      source_field: title
    status:
      source_ref: .governance/runtime/status/change-status.yaml
      source_field: current_status
    phase:
      source_ref: .governance/runtime/status/change-status.yaml
      source_field: phase
    step:
      source_ref: .governance/runtime/status/change-status.yaml
      source_field: current_step
    headline:
      source_ref: .governance/changes/CHG-.../manifest.yaml
      source_field: title
    next_attention:
      source_ref: .governance/runtime/status/change-status.yaml
      source_field: gate_posture.waiting_on|gate_posture.next_decision
```

archived 场景中则优先指向：
- `closeout-packet`
- archived `manifest.yaml`

## 6. 生成规则

### 6.1 active

- `status / phase / step / next_attention` 来自 `runtime/status/change-status.yaml`
- `title / headline` 默认来自 active `manifest.yaml`

### 6.2 archived

- `status / phase / step / headline / next_attention` 优先来自 `closeout-packet.yaml`
- `title` 可来自 archived `manifest.yaml`

## 7. 测试建议

至少新增：

1. `test_resolve_continuity_digest_active_includes_projection_sources`
2. `test_resolve_continuity_digest_archived_includes_projection_sources`

## 8. 退出条件

1. active / archived digest 都有最小 `projection_sources`
2. 关键字段有明确 authoritative source 映射
3. 全量测试通过

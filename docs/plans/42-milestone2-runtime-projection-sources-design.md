# open-cowork Milestone 2 Runtime Projection Sources 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 下一段最小工作包正式收口为：

> 为 `runtime/status` 与 `runtime/timeline` 增补显式 projection sources。

上一轮我们已经为 `continuity digest` 增加了 `projection_sources`，这让摘要层开始能明确说明自己是从哪里镜像出来的。

但目前更底层的派生层本身仍有一个结构性缺口：

- `runtime/status` 和 `runtime/timeline` 虽然已经稳定可读；
- 但它们自己还没有显式告诉消费者：哪些字段来自哪些 authoritative file / source field；
- 后续如果继续做更丰富的 digest / summary / dashboard，就仍然要反复去读实现猜口径。

本轮要做的，是把这层投影来源元数据下沉到 runtime 层本身。

## 2. 设计目标

1. 为 `runtime-change-status` 增补 `projection_sources`
2. 为 `runtime-steps-status` 增补 `projection_sources`
3. 为 `runtime-participants-status` 增补 `projection_sources`
4. 为 `runtime-event` 增补最小 `projection_sources`
5. 不改动 authoritative truth-source schema
6. 不新增新的事实文件

## 3. 边界

### 3.1 本轮纳入

1. `runtime/status/*.yaml` 的 projection source 元数据
2. `runtime/timeline/events-YYYYMM.yaml` 中单个事件的 projection source 元数据
3. 最小测试覆盖

### 3.2 本轮不纳入

1. 全字段 lineage graph
2. 自动 schema validator
3. digest / closeout / sync 的再次重构
4. 运行时写入行为变化

## 4. 推荐方案

推荐采用：

> `runtime payload carries explicit projection metadata`

也就是：

1. 保持现有 payload 结构不动
2. 每个 payload 额外挂一个最小 `projection_sources`
3. 只标最关键镜像字段，不追求全覆盖

这样可以做到：

- 不打断现有消费者
- 但新消费者可以直接拿这层元数据解释语义

## 5. 结构建议

### 5.1 change-status

```yaml
projection_sources:
  phase:
    source_ref: .governance/index/current-change.yaml
    source_field: current_change.current_step
    derivation: phase_label_for_step
  current_status:
    source_ref: .governance/changes/CHG-.../manifest.yaml
    source_field: status
  current_step:
    source_ref: .governance/changes/CHG-.../manifest.yaml
    source_field: current_step
  gate_posture.waiting_on:
    source_ref: .governance/changes/CHG-.../manifest.yaml
    source_field: current_step|status
    derivation: render_status_snapshot.waiting_on
```

### 5.2 steps-status

```yaml
projection_sources:
  current_step:
    source_ref: .governance/changes/CHG-.../manifest.yaml
    source_field: current_step
  next_step:
    source_ref: .governance/changes/CHG-.../manifest.yaml
    source_field: current_step
    derivation: next_step
  steps[].owner:
    source_ref: .governance/changes/CHG-.../bindings.yaml
    source_field: steps.<n>.owner|manifest.roles
```

### 5.3 participants-status

```yaml
projection_sources:
  participants[].actor_id:
    source_ref: .governance/changes/CHG-.../bindings.yaml
    source_field: steps.<n>.owner|manifest.roles
  participants[].status:
    source_ref: .governance/runtime/status/steps-status.yaml
    source_field: steps[].status
    derivation: participant_status
```

### 5.4 timeline event

```yaml
projection_sources:
  to_status:
    source_ref: .governance/changes/CHG-.../verify.yaml
    source_field: summary.status
    derivation: event_status_mapping
  timestamp:
    source_ref: .governance/changes/CHG-.../verify.yaml
    source_field: file_mtime
```

## 6. 生成原则

1. projection 元数据只能说明来源，不能形成新的 truth-source。
2. 若字段是通过 helper 派生，应显式写 `derivation`。
3. 若字段同时有两个候选来源，可用 `a|b` 形式写明优先级。
4. 本轮只做最关键字段，不追求全量覆盖。

## 7. 测试建议

至少新增：

1. `test_runtime_status_change_payload_includes_projection_sources`
2. `test_runtime_status_steps_payload_includes_projection_sources`
3. `test_runtime_status_participants_payload_includes_projection_sources`
4. `test_timeline_event_includes_projection_sources`

## 8. 退出条件

1. runtime 三份 status payload 都有最小 projection sources
2. timeline event 有最小 projection sources
3. 全量测试通过

# open-cowork Milestone 2 Runtime Projection Sources 实施计划

## 1. 文档目的

本实施计划用于指导 `runtime/status` 与 `runtime/timeline` 的 projection sources 最小实现。

## 2. 本轮目标

完成后应具备：

1. `runtime-change-status` 含最小 `projection_sources`
2. `runtime-steps-status` 含最小 `projection_sources`
3. `runtime-participants-status` 含最小 `projection_sources`
4. `runtime-event` 含最小 `projection_sources`

## 3. 范围

### 3.1 纳入

1. `src/governance/runtime_status.py`
2. `tests/test_runtime_status.py`
3. `docs/README.md`

### 3.2 不纳入

1. digest / closeout / sync 重写
2. 全量 lineage
3. schema validator

## 4. 设计约束

1. 不能改变现有 payload 的核心字段与语义。
2. projection source 只能解释来源，不能替代 refs。
3. timeline 只补最小事件级来源，不做复杂历史回溯。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_runtime_status_change_payload_includes_projection_sources`
2. `test_runtime_status_steps_payload_includes_projection_sources`
3. `test_runtime_status_participants_payload_includes_projection_sources`
4. `test_timeline_event_includes_projection_sources`

### Step 2. 实现 helper

建议新增：

1. `_change_status_projection_sources(...)`
2. `_steps_status_projection_sources(...)`
3. `_participants_status_projection_sources(...)`
4. `_timeline_event_projection_sources(...)`

### Step 3. 接入 payload

1. change-status 写入 `projection_sources`
2. steps-status 写入 `projection_sources`
3. participants-status 写入 `projection_sources`
4. event 写入 `projection_sources`

### Step 4. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. runtime status / timeline 都带最小 projection 元数据
2. 测试通过
3. 现有消费者不受影响

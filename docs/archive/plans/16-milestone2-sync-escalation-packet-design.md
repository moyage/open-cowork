# open-cowork Milestone 2 Sync / Escalation Packet 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / continuity primitives` 的下一段最小能力包正式收口为：

> `sync-packet`

它回答的问题不是“再复制一份 closeout 文档给上层看”，而是：

- 当项目级 change 需要向更高层消费面同步当前状态或进行升级时，如何提供一个统一、低摩擦、可被人和 agent 消费的协议包；
- 如何让 `closeout-packet` 与 `increment-package` 都能作为上游输入，而不形成两套平行同步协议；
- 如何把“常规同步”和“需要更高层介入的升级”统一进一个最小对象。

## 2. 设计目标

本轮目标如下：

1. 为项目级 change 定义一份最小但正式的 `sync-packet` 结构。
2. 让这份 packet 至少回答清楚：
   - 这次同步来自哪一个 change；
   - 同步锚点是 closeout 还是 increment；
   - 本次要向上层传递哪些结果、阻塞、待决策点；
   - 这只是 routine sync，还是已经进入 escalation；
   - 上层应关注什么、需要给出什么反馈。
3. 让 `sync-packet` 复用：
   - `closeout-packet`
   - `increment-package`
   - `runtime timeline`
   - 可选的 `owner-transfer-continuity`
4. 保持 `sync-packet` 仍是协议层的“对上消费包”，而不是新的 truth-source。

## 3. 边界

### 3.1 本轮纳入

1. `sync-packet` schema
2. routine sync 与 escalation 的统一结构
3. 最小 CLI 入口设计
4. 与 closeout / increment / runtime timeline 的衔接规则
5. 最小测试建议

### 3.2 本轮明确不做

1. 生态级项目组合管理
2. 自动发送消息、邮件或通知
3. 上层审批流或工单系统集成
4. 多目标同步分发
5. 历史 sync packet 聚合面板

### 3.3 但必须兼容

1. 更高层 sponsor / steering / ecosystem 消费
2. 外部只读系统直接消费
3. 后续 sync history 列表
4. 项目级 closeout 到生态级汇总的桥接

## 4. 为什么 closeout-packet 之后先做 sync-packet

当前 continuity primitives 已经覆盖：

1. 启动与接续：`launch-input / round-entry-summary`
2. 交接与转移：`handoff-package / owner-transfer-continuity`
3. 阶段增量：`increment-package`
4. 正式收束：`closeout-packet`

接下来最自然的缺口就是：

- 如何把这些项目内的 continuity 结果，以统一协议向更高层同步；
- 如何在不引入上层治理系统的前提下，先把“上层消费接口”做成最小能力。

一句话说：

> `sync-packet` 是项目级 continuity primitives 向更高层消费面的第一层协议出口。

## 5. 推荐方案

推荐采用：

> `single sync packet + source anchor + sync kind`

也就是：

1. 只定义一个统一对象：`sync-packet`；
2. 用 `source_anchor` 区分它是来自：
   - `closeout-packet`
   - `increment-package`
3. 用 `sync_kind` 区分它是：
   - `routine-sync`
   - `escalation`

不推荐：

1. 为 `sync` 和 `escalation` 分别定义两套 packet  
   - 会造成消费方要处理两套近似对象。
2. 让上层消费方直接读取 `closeout-packet` / `increment-package`  
   - 会把项目级内部对象直接暴露给更高层，缺少面向上层的统一摘要层。

## 6. 建议结构

建议新增文件：

```text
.governance/changes/<change-id>/sync-packet.yaml
```

如果本次同步锚点来自 `closeout-packet`，也允许输出到：

```text
.governance/archive/<change-id>/sync-packet.yaml
```

本轮推荐规则：

1. `source_anchor = increment` 时，输出到 change 目录。
2. `source_anchor = closeout` 时，输出到 archive 目录。

它属于：

- continuity primitives 向更高层消费面的桥接层
- 项目级对上同步的统一入口

它不替代：

- `closeout-packet.yaml`
- `increment-package.yaml`
- `runtime/status/*.yaml`
- `runtime/timeline/events-YYYYMM.yaml`

## 7. authoritative source 与生成规则

### 7.1 核心来源

1. `closeout-packet.yaml` 或 `increment-package.yaml`（至少其一）
2. `runtime/timeline/events-YYYYMM.yaml`
3. `runtime/status/change-status.yaml`
4. `owner-transfer-continuity.yaml`（存在时）

### 7.2 关键判断

`sync-packet` 不能是纯派生对象。

原因是：

1. `target_layer`
2. `target_scope`
3. `sync_kind`
4. `attention_request`
5. `decision_request`

这些都不是现有项目内事实层天然存在的字段，而是“面向更高层消费”的新记录语义。

因此本轮明确：

1. `sync-packet` 是“派生 + 显式输入”的混合对象；
2. 当前状态与结果锚点必须来自 `closeout` 或 `increment`；
3. 上层消费语义由 CLI 输入并持久化。

### 7.3 生成原则

1. `sync-packet` 只表达“对上同步所需”的最小信息。
2. 不复制完整 closeout 或 increment 内容。
3. 所有项目内结论都必须能回指到 source anchor refs。
4. 如果 `sync_kind = escalation`，必须显式写出 attention / decision 请求。
5. `sync-packet` 不得替代项目级 authoritative facts。

## 8. 最小 schema

建议最小字段如下：

```yaml
schema: sync-packet/v1
change_id: CHG-20260424-001
generated_at: 2026-04-24T12:00:00Z
sync_kind: escalation

source_anchor:
  source_kind: closeout
  source_ref: .governance/archive/CHG-20260424-001/closeout-packet.yaml
  source_status: archived
  source_summary: "本轮已完成 continuity primitives 的最小闭环"

target_context:
  target_layer: sponsor
  target_scope: project-level
  urgency: attention

sync_summary:
  headline: "项目级 continuity primitives 已闭环，建议进入更高层同步阶段"
  delivered_scope:
    - "closeout-packet"
    - "handoff / owner-transfer / increment"
  pending_scope:
    - "ecosystem-level sync"
  requested_attention:
    - "确认上层同步边界"
  requested_decisions:
    - "是否以 sync-packet 作为默认上层输入"

continuity_bridge:
  next_owner_suggestion: "sponsor-or-ecosystem-operator"
  next_action_suggestion: "review sync packet and decide next-level integration"
  return_path_ref: .governance/archive/CHG-20260424-001/closeout-packet.yaml

refs:
  closeout_packet: .governance/archive/CHG-20260424-001/closeout-packet.yaml
  increment_package: .governance/changes/CHG-20260424-001/increment-package.yaml
  runtime_timeline: .governance/runtime/timeline/events-202604.yaml
  owner_transfer: .governance/changes/CHG-20260424-001/owner-transfer-continuity.yaml
```

说明：

1. `source_anchor` 是受控镜像字段，只用于标明本次同步的状态锚点。
2. `sync_summary` 是面向更高层消费的摘要层，不是新的项目内事实层。
3. `requested_attention / requested_decisions` 在 `routine-sync` 时可以为空，在 `escalation` 时必须至少有一项。

## 9. 最小生命周期

本轮建议最小生命周期只有一步：

1. `materialize`
   - 识别 source anchor
   - 读取 anchor payload
   - 写入 target context / sync summary / continuity bridge
   - 输出 `sync-packet.yaml`

本轮明确不做：

1. `acknowledge`
2. `resolve`
3. `history list`
4. `multi-target dispatch`

## 10. 最小 CLI 设计

建议新增：

```bash
ocw continuity sync-packet \
  --change-id CHG-20260424-001 \
  --source-kind closeout \
  --sync-kind escalation \
  --target-layer sponsor \
  --target-scope project-level \
  --urgency attention \
  --headline "项目级 continuity primitives 已闭环，建议进入更高层同步阶段" \
  --delivered-scope "closeout-packet" \
  --delivered-scope "handoff / owner-transfer / increment" \
  --pending-scope "ecosystem-level sync" \
  --requested-attention "确认上层同步边界" \
  --requested-decision "是否以 sync-packet 作为默认上层输入" \
  --next-owner-suggestion "sponsor-or-ecosystem-operator" \
  --next-action-suggestion "review sync packet and decide next-level integration"
```

### 10.1 命令职责

1. 根据 `source-kind` 读取 `closeout-packet` 或 `increment-package`。
2. 组装统一 `sync-packet`。
3. 在正确目录中落盘。
4. 输出供人和上层 agent 消费的最小桥接包。

### 10.2 失败规则

以下情况必须失败：

1. `source-kind = closeout` 但 `closeout-packet` 不存在
2. `source-kind = increment` 但 `increment-package` 不存在
3. `sync-kind = escalation` 且没有任何 `requested_attention` 与 `requested_decisions`
4. `target_layer / target_scope` 缺失

以下情况不得失败，只应降级：

1. `owner-transfer-continuity` 不存在  
   - 仅省略对应 ref。
2. `runtime/status` 当前已不再对应该 archived change  
   - 只保留 runtime timeline ref。

## 11. 最小测试建议

建议至少覆盖：

1. 从 `closeout-packet` 成功生成 `sync-packet`
2. 从 `increment-package` 成功生成 `sync-packet`
3. `escalation` 缺少 requested attention / decision 时失败
4. 可选 ref 缺失时仍可生成
5. 输出路径随 `source-kind` 正确切换

## 12. 与后续方向的关系

这份设计的价值在于：

1. 把项目级 continuity 成果收敛成统一的对上同步对象；
2. 让“常规同步”和“升级请求”共用一套结构；
3. 为后续更高层消费、外部只读系统、甚至新项目中的生态治理提供稳定输入面；
4. 保持 `open-cowork` 仍停留在项目级协议与协作层，而不上卷成生态级治理系统本身。

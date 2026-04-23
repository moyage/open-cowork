# open-cowork Milestone 2 Closeout / Close-Loop Packet 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / continuity primitives` 的下一段最小能力包正式收口为：

> `closeout-packet`

它回答的问题不是“再补一轮更大的复盘文档包”，而是：

- 当一个 change 已完成 `Step 9 archive` 后，如何输出一个正式、低摩擦、低歧义、默认可阅读的收束入口；
- 如何把 `archive artifacts`、`runtime/status`、`timeline`、`handoff / owner-transfer / increment` 串成一个统一 closure 入口；
- 如何让后续 `sync / escalation packet` 直接复用这份 closeout 结果，而不是重新扫全部原始事实层。

## 2. 设计目标

本轮目标如下：

1. 为已 archive 的 change 定义一份最小但正式的 `closeout-packet` 结构。
2. 让人和 agent 都能用最少阅读面理解：
   - 本轮最终结果是什么；
   - 本轮哪些能力或变更已经正式交付；
   - 哪些事项被明确延后；
   - 下一轮默认建议方向是什么；
   - 关键事实应回看哪些 authoritative refs。
3. 让 `closeout-packet` 成为：
   - `sync / escalation packet` 的直接上游输入；
   - 人类默认 close-loop 阅读入口；
   - 当前轮与下一轮之间的正式桥接对象。
4. 保持 `closeout-packet` 只是 closure 摘要层，而不是新的 truth-source。

## 3. 边界

### 3.1 本轮纳入

1. `closeout-packet` schema
2. 最小 authoritative source 规则
3. 最小 CLI 入口设计
4. 与 `archive / runtime status / timeline / continuity primitives` 的衔接规则
5. 最小测试建议

### 3.2 本轮明确不做

1. 回到旧版 5 份 closeout 文档包的完整重建
2. 自动生成外部 sponsor 报告或周报
3. 项目组合级总结或生态级汇总
4. 自动同步到上层系统
5. 复杂 closeout 审批流

### 3.3 但必须兼容

本轮 `closeout-packet` 必须为后续能力保留兼容空间：

1. `sync / escalation packet`
2. external / local closeout directory 的默认入口
3. retrospective / reference suggestion 的轻量镜像
4. 多段 increment history 的汇总引用

## 4. 为什么先做 closeout-packet

当前 continuity primitives 已经形成：

1. `continuity launch-input`
2. `round-entry-summary`
3. `handoff-package`
4. `owner-transfer-continuity`
5. `increment-package`

它们已经覆盖了“启动、接手、转移、增量”这几类过程型原语，但还缺少：

- 一个面向“本轮已正式结束”的默认入口；
- 一个能把 closure 结果稳定传递给下一层消费面的正式包；
- 一个把 runtime/timeline 与 archived artifacts 组织成统一 close-loop 阅读面的方法。

一句话说：

> `closeout-packet` 是 continuity primitives 与下一步 `sync / escalation packet` 之间的必要桥梁。

## 5. 推荐方案

推荐采用：

> `single closeout packet + layered refs`

也就是：

1. 只输出一份单一 `closeout-packet.yaml`；
2. 它自己只承载最小必需的 closure 摘要；
3. 其余内容通过 refs 指向已有 authoritative / machine-readable artifacts；
4. 不重新回到“多份 closeout 文档共同承载语义”的模式。

不推荐：

1. 直接沿用旧的 5 份 closeout package 作为主内置能力  
   - 这会让人类阅读层再次膨胀。
2. 让 `closeout-packet` 只剩 archive receipt + timeline index  
   - 这会让默认阅读入口过瘦，不符合我们前面确定的人类体验方向。

## 6. 建议结构

建议新增文件：

```text
.governance/archive/<change-id>/closeout-packet.yaml
```

它属于：

- archive 目录内的 closure 摘要层
- 面向人和 agent 的统一收束入口

它不替代：

- `archive-receipt.yaml`
- `manifest.yaml / contract.yaml / verify.yaml / review.yaml`
- `runtime/status/*.yaml`
- `runtime/timeline/events-YYYYMM.yaml`
- `handoff-package.yaml`
- `owner-transfer-continuity.yaml`
- `increment-package.yaml`

## 7. authoritative source 与生成规则

### 7.1 核心来源

1. `.governance/archive/<change-id>/archive-receipt.yaml`
2. `.governance/archive/<change-id>/manifest.yaml`
3. `.governance/archive/<change-id>/contract.yaml`
4. `.governance/archive/<change-id>/verify.yaml`
5. `.governance/archive/<change-id>/review.yaml`
6. `.governance/index/maintenance-status.yaml`
7. `.governance/runtime/status/change-status.yaml`
8. `.governance/runtime/timeline/events-YYYYMM.yaml`

### 7.2 可选增强来源

以下来源不属于 `closeout-packet` 的最小成立条件，但在存在时应被复用：

1. `.governance/changes/<change-id>/handoff-package.yaml`
2. `.governance/changes/<change-id>/owner-transfer-continuity.yaml`
3. `.governance/changes/<change-id>/increment-package.yaml`
4. 外层 closeout directory 中的人类阅读文档（如存在）

### 7.3 生成原则

1. `closeout-packet` 必须是 closure 摘要层。
2. 所有 closure 结论必须能回指到明确 refs。
3. 如果同类状态信息已存在于 archived artifacts 或 runtime/status，不得再造平行语义。
4. `closeout-packet` 可以提供“默认阅读入口”，但不得替代 authoritative facts。
5. `closeout-packet` 只在 archive 完成后生成，不能用于未归档 change 的 progress 汇报。

### 7.4 最小成立条件

1. 目标 change 必须已经 archive。
2. `archive-receipt.yaml` 必须存在，且 `archive_executed = true`。
3. `manifest.yaml / review.yaml / verify.yaml` 缺一不可，除非旧归档形态没有该文件且能明确识别为兼容缺失。
4. `closeout-packet` 不依赖 `handoff / owner-transfer / increment` 存在；它们属于可选增强 refs。
5. 只有在无法识别该 archived change 的基础 closure 状态时才应失败。

## 8. 最小 schema

建议最小字段如下：

```yaml
schema: closeout-packet/v1
change_id: CHG-20260424-001
generated_at: 2026-04-24T12:00:00Z
closeout_kind: archived-change

closure_summary:
  title: "本轮 change 标题"
  final_status: "archived"
  final_phase: "Phase 4 / 审查与收束"
  final_step: 9
  final_decision: "approve-and-close"
  closeout_statement: "本轮已完成最小闭环并正式归档"

result_summary:
  delivered_scope:
    - "runtime status / timeline protocol"
    - "handoff package"
    - "owner transfer continuity"
    - "increment package"
  deferred_scope:
    - "sync / escalation packet"
  key_outcomes:
    - "主链闭环成立"
    - "continuity primitives 形成最小链"
  unresolved_items:
    - "上层 sync 协议尚未建立"

continuity_bridge:
  next_round_default_direction: "build sync / escalation packet"
  next_round_attention_points:
    - "不要把 closeout-packet 扩成新的 truth-source"
    - "优先复用 increment / handoff / timeline"
  carry_forward_items:
    - "closeout packet external reading entry"
    - "project-to-higher-layer sync"

human_reading_entry:
  operator_summary: "给操作者默认看的简明收束摘要"
  sponsor_summary: "给 sponsor 的简版收束说明"
  next_operator_start_pack:
    - ".governance/archive/CHG-20260424-001/closeout-packet.yaml"
    - ".governance/archive/CHG-20260424-001/archive-receipt.yaml"
    - ".governance/archive/CHG-20260424-001/review.yaml"

refs:
  archive_receipt: .governance/archive/CHG-20260424-001/archive-receipt.yaml
  archived_manifest: .governance/archive/CHG-20260424-001/manifest.yaml
  archived_contract: .governance/archive/CHG-20260424-001/contract.yaml
  archived_verify: .governance/archive/CHG-20260424-001/verify.yaml
  archived_review: .governance/archive/CHG-20260424-001/review.yaml
  maintenance_status: .governance/index/maintenance-status.yaml
  runtime_change_status: .governance/runtime/status/change-status.yaml
  runtime_timeline: .governance/runtime/timeline/events-202604.yaml
  handoff_package: .governance/changes/CHG-20260424-001/handoff-package.yaml
  owner_transfer: .governance/changes/CHG-20260424-001/owner-transfer-continuity.yaml
  increment_package: .governance/changes/CHG-20260424-001/increment-package.yaml
```

说明：

1. `closure_summary` 是受控镜像字段，只用于提供默认 close-loop 摘要。
2. 其唯一权威来源应来自：
   - `archive-receipt.yaml`
   - archived `manifest / verify / review`
3. `result_summary` 是 closure 摘要层新增的记录字段，允许由 CLI 输入辅助生成。
4. `continuity_bridge` 不是下一轮已定执行方案，而是下一轮默认建议入口。
5. `handoff / owner_transfer / increment` 为可选 refs，仅在存在时写入。

## 9. 最小生命周期

本轮建议最小生命周期只有一步：

1. `materialize`
   - 验证目标 change 已 archive
   - 读取 archive receipt 与 archived artifacts
   - 生成 `closeout-packet.yaml`
   - 如果存在 handoff / owner transfer / increment，则追加对应 refs

本轮明确不做：

1. `update`
2. `publish`
3. `multi-closeout bundle`
4. `external directory auto-export`

## 10. 最小 CLI 设计

建议新增：

```bash
ocw continuity closeout-packet \
  --change-id CHG-20260424-001 \
  --closeout-statement "本轮已完成最小闭环并正式归档" \
  --delivered-scope "runtime status / timeline protocol" \
  --delivered-scope "handoff package" \
  --delivered-scope "owner transfer continuity" \
  --delivered-scope "increment package" \
  --deferred-scope "sync / escalation packet" \
  --key-outcome "主链闭环成立" \
  --key-outcome "continuity primitives 形成最小链" \
  --unresolved-item "上层 sync 协议尚未建立" \
  --next-direction "build sync / escalation packet" \
  --attention-point "不要把 closeout-packet 扩成新的 truth-source" \
  --attention-point "优先复用 increment / handoff / timeline" \
  --carry-forward-item "project-to-higher-layer sync" \
  --operator-summary "本轮已完成 continuity primitives 的最小闭环" \
  --sponsor-summary "本轮完成 continuity 主线基线，下一步进入 sync 协议"
```

### 10.1 命令职责

1. 校验目标 change 已 archive。
2. 读取 archive artifacts。
3. 写入最小 closure 摘要字段。
4. 写入 refs。
5. 输出 `.governance/archive/<change-id>/closeout-packet.yaml`。

### 10.2 失败规则

以下情况必须失败：

1. 未提供 `change_id` 且当前上下文无法识别目标 archived change
2. archive receipt 不存在
3. archive receipt 未标记为 `archive_executed = true`
4. archived `manifest` 缺失
5. archived `review` 或 `verify` 缺失到无法判断 final decision

以下情况不得失败，只应降级：

1. `runtime/status` 当前已不再对应该 archived change  
   - 只保留 runtime refs 或在可识别时补充 snapshot refs。
2. `handoff / owner-transfer / increment` 不存在  
   - 仅省略对应 refs。

## 11. 最小测试建议

建议至少覆盖：

1. 已 archive change 可成功生成 `closeout-packet.yaml`
2. 未 archive change 会被拒绝
3. `archive_receipt` 缺失时失败
4. 无 `handoff / owner-transfer / increment` 仍可生成
5. 若这些 continuity 文件存在，则 refs 被正确写入
6. `closeout-packet` 不写入新的 truth-source 类字段

## 12. 与旧版 closeout spec 的关系

仓库中已有：

- `docs/specs/13-round-close-report-and-closeout-package-spec.md`

它代表的是更早阶段的“外层 closeout 文档包规范”。

本轮明确：

1. `closeout-packet` 不直接取代该规范；
2. 但它将成为未来精简外层 closeout 包的内置核心索引；
3. 如需外层 1~N 份 closeout 文档，应以 `closeout-packet` 为统一事实入口，而不是再各自重新组织 closure 语义。

## 13. 价值

这份设计的价值在于：

1. 给已 archive 的 round 一个正式、默认、低摩擦的收束入口；
2. 把人类默认 close-loop 阅读面从旧式大包收敛为单一 packet；
3. 让 `sync / escalation packet` 有清晰上游输入；
4. 继续坚持“事实层稳定、阅读层压缩、协议层可复用”的方向。

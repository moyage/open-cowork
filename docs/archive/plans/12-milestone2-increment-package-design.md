# open-cowork Milestone 2 Increment Package 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / continuity primitives` 的下一段最小能力包正式收口为：

> `increment package`

它回答的问题不是“再输出一份阶段总结”，而是：

- 当前这一段推进相对于上一段到底新增了什么；
- 哪些原有假设已经失效；
- 哪些风险、阻塞、待决策点被带到了下一段；
- 如何让 handoff、owner transfer、下一轮接续都能复用这一段的增量结果，而不是每次重新从全部事实层重扫。

## 2. 设计目标

本轮目标如下：

1. 为 active change 定义一份最小但正式的 `increment package` 结构。
2. 让这一段增量至少回答清楚：
   - 本段新增结论
   - 本段失效假设
   - 本段新增风险 / 阻塞
   - 本段留下的下一判断点
3. 让 `increment package` 复用：
   - `handoff-package.yaml`
   - `owner-transfer-continuity.yaml`（存在时）
   - `runtime/status`
   - `runtime/timeline`
4. 保持 increment package 仍是 continuity 层的“增量摘要对象”，而不是新的权威事实层。

## 3. 边界

### 3.1 本轮纳入

1. `increment package` schema
2. 最小生成规则
3. 最小 CLI 设计
4. 与 handoff / owner transfer / round-entry 的组合关系
5. 最小测试建议

### 3.2 本轮明确不做

1. 自动 diff 全量文档语义
2. 自动从自然语言总结中提取高质量结论
3. 复杂多段 increment 历史聚合
4. 项目级周报或组合级增量汇总
5. 自动同步到外部系统

### 3.3 但必须兼容

1. 多段 increment history
2. closeout / retrospective 引用
3. escalation / sync packet
4. round-entry 输入压缩

## 4. 为什么它不等于 handoff 或 owner transfer

`handoff package` 解决的是：

- 当前 change 在哪里
- 谁适合接手
- 下一步最小阅读面

`owner transfer continuity` 解决的是：

- 所有权为什么变化
- 由谁发起
- 由谁接受
- 是否正式生效

`increment package` 解决的是：

- 这一段推进新增了哪些结论
- 哪些旧判断不再成立
- 哪些风险和阻塞需要被继续带走

一句话说：

> `handoff package` 是接手入口；`owner transfer continuity` 是转移记录；`increment package` 是阶段增量摘要。

## 5. 推荐方案

推荐采用：

> `single increment packet + layered refs`

也就是：

1. increment package 自己只承载这一段“新增/失效/残留”的结构化摘要；
2. 当前状态、接手入口、owner 变化都通过 refs 指向已有 handoff / owner transfer / runtime status；
3. 不复制整套 state snapshot，不形成第四套状态镜像。

不推荐：

1. 把 increment package 扩成完整 closeout package  
   - 会把阶段增量和最终收束混成一个对象。
2. 直接从 timeline 自动生成全部增量结论  
   - timeline 更适合记录发生过什么，不足以表达“哪些结论是本段确认的”。

## 6. 建议结构

建议新增文件：

```text
.governance/changes/<change-id>/increment-package.yaml
```

它属于：

- change 目录内的 continuity 增量摘要层
- 面向下一段工作包的结构化输入

它不替代：

- `handoff-package.yaml`
- `owner-transfer-continuity.yaml`
- `runtime/status/*.yaml`
- `runtime/timeline/events-YYYYMM.yaml`

## 7. 事实来源与生成规则

### 7.1 核心来源

1. `handoff-package.yaml`
2. `runtime/status/change-status.yaml`
3. `runtime/status/steps-status.yaml`
4. `runtime/timeline/events-YYYYMM.yaml`
5. `verify.yaml / review.yaml`（存在时）

### 7.2 可选增强来源

1. `owner-transfer-continuity.yaml`
2. `continuity-launch-input.yaml`
3. `ROUND_ENTRY_INPUT_SUMMARY.yaml`

### 7.3 关键判断

increment package 虽然是 continuity 对象，但它不能纯靠派生自动生成高质量结论。

原因是：

1. `new_findings`
2. `invalidated_assumptions`
3. `new_risks`
4. `next_followups`

这些内容带有明确的人/agent 判断，不是 runtime 文件天然已有的字段。

因此本轮明确：

1. increment package 是“派生 + 显式输入”的混合对象；
2. 当前状态相关字段必须来自 handoff / runtime status；
3. 增量判断字段由 CLI 输入并记录。

## 8. 最小 schema

建议最小字段如下：

```yaml
schema: increment-package/v1
change_id: CHG-20260424-001
generated_at: 2026-04-24T12:00:00Z

increment_context:
  increment_reason: "post-verify update"
  segment_owner: "verifier-agent"
  segment_label: "verify-to-review"

state_anchor:
  current_status: "step7-verified"
  current_step: 7
  current_phase: "Phase 3 / 执行与验证"
  next_decision: "Step 8 / Review and decide"

delta:
  new_findings:
    - "runtime status schema 已稳定"
  invalidated_assumptions:
    - "timeline 可以只靠生成式补写"
  new_risks:
    - "owner transfer 尚未进入 review trace"
  blockers:
    - "review gate still pending"
  next_followups:
    - "prepare review decision"

refs:
  handoff_package: .governance/changes/CHG-20260424-001/handoff-package.yaml
  runtime_change_status: .governance/runtime/status/change-status.yaml
  runtime_timeline: .governance/runtime/timeline/events-202604.yaml
  verify: .governance/changes/CHG-20260424-001/verify.yaml
  owner_transfer: .governance/changes/CHG-20260424-001/owner-transfer-continuity.yaml
```

说明：

1. `state_anchor` 是受控镜像字段，只用于标记本段增量发生时的状态锚点。
2. 其唯一权威来源应来自：
   - `handoff-package.yaml`
   - `runtime/status/change-status.yaml`
3. `delta` 是 increment package 新增的记录层，不来自已有派生对象。
4. `owner_transfer` ref 为可选字段，仅在存在时写入。

## 9. 最小生命周期

本轮建议最小生命周期只有一步：

1. `materialize`
   - 若 `handoff-package.yaml` 不存在，先 materialize handoff package
   - 读取当前状态锚点
   - 写入 `increment_reason / segment_owner / segment_label`
   - 写入 `delta` 中的 4 类增量内容

本轮明确不做：

1. `update`
2. `merge`
3. `history list`

## 10. 最小 CLI 设计

建议新增：

```bash
ocw continuity increment-package \
  --change-id CHG-20260424-001 \
  --reason "post-verify update" \
  --segment-owner verifier-agent \
  --segment-label verify-to-review \
  --new-finding "runtime status schema 已稳定" \
  --invalidated-assumption "timeline 可以只靠生成式补写" \
  --new-risk "owner transfer 尚未进入 review trace" \
  --blocker "review gate still pending" \
  --next-followup "prepare review decision"
```

### 10.1 命令职责

1. 若 `handoff-package.yaml` 不存在，先 materialize handoff package
2. 生成 `.governance/changes/<change-id>/increment-package.yaml`
3. 当前状态字段全部来自 handoff / runtime status
4. `delta` 中的结构化内容由 CLI 输入

### 10.2 本轮失败规则

1. change 不存在
2. handoff package 无法生成
3. 缺少 `reason / segment-owner / segment-label`
4. 所有 `delta` 输入都为空

## 11. 与后续能力的关系

### 11.1 与 handoff package

handoff package 仍是默认接手入口。  
increment package 不是替代 handoff，而是记录“这段新增了什么”。

### 11.2 与 owner transfer continuity

owner transfer continuity 记录“谁变了”。  
increment package 记录“内容变了什么”。

两者一起才能完整回答：

1. 状态是如何变化的
2. 由谁接走了
3. 本段又新增了哪些判断

### 11.3 与 round-entry

后续 round-entry summary 可以优先引用最近一次 increment package，减少重复压缩工作。

## 12. 最小测试建议

本轮最小测试至少覆盖：

1. 能生成 `increment-package.yaml`
2. 若 handoff 不存在，会先 materialize handoff
3. `state_anchor` 来自 handoff / runtime status
4. `delta` 中的显式输入被正确记录
5. `owner_transfer` 不存在时不失败
6. 所有 delta 输入为空时应失败

## 13. 一句话结论

`increment package` 的最小成立，不在于“更完整地总结一切”，而在于把“本段真正新增了什么、推翻了什么、留下了什么”沉淀成下一段可直接复用的结构化输入。  

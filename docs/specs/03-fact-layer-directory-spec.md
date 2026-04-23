# open-cowork 事实层目录规范

## 1. 目标
定义 open-cowork 的分层治理目录、权威等级、生命周期和读取策略，防止当前事实与历史、运行态混杂。

## 2. 顶层目录
```text
.governance/
  stable/
  changes/
  runtime/
  archive/
  index/
```

说明：MVP 可将以上目录放在项目根下的 `.governance/`，也可在独立治理目录中承载；默认不得深改业务项目原有结构。

## 3. 分层说明
### 3.1 stable/
用途：存放当前有效、已通过治理流程确认的稳定事实。
权威等级：最高。
生命周期：持续存在，可被后续 change 引用和更新。
可被 AI 高权重读取：是。
禁止：
- 混入草稿、未批准设计、原始日志。
- 直接写入未经 review/approval 的执行结论。

建议子目录：
```text
stable/
  product/
  architecture/
  governance/
  maintenance/
```

### 3.2 changes/
用途：存放正在进行中的 change package。
权威等级：中。
生命周期：从 Step 4/5 建立，到 Step 8 决策完成后结束。
可被 AI 高权重读取：条件性读取，仅当前 change 与相关步骤高权重。
禁止：
- 取代 stable 作为全局当前真相源。

### 3.3 runtime/
用途：存放执行中间态、任务状态、临时产物、工作日志指针。
权威等级：低。
生命周期：短期。
可被 AI 高权重读取：否，默认低权重。
禁止：
- 将 runtime 中间结果直接视为最终事实。
- 用 runtime 替代 archive 或 stable。

### 3.4 archive/
用途：存放已完成 change 的全量归档材料。
权威等级：历史权威，不是当前事实权威。
生命周期：长期保存。
可被 AI 高权重读取：默认否，按需检索。
禁止：
- 让 archive 覆盖 stable。
- 将过时决策作为现行规则回灌。

### 3.5 index/
用途：存放索引、导航、摘要、映射、状态聚合。
权威等级：派生层，不是事实源。
生命周期：可重建。
可被 AI 高权重读取：可读，但必须追溯原事实层。
禁止：
- 把 index 当作唯一真相源。

## 4. 权威等级矩阵
| 层 | 是否当前真相 | 是否可直接引用为决策依据 | 是否可覆盖 stable |
|---|---|---|---|
| stable | 是 | 是 | 不适用 |
| changes | 否（仅 change 范围内阶段性有效） | 是，需结合 gate 状态 | 否 |
| runtime | 否 | 否 | 否 |
| archive | 否（历史） | 是，需显式说明为历史参考 | 否 |
| index | 否（派生） | 仅导航用途 | 否 |

## 5. 最小目录与文件建议
```text
.governance/
  stable/
    governance/current-model.md
    maintenance/current-iteration-context.md
  changes/
    CHG-YYYYMMDD-001/
      intent.md
      requirements.md
      design.md
      tasks.md
      contract.yaml
      evidence/
      verify.yaml
      review.yaml
  runtime/
    sessions/
    locks/
    temp/
  archive/
    2026/
      CHG-YYYYMMDD-001/
  index/
    changes-index.yaml
    stable-map.yaml
    archive-map.yaml
```

## 6. 读取策略
- AI 高权重默认读取：stable + 当前 change 必要文件。
- AI 中权重读取：与当前 change 强相关的 archive 摘要。
- AI 低权重读取：runtime 原始日志。
- README：仅人类入口层，不作为机器事实源。

## 7. 生命周期规则
1. 输入被组装为 change package，进入 `changes/`。
2. 执行中间态进入 `runtime/`。
3. 审查通过后，稳定结论进入 `stable/`。
4. 该 change 的完整材料归档到 `archive/`。
5. `index/` 更新映射与摘要。

## 8. 阻断条件
- stable 与 archive 混用。
- README 承担机器事实职责。
- runtime 无边界外溢为当前事实。
- 无 index 导航导致维护不可持续。

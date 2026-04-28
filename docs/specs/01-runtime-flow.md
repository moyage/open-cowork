# 01. Runtime Flow

open-cowork 使用 4 个阶段和 9 个标准步骤。Step 名称必须使用中文动作名 + 英文锚点，方便人理解，也方便跨 Agent 对齐。

| Step | 名称 | Gate 语义 |
| --- | --- | --- |
| 1 | 明确意图 / Clarify intent | intent confirmation 可满足 Step 1 approval。 |
| 2 | 确定范围 / Lock scope | scope、非目标和验收标准确认。 |
| 3 | 方案设计 / Shape approach | 方案、风险、open questions 可被 review。 |
| 4 | 组装变更包 / Assemble change package | 可记录 human acknowledgement，但默认不是阻塞 gate。 |
| 5 | 批准开工 / Approve execution | 阻塞 gate；批准后才能进入 Step 6。 |
| 6 | 执行变更 / Execute change | 在 Contract 范围内执行并记录 Evidence。 |
| 7 | 验证结果 / Verify result | 记录 governance state verification；可选择执行 product verification commands。 |
| 8 | 独立审查 / Independent review | 先记录 reviewer decision，再由人确认是否接受该 decision。 |
| 9 | 归档接续 / Archive and handoff | 需要 review approved、Step 8 acceptance 和 Step 9 archive approval。 |

## Gate 与 acknowledgement

- **Gate approval** 会阻塞流程推进。
- **Acknowledgement** 只记录人的参与痕迹，不改变 lifecycle。
- `intent confirm` 是 Step 1 的核心 gate，因此会自动写入 Step 1 approval source。
- Step 4 等非阻塞步骤可以记录 acknowledgement，避免人的确认被挪到不准确的 Step。
- Step 5 的批准含义是按当前 change package、contract 和验收标准完整执行；若要降级、拆分、延期或缩减范围，必须在进入 Step 6 前获得人的新批准。

## Strict single-step

Human-gated step 只能按当前 lifecycle 顺序批准。已推进到后续 step 的历史 gate 会被视为已经通过，不再阻止补记当前 gate。

## 禁止未批准降级

Step 6 执行、Step 7 验证、Step 8 审查和 Step 9 归档都必须以已批准范围为准。Agent 不得自行把需求改成最小实现、部分实现或后续再补；Reviewer 发现未获批准的范围缩减、验收降级或任务遗漏时，必须给出阻塞性 revise / reject，而不能 approve。

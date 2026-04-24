# open-cowork Milestone 2 Truth-Source / Artifact Boundary Hardening 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / Workstream A` 的下一段硬边界工作收口为：

> `executor` 不得触碰 `.governance/changes/**` 包体

上一轮已经阻断了：

1. `.governance/index/**`
2. `.governance/runtime/**`
3. `.governance/archive/**`
4. `.governance/changes/**/*.yaml`

但当前仍存在一个更细的边界缺口：

`executor` 仍可通过 artifacts 声明触碰 `.governance/changes/<change-id>/` 下的 markdown、文本或其他非 YAML 文件，这会让 change package 包体与执行产物继续混层。

## 2. 设计目标

本轮目标如下：

1. 把 `.governance/changes/**` 整体收口为治理包体保留区。
2. 明确 `executor` 只能修改 repo 工作产物，而不能修改 change package 包体。
3. 保持 evidence 仍由治理层自行物化，不要求 `executor` 直接写任何 `.governance/changes/**` 文件。
4. 不改变 continuity / closeout / sync 等已有命令的调用方式。

## 3. 边界

### 3.1 本轮纳入

1. `run_change(...)` 阻断 `.governance/changes/**` 全部 executor artifacts
2. 新增对应单元测试
3. 文档索引与 Baseline 同步

### 3.2 本轮明确不做

1. OS 级真实写入拦截
2. 对 repo 代码目录的更细粒度分类
3. `scope_in / scope_out` 语义重构
4. change package 内新增“executor 可写辅助目录”

### 3.3 但必须兼容

1. 治理层自己物化：
   - `evidence/**`
   - `verify.yaml`
   - `review.yaml`
   - continuity / closeout / sync 各类 packet
2. `executor` 继续正常写：
   - `src/**`
   - `tests/**`
   - contract 明确允许的 repo 工作目录

## 4. 推荐方案

推荐采用：

> `change package subtree reserved-by-default`

也就是：

1. `executor` 声明的 artifacts 一旦命中 `.governance/changes/`，直接阻断；
2. 不再只看后缀是否为 `.yaml`；
3. 将整个 change package 视为治理包体，而非执行工作目录。

不推荐：

1. 仅把 markdown 也额外列入黑名单  
   - 规则仍然零散，后续容易继续漏出 `.txt`、`.json`、`.log` 等旁路。
2. 为 `executor` 在 `.governance/changes/` 下保留多个可写例外目录  
   - 现在会把边界重新做复杂，收益不高。

## 5. authoritative source 与生成规则

1. `.governance/changes/<change-id>/` 整体属于治理包体。
2. 包体内既包括权威事实源，也包括派生 packet 与人类阅读材料。
3. 即使某些文件不是最终 truth-source，它们也不应由 `executor` 直接声明写入。
4. `executor` 的职责仍是修改工作产物，不是修改治理包体。

## 6. 规则

### 6.1 必须阻断

`executor` artifacts 不得触碰：

1. `.governance/changes/<change-id>/**`

包括但不限于：

1. `intent.md`
2. `requirements.md`
3. `design.md`
4. `tasks.md`
5. `manifest.yaml`
6. `contract.yaml`
7. `bindings.yaml`
8. `verify.yaml`
9. `review.yaml`
10. `evidence/**`
11. `handoff-package.yaml`
12. `owner-transfer-continuity.yaml`
13. `increment-package.yaml`
14. `continuity-launch-input.yaml`
15. `ROUND_ENTRY_INPUT_SUMMARY.yaml`

### 6.2 明确保留

以下写入仍允许：

1. 治理层在 `run_change(...)` 之后物化 evidence
2. 其他 governance 命令写 continuity / closeout / sync 相关文件
3. repo 工作目录中的真实代码和测试文件

## 7. 最小测试建议

建议至少覆盖：

1. `executor` 触碰 `.governance/changes/<id>/tasks.md` 被拒绝
2. `executor` 触碰 `.governance/changes/<id>/requirements.md` 被拒绝
3. `executor` 触碰 `.governance/changes/<id>/evidence/manual-note.txt` 被拒绝
4. 现有 repo 工作目录写入仍通过

## 8. 价值

这份设计的价值在于：

1. 把 change package 从“可能被执行层顺手改动”的半开放目录，收成明确治理包体；
2. 让 continuity / handoff / increment / sync 的上游输入更可信；
3. 进一步压实“执行产物”和“治理包体”分层；
4. 为后续如果真要开放 executor 辅助输出目录，保留清晰的显式设计入口。

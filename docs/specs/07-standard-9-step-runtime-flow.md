# open-cowork 标准 9 步运行流程规格

## 1. 总原则
- 9 步是固定骨架，不得删除。
- 复杂度决定每步强度，不决定是否存在该步。
- 每步都支持 gate。
- 运行状态必须同时表达 `gate_type`、`gate_state` 和 `approval_state`，避免把 review、approval、not-required 混成一个 `approval` 字段。
- Step 8 必须产出明确 decision。
- Step 9 不可跳过。

## 2. 9 步总表
| Step | 名称 | 目标 | 主要输入 | 主要输出 | Owner | Gate 默认 |
|---|---|---|---|---|---|---|
| 1 | 输入接入与问题定界 | 接入多源输入并形成问题边界 | 原始需求、参考资料、约束 | framed input、约束池 | Human Sponsor / Orchestrator | review-required |
| 2 | 意图澄清与范围定义 | 明确目标、边界、非目标、复杂度 | Step1 输出 | scope、non-goals、policy level | Analyst / Architect | approval-required |
| 3 | 方案塑形 | 形成设计基线与方案方向 | Step2 输出、参考分析 | design baseline、能力边界 | Analyst / Architect | review-required |
| 4 | 变更包组装 | 形成结构化工作单元 | Step3 输出 | change package 初稿 | Orchestrator | review-required |
| 5 | 角色绑定与执行准备 | 绑定角色、gate、isolation、contract | change package | bindings、contract ready | Human Sponsor / Orchestrator | approval-required |
| 6 | 隔离执行 | 在受控环境执行 | contract、bindings | 产物、evidence | Executor | auto-pass 到 Step7 |
| 7 | 验证与纠偏 | 检查结果并回流修正 | 产物、evidence | verify result、issues | Verifier | review-required |
| 8 | 审查与决策 | 独立决定是否通过 | verify、evidence、change package | review decision | Reviewer / Sponsor | approval-required |
| 9 | 归档与维护状态更新 | 归档、更新 stable、刷新维护上下文 | approved outputs | archive、stable updates、index refresh | Maintainer / Governance | approval-required |

## 2.1 Gate 状态语义

`gate_type` 表示该步骤需要哪类控制：

- `review-required`：需要 review/确认步骤产物，但不等同于 approval gate。
- `approval-required`：必须有人类或授权 sponsor 明确 approve/revise/reject。
- `auto-pass-to-step7`：Step 6 执行完成后进入 Step 7 验证，但仍必须保留 execution evidence。

`gate_state` 表示 gate 当前推进状态：

- `not-started`
- `waiting-review`
- `reviewed`
- `waiting-approval`
- `approved`
- `bypassed`
- `blocked`
- `not-required`

`approval_state` 只用于 `approval-required`：

- `not-required`
- `required-pending`
- `approved`
- `bypassed`

兼容旧输出时可以继续显示 `approval`，但它只能作为简化 alias；人类可读 status/report 必须优先显示三层语义。

## 3. 分步细则
### Step 1 输入接入与问题定界
输入：多源问题、历史背景、参考项目、限制条件。
输出：framed input、初始约束池、问题范围。
禁止：直接跳到实现方案。

### Step 2 意图澄清与范围定义
输入：Step1 输出。
输出：目标、边界、非目标、复杂度档位。
禁止：边界未清仍生成 contract。

### Step 3 方案塑形
输入：scope、参考分析。
输出：设计基线、能力地图、结构性原则。
禁止：把参考项目机械拼装成目标架构。

### Step 4 变更包组装
输入：设计基线。
输出：change package 初稿、交付清单。
禁止：缺少 tasks/contract 预留即进入执行准备。

### Step 5 角色绑定与执行准备
输入：change package 初稿。
输出：bindings、gate policy、isolation strategy、final contract。
禁止：无明确角色边界就进入 Step 6。
人类确认应提供短选项，例如 `approve` / `revise` / `reject`，不应要求人记忆长篇固定审批句。

### Step 6 隔离执行
输入：contract、bindings。
输出：目标产物、execution evidence。
要求：默认使用隔离目录 / worktree / sandbox 等低侵入方式。
禁止：执行者直接写 stable facts。

### Step 7 验证与纠偏
输入：产物、evidence、验证计划。
输出：verify result、问题分级、修正回流。
禁止：把 verify 写成纯主观好坏评价。

### Step 8 审查与决策
输入：verify result、evidence、change package、顶层约束。
输出：approve/reject/revise decision。
禁止：无 decision 即视为通过。

### Step 9 归档与维护状态更新
输入：approved outputs、review decision。
输出：archive、副本、stable updates、index refresh、next-iteration context。
禁止：只归档不更新 stable / index / maintenance context。

## 4. Lite / Standard / Strict 裁剪规则
| Step | Lite | Standard | Strict |
|---|---|---|---|
| 1 | 输入摘要即可 | 标准边界澄清 | 完整输入归集 + 风险项 |
| 2 | 精简 scope | 标准 scope + non-goals | 完整边界 + 风险与假设 |
| 3 | 轻量方案 | 标准方案塑形 | 替代方案比较 |
| 4 | 精简 package | 标准 package | 完整 package + manifest |
| 5 | 基本绑定 | 标准双层绑定 | 严格审批 + isolation detail |
| 6 | 单 adapter | 单 adapter + evidence | 更完整执行记录 |
| 7 | 最小 verify | 标准 verify | 完整 taxonomy |
| 8 | reviewer 决策 | reviewer + sponsor | 多方审批 |
| 9 | 基础归档 | 归档 + stable + index | 再加维护上下文刷新证明 |

## 5. 传统流程映射
- Step1-2 ≈ 需求接收与澄清
- Step3 ≈ 架构/方案设计
- Step4-5 ≈ 实施包准备与角色分工
- Step6 ≈ 受控开发/执行
- Step7 ≈ 测试验证
- Step8 ≈ 评审验收
- Step9 ≈ 归档与维护交接

## 6. 核心审计点
- 是否出现 Step 2/3 直接跳 Step 6 的偷跑。
- 是否缺失任一步的输入/输出/gate。
- `change prepare` 是否只生成准备材料，而不是把 Step 1-5 标记为完成。
- Step 5 / Step 8 / Step 9 是否分别保留 human gate trace。
- Step 8 是否有明确 decision。
- reviewer mismatch bypass 是否记录 reason、recorded_by、evidence_ref。
- Step 9 是否真实更新维护状态。

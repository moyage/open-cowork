# open-cowork 首个工程实现 Change Package 桥接规格

## 1. 目的
本文件是 Step 5 收口到 Step 6 开始之间的桥接件。

它只定义“首轮真实工程执行前必须具备什么”，用于把已有规格文档转成首个可执行的工程实现 change package。

本文件不包含业务代码，不宣称 Step 6 已开始，也不替代 `04-change-package-spec.md`、`05-execution-contract-spec.md`、`06-evidence-verify-review-schema.md`。

## 2. 适用时机
当满足以下前提时，应使用本桥接规格：
- 规格化主干文档已完成。
- 当前位于 Step 5：角色绑定与执行准备。
- 下一步目标是创建首个真实工程实现 change package。
- 准备进入 Step 6，但尚未允许 executor 开始实现。

## 3. 桥接目标
在进入 Step 6 前，把“已有规格”收束成“可执行但尚未执行”的最小工程 change package，确保：
- change package 文件齐备。
- 角色绑定明确。
- execution contract 可执行且边界清晰。
- verify / review / archive 路径已预留。
- executor adapter 的请求/响应绑定点已明确。
- 不需要执行者猜目录、猜字段、猜输出位置。

## 4. 首个工程实现 change package 的最小落盘结构
```text
.governance/
  changes/
    <change-id>/
      intent.md
      requirements.md
      design.md
      tasks.md
      contract.yaml
      bindings.yaml
      verify.yaml
      review.yaml
      manifest.yaml
      evidence/
  index/
    current-change.yaml
    changes-index.yaml
```

说明：
- `evidence/` 在 Step 5 末尾就必须先建好目录，Step 6 开始后持续写入。
- `verify.yaml`、`review.yaml` 在 Step 5 末尾必须完成结构预留，不能等执行后再补壳。
- `archive/` 在本桥接阶段不要求生成归档副本，但必须在 contract、review 或 manifest 中保留归档去向约束。

## 5. 必备文件要求
### 5.1 intent.md
必须明确：
- 本 change 的工程目标。
- 本轮不做什么。
- 对应的 MVP 边界。
- 与已有规格文档的来源关系。

禁止：
- 把顶层 PRD 重写一遍。
- 把实现细节写成散乱 TODO。

### 5.2 requirements.md
必须明确：
- 必须交付的工程能力。
- 不可突破的治理约束。
- 必须保留的低侵入原则。
- 验证与审计上的硬性条件。

至少应覆盖：
- 治理目录建立要求。
- change package 读写要求。
- contract 驱动执行要求。
- evidence / verify / review / archive 主链路要求。
- 单一 adapter MVP 要求。

### 5.3 design.md
必须明确：
- 首轮实现只覆盖哪些链路。
- 目录与模块边界如何映射规格。
- CLI、index、adapter、evidence 链路如何对接。
- 哪些能力保留到后续 change。

禁止：
- 把未来完整系统一次性塞入首轮 change。
- 以设计名义扩大发散范围。

### 5.4 tasks.md
必须明确：
- 任务顺序。
- 每个任务的完成判据。
- 哪些任务属于 Step 6 执行。
- 哪些任务属于 Step 7/8/9 的预留，不在 Step 6 内完成审批本身。

建议按以下顺序组织：
1. 建立最小治理目录与索引文件。
2. 创建首个 change package 读写链路。
3. 创建 contract 生成或装载链路。
4. 接入一个 executor adapter。
5. 接入 evidence 写入。
6. 接入 verify / review / archive 的落盘链路。

### 5.5 manifest.yaml
至少必须包含：
```yaml
change_id: CHG-YYYYMMDD-001
status: step5-ready
current_step: 5
policy_level: standard
owner: orchestrator
files:
  required:
    - intent.md
    - requirements.md
    - design.md
    - tasks.md
    - contract.yaml
    - bindings.yaml
    - verify.yaml
    - review.yaml
    - manifest.yaml
  directories:
    - evidence/
readiness:
  step6_entry_ready: false
  missing_items: []
```

要求：
- `status` 必须反映“已准备、未执行”。
- `current_step` 在进入执行前必须仍为 `5`。
- `readiness.step6_entry_ready` 只有在全部检查通过后才能改为 `true`。

## 6. bindings.yaml 必备内容
首个真实工程 change 在 Step 5 末尾必须存在 `bindings.yaml`，且至少覆盖 Step 5-9。

最小要求：
```yaml
change_id: CHG-YYYYMMDD-001
global:
  sponsor: <id>
  orchestrator: <id>
  analyst: <id>
  default_reviewer: <id>
  default_maintainer: <id>
  default_executor_type: <adapter-type>
steps:
  '5':
    owner: <id>
    approver: <id>
    gate: approval-required
  '6':
    owner: <id>
    executor: <id>
    verifier: <id>
    gate: auto-pass
    isolation: <sandbox|worktree|isolated-dir>
  '7':
    owner: <id>
    verifier: <id>
    gate: review-required
  '8':
    owner: <id>
    reviewer: <id>
    approver: <id>
    gate: approval-required
  '9':
    owner: <id>
    maintainer: <id>
    gate: approval-required
```

绑定约束：
- Executor 不得兼任最终独立 Reviewer。
- Maintainer 不能缺位，因为 Step 9 不可跳过。
- Step 6 必须声明 isolation 策略，不能默认在主工作区裸跑。
- 若个人域同一人承担多个角色，也必须在文件中显式写出，而不是省略。

## 7. contract.yaml 必备字段
首个真实工程实现 change 的 `contract.yaml` 必须是“可执行 contract”，不是抽象愿景。

最小字段要求：
```yaml
schema: execution-contract/v1
change_id: CHG-YYYYMMDD-001
title: <工程实现 change 标题>
objective: <本轮最小闭环目标>
scope_in: []
scope_out: []
allowed_actions: []
forbidden_actions: []
inputs:
  required: []
outputs:
  required: []
verification:
  commands: []
  checks: []
evidence_expectations:
  required: []
review_handoff:
  required_reviewers: []
failure_policy:
  on_blocker: halt_and_report
```

额外约束：
- `scope_in` 必须明确允许改动的代码、测试、治理文件范围。
- `scope_out` 必须明确禁止改动的无关区域。
- `inputs.required` 必须包含本轮依赖的规格文档与 change package 文件。
- `outputs.required` 必须包含治理索引、change package 核心文件及预期工程产物范围。
- `verification.checks` 必须覆盖 contract 驱动执行、证据落盘、verify/review/archive 不可绕过。
- `evidence_expectations.required` 至少应覆盖 `file_diff`、`command_output`、`test_output`、`changed_files_manifest`。

## 8. adapter 绑定点
在进入 Step 6 前，不要求写完 adapter 业务实现，但必须明确 adapter 绑定点。

至少要能回答：
- 本轮使用哪个 `adapter_type`。
- contract 从哪里传入 adapter。
- 隔离工作目录在哪里生成。
- adapter 返回哪些结构化字段用于写入 evidence。
- 失败时由谁中止并回报 blocker。

最小绑定关系建议在以下位置可追踪：
- `bindings.yaml`：声明默认 executor type 与 Step 6 owner/executor。
- `contract.yaml`：声明允许动作、输入输出、验证与证据要求。
- `design.md`：说明 adapter 链路如何挂接到 CLI 和治理目录。

## 9. verify / review / archive 预留要求
### 9.1 verify.yaml
在 Step 5 结束前必须已有结构化骨架，至少包含：
```yaml
schema: verify-result/v1
change_id: CHG-YYYYMMDD-001
verifier:
  role: verifier
  id: <id>
checks: []
summary:
  status: pending
  blocker_count: 0
  major_count: 0
  minor_count: 0
issues: []
```

要求：
- `status` 初始值应体现“未验证”或“待验证”语义，不能伪造 pass。
- `checks` 至少预留 contract、产物、证据、边界、命令结果几类检查位。

### 9.2 review.yaml
在 Step 5 结束前必须已有结构化骨架，至少包含：
```yaml
schema: review-decision/v1
change_id: CHG-YYYYMMDD-001
reviewers:
  - role: reviewer
    id: <id>
decision:
  status: pending
  rationale: ''
conditions:
  must_before_next_step: []
  followups: []
trace:
  evidence_refs: []
  verify_refs:
    - verify.yaml
```

要求：
- 不允许在尚未 review 时写入 `approve`。
- 必须预留 `trace`，因为审查不是脱离 evidence 和 verify 独立发生。

### 9.3 archive 预留
首轮工程 change 在 Step 5 不要求立即生成归档副本，但必须明确归档预留。

至少满足其一：
- `manifest.yaml` 中声明归档目标位置或状态流转。
- `review.yaml.conditions.followups` 中声明 Step 9 归档动作。
- `contract.yaml.outputs.required` 中声明归档回执或归档相关索引更新产物。

最低要求不是“已经归档”，而是“归档路径与责任已被定义”。

## 10. Step 6 准入清单
只有以下检查全部通过，才允许从 Step 5 进入 Step 6：
1. 首个 change package 已在 `.governance/changes/<change-id>/` 落盘。
2. `intent.md`、`requirements.md`、`design.md`、`tasks.md`、`contract.yaml`、`bindings.yaml`、`verify.yaml`、`review.yaml`、`manifest.yaml` 全部存在。
3. `evidence/` 目录已创建且可写。
4. `bindings.yaml` 已覆盖 Step 5-9，且角色冲突合法。
5. `contract.yaml` 已具备可执行字段，不存在模糊 scope。
6. adapter 绑定点已明确，隔离策略已声明。
7. verify / review / archive 预留已结构化落盘。
8. `manifest.yaml.current_step` 仍为 `5`，未伪造执行完成。
9. 进入 Step 6 的审批 gate 已满足或被明确批准。

## 11. 禁止事项
- 直接拿规格文档当 change package 使用，不落盘首个真实工程 change。
- 只有 `contract.yaml`，却没有 `bindings.yaml`、`verify.yaml`、`review.yaml` 预留。
- Step 6 开始后才临时创建 `evidence/`。
- 让 executor 自行猜测允许改什么、输出写到哪里。
- 在桥接文档里写业务实现代码或声称实现已完成。
- 把 review / archive 视为“后面再说”的口头动作，不做结构化预留。

## 12. 与其他规格的关系
- `04-change-package-spec.md` 定义通用 change package 结构；本文件定义首个真实工程实现 change 在 Step 5 末尾的收口要求。
- `05-execution-contract-spec.md` 定义 contract 通用字段与示例；本文件强调首轮工程执行前 contract 必须达到“可执行”而非“仅示意”。
- `06-evidence-verify-review-schema.md` 定义 verify / review 的最小 schema；本文件要求在执行前完成骨架预留。
- `07-standard-9-step-runtime-flow.md` 定义 Step 5-9 生命周期；本文件是 Step 5 进入 Step 6 的准入桥接。
- `11-executor-adapter-interface.md` 定义 adapter 接口；本文件要求在首轮工程 change 中把 adapter 绑定点明确到可接线状态。

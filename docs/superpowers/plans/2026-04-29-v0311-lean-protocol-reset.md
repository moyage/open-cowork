# v0.3.11 精简协议重置实施计划

> **给 Agent 执行者的要求：** 实施本计划时必须逐项推进、逐项验证、逐项提交。若采用多 Agent 协作，必须使用真实本地 Agent 或人明确授权的 Codex Subagent，不得伪造第三方执行、Review 或批准结论。

**目标：** 将 open-cowork v0.3.11 实现为可长期运行、可多人/多 Agent 协作、默认读取集和治理状态有界的轻量协同治理协议。

**权威关系：** 若本计划与 `docs/specs/08-v0311-lean-protocol-reset.md` 冲突，以规格文档为准；本计划只负责把规格拆成可执行任务。

**总体架构：** 新增 v0.3.11 compact state layer。正常命令只维护 `.governance/` 下的固定轻量文件；旧版 `changes/`、`archive/`、`runtime/`、`index/`、`local/` 只能被迁移、清理、冷存储读取或显式兼容处理，不能在默认流程中被重新创建。

**命名约定：** 文档和新命令以 `ocw` 为主命令；`open-cowork` 可作为兼容别名。实现层应共用同一套 handler，避免两套路由产生语义差异。

---

## 1. 不可变要求

- 版本是 `v0.3.11`，不是 `v4.0`。
- 默认读取集必须保持小而固定。
- 默认运行面不得创建每轮目录树。
- 个人域单 Agent、个人域多 Agent、团队域多 Agent 共用同一套 compact state model。
- 历史只以摘要、引用、hash、路径、外部 ref 表达，不复制完整轮次目录。
- `resume`、`status`、`preflight` 和 review 入口不得扫描冷历史。
- 不允许自动降级、最小实现替代完整实现、伪造授权、事后补写授权。
- 不同 Agent runtime 对流程状态和 gate 的判定必须一致。
- 旧安装必须支持 detect、dry-run、migrate、verify、cleanup receipt、uninstall。
- 新增产出文档使用中文。

## 1.1 Review 问题追踪

| Review 问题 | 方案收口位置 | 实现/测试覆盖 |
| --- | --- | --- |
| 默认文件集缺 `agent-entry.md` / `templates/` | 第 2 节默认治理布局 | 任务 1、任务 2、任务 12 |
| 授权模型不能只看 `human:*` 字符串 | 第 3.1 节、任务 4 | `tests/test_v0311_gates.py` |
| 阶段枚举与 closeout gate 不一致 | 第 4 节、任务 5、任务 8 | `tests/test_v0311_gates.py`、`tests/test_state_consistency.py` |
| `state.yaml` schema 过薄 | 第 3.1 节、任务 2 | `tests/test_v0311_lean_state.py` |
| 协作者模型过窄 | 第 3.1 节、任务 3 | `tests/test_v0311_gates.py` |
| 旧版本迁移、清理、卸载不足 | 第 7 节、任务 9 | `tests/test_v0311_migration.py` |
| 上下文预算和压力测试不足 | 第 3.2、3.3、任务 11 | `tests/test_v0311_pressure.py` |
| 文档、dogfood、发布 gate 不完整 | 任务 12、任务 13、任务 14 | 文档 grep、完整测试、人工发布授权 |

## 2. 默认治理布局

v0.3.11 默认布局：

```text
.governance/
  AGENTS.md
  agent-entry.md
  agent-playbook.md
  state.yaml
  current-state.md
  ledger.yaml
  evidence.yaml
  rules.yaml
  templates/
```

可选冷存储：

```text
.governance/cold/
  legacy/
  artifacts/
```

默认废弃目录：

```text
.governance/changes/
.governance/archive/
.governance/runtime/
.governance/index/
.governance/local/
```

默认读取集：

```text
.governance/AGENTS.md
.governance/agent-entry.md
.governance/current-state.md
.governance/state.yaml
```

专项读取集：

```text
.governance/ledger.yaml
.governance/evidence.yaml
.governance/rules.yaml
.governance/agent-playbook.md
.governance/templates/
```

说明：

- `resume`、`status`、`preflight` 默认只读取默认读取集。
- `ledger.yaml`、`evidence.yaml`、`rules.yaml` 只在统计、验证、审查、规则和收束场景读取。
- `agent-playbook.md` 和 `templates/` 是默认布局的一部分，但只在 Agent 指南渲染、模板生成或文档更新场景读取；不得因为它们存在就扩大常规状态恢复上下文。

冷历史永远不默认读取。

## 3. 最小权威 Schema

`state.yaml` 是唯一机器权威当前状态。`current-state.md` 从它生成，不具备权威性。

### 3.1 `state.yaml`

```yaml
protocol:
  name: open-cowork
  version: 0.3.11
layout: lean
default_read_set:
  - .governance/AGENTS.md
  - .governance/agent-entry.md
  - .governance/current-state.md
  - .governance/state.yaml
active_round:
  round_id: R-20260429-001
  goal: "面向人的简短目标"
  phase: intent-scope
  scope:
    in: []
    out: []
  acceptance:
    summary: ""
    done_definition: full-scope
  plan:
    summary: ""
    steps: []
    risks: []
    assumptions: []
  verification_plan:
    commands: []
    external_rules: []
    reviewer_required: true
  participants:
    sponsor: ""
    owner_agent: ""
    orchestrator: ""
    executor: ""
    reviewer: ""
    advisors: []
  participant_initialization:
    status: pending
    required_roles:
      - sponsor
      - owner_agent
      - executor
      - reviewer
    initialized_roles: []
    missing_roles:
      - sponsor
      - owner_agent
      - executor
      - reviewer
    role_bindings:
      - role: owner_agent
        actor: ""
        responsibility: ""
        authority_scope: []
        output_responsibility: []
        independence_requirement: ""
        evidence_ref: ""
    bypass:
      allowed: false
      requested_by: ""
      approved_by: ""
      approval_source: ""
      approval_channel: ""
      approval_evidence_ref: ""
      approved_at: ""
      reason: ""
      impact_scope: ""
  gates:
    execution:
      status: pending
      requested_by: ""
      approved_by: ""
      approval_source: ""
      approval_channel: ""
      approval_evidence_ref: ""
      created_by: ""
      created_at: ""
      reason: ""
    closeout:
      status: pending
      requested_by: ""
      approved_by: ""
      approval_source: ""
      approval_channel: ""
      approval_evidence_ref: ""
      created_by: ""
      created_at: ""
      reason: ""
  external_rules:
    active: []
    suspended: []
  evidence_refs: []
  verify:
    status: not-run
    summary: ""
    rule_results: []
  review:
    status: not-requested
    decision: ""
    reviewer: ""
    independent: true
    summary: ""
  implementation_commitment:
    mode: full-scope
    downgrade_allowed: false
    downgrade_approval: null
  closeout:
    status: open
    summary: ""
    remaining_risks: []
    completed: []
    not_completed: []
  carry_forward: []
decision_needed: []
context_budget:
  current_state_target_lines: 200
  state_target_lines: 400
updated_at: ""
```

强约束：

- phase 持久化只使用规格枚举：`intent-scope`、`plan-contract`、`execute-evidence`、`verify-review`、`closeout`。
- 授权不是字符串前缀检查。没有 `approval_evidence_ref` 的 gate approval 必须保持 `blocked` 或 `pending`。
- Agent 可以记录“请求授权”，但不能把自己传入的 `human:*` 当作真实批准。
- `implementation_commitment.mode` 默认 `full-scope`，除非存在外部授权证据，否则不能变成 partial/minimal/deferred。
- `plan` 和 `verification_plan` 必须写入 `state.yaml`，不能只存在聊天上下文或临时计划文件。
- `role_bindings` 必须采用统一 item schema，不能由 CLI、renderer、测试各自发明字段。
- 所有 phase、gate status、review status、review decision、rule failure impact 必须来自同一常量/枚举来源。

### 3.1.1 Review 状态组合

`review.status` 和 `review.decision` 必须满足：

| `review.status` | 允许的 `review.decision` | 是否允许 closeout |
| --- | --- | --- |
| `not-requested` | 空字符串 | 否 |
| `requested` | 空字符串 | 否 |
| `completed` | `approve` | 是，但仍需 verify pass、blocking rules pass、closeout gate approve |
| `completed` | `revise` | 否 |
| `completed` | `reject` | 否 |
| `blocked` | 空字符串或 `revise` | 否 |

非法组合必须在 schema validation 和 gate validation 中同时失败，例如 `status=completed` 但 `decision=""`。

### 3.1.2 `decision_needed` 生命周期

每个待决事项使用统一结构：

```yaml
- id: D-20260429-001
  status: open
  summary: ""
  requested_by: ""
  created_at: ""
  blocking: true
  resolved_by: ""
  resolved_at: ""
  resolution_summary: ""
  evidence_ref: ""
```

要求：

- `blocking=true` 且 `status=open` 时不能 closeout。
- 解决后的 decision 必须保留 resolution summary；`current-state.md` 只显示打开项和最近解决项。
- closeout 时已解决项压缩进 ledger summary，不复制完整历史。

### 3.2 `ledger.yaml`

每轮 closeout 只追加一条 compact record：

```yaml
- round_id: R-20260429-001
  started_at: ""
  closed_at: ""
  goal: ""
  scope_digest: ""
  participants_digest: ""
  final_status: closed
  verify_summary: ""
  review_summary: ""
  external_rules_summary: ""
  evidence_refs: []
  closeout_summary: ""
  carry_forward: []
```

预算：

- 超过 500 条 compact records 或 512 KB 时，`ocw hygiene` 警告。
- 只有显式 `ocw hygiene --rotate-ledger` 才能轮转。

### 3.3 `evidence.yaml`

```yaml
- evidence_id: E-20260429-001
  round_id: R-20260429-001
  kind: test
  ref: pytest tests -q
  summary: "测试通过"
  hash: ""
  created_by: codex
  created_at: ""
```

预算：

- 超过 1,000 条 refs 或 512 KB 时，`ocw hygiene` 警告。
- 大型证据永远放在默认读取集之外，只记录摘要和引用。

### 3.4 `rules.yaml`

```yaml
- id: lint
  name: "代码 lint"
  kind: command
  applies_to:
    - execute-evidence
    - verify-review
  command: ruff check src tests
  status: active
  failure_impact: blocking
  scope: current-round
  added_by: human:mlabs
  approval_evidence_ref: ""
  added_at: ""
  suspended_by: ""
  suspended_at: ""
  suspend_reason: ""
  suspend_until: ""
```

规则要求：

- `failure_impact` 只能是 `blocking`、`warning`、`advisory`。
- active round 中新增、暂停、移除 blocking rule 必须有外部授权证据。
- blocking rule 失败时不能 closeout，除非存在 human/team bypass evidence。

## 4. 流程阶段与 Gate

### 4.1 意图与范围：`intent-scope`

目标：

- 确认本轮真正要完成什么。
- 明确 scope in/out。
- 建立 round id 和验收摘要。

不得做：

- 不修改项目代码。
- 不进入执行。
- 不缩小已确认完整需求。

必要产出：

- `active_round.goal`
- `active_round.scope.in`
- `active_round.scope.out`
- `active_round.acceptance`

### 4.2 计划与契约：`plan-contract`

目标：

- 形成计划、角色绑定、验证方式、外部规则。
- 完成 participant initialization。
- 获取 execution gate 的外部授权。

必要产出：

- compact plan
- role bindings
- `participant_initialization.status`
- `gates.execution`
- verification plan
- active external rules

阻断条件：

- participant initialization 未完成。
- executor/reviewer 未分离且无外部 bypass evidence。
- execution gate 未批准。
- approval 没有 evidence ref。

### 4.3 执行与证据：`execute-evidence`

目标：

- 按完整 scope 执行。
- 写入有界 evidence refs。

不得做：

- 不得越过 scope in。
- 不得自动改成 minimal/partial/deferred。
- 不得用命令成功掩盖实现未完成。

必要产出：

- 项目变更。
- `evidence.yaml` 中的 evidence refs。
- `state.yaml` 中的执行摘要。
- 如阻塞，写入 `decision_needed`。

### 4.4 验证与审查：`verify-review`

目标：

- 执行内置验证和外部规则。
- 记录独立 Review。

必要产出：

- `verify.status`
- `verify.summary`
- `verify.rule_results`
- `review.status`
- `review.decision`
- `review.independent`

阻断条件：

- verify 失败。
- blocking rule 失败且无 bypass evidence。
- reviewer 与 executor 相同且无 human/team bypass evidence。
- review decision 不是 approve。

### 4.5 收束与接续：`closeout`

目标：

- 关闭本轮。
- 追加 compact ledger record。
- 留下 carry-forward。

必要产出：

- `gates.closeout`
- `closeout.summary`
- `closeout.remaining_risks`
- `closeout.completed`
- `closeout.not_completed`
- `carry_forward`
- `ledger.yaml` compact record
- 更新后的 `state.yaml`
- 更新后的 `current-state.md`

阻断条件：

- closeout gate 未批准。
- verify/review 未通过。
- closeout summary 缺失。
- ledger append 失败。

## 5. 命令面

文档主命令：

```bash
ocw init
ocw resume
ocw status
ocw round start
ocw round participants init
ocw round approve
ocw evidence add
ocw rule add
ocw rule suspend
ocw rule resume
ocw rule remove
ocw verify
ocw review
ocw round close
ocw migrate detect
ocw migrate lean --dry-run
ocw migrate lean --confirm
ocw hygiene
ocw hygiene --cleanup --dry-run
ocw hygiene --cleanup --confirm
ocw uninstall --dry-run
ocw uninstall --confirm
```

兼容要求：

- `open-cowork` 可作为 `ocw` alias。
- 旧命令若能映射到 compact model，应映射到同一实现入口。
- 旧命令若需要创建 legacy heavy directories，必须失败并给出迁移指导。

统一失败提示：

```text
This command would create the legacy heavy governance layout. Use the v0.3.11 lean command or pass --legacy-layout intentionally.
```

## 6. 旧命令兼容矩阵

| 旧能力 | v0.3.11 映射 | 默认允许 | `--legacy-layout` | 说明 |
| --- | --- | --- | --- | --- |
| init / activation | `ocw init` / `ocw resume` | 是 | 否 | 创建或读取 compact layout |
| change prepare | `ocw round start` | 是 | 否 | 写 active_round，不创建 `changes/` |
| contract | `ocw round participants init` + `ocw round approve` | 是 | 否 | 写 role bindings、execution gate |
| evidence write | `ocw evidence add` | 是 | 否 | 写 `evidence.yaml` |
| runtime event | `ledger.yaml` compact event 或 `state.yaml` 摘要 | 部分 | 否 | 长事件不进入默认读取集 |
| index rebuild | `ocw status` / `ocw hygiene` | 部分 | 否 | 不创建 `index/` |
| verify | `ocw verify` | 是 | 否 | 写 compact verify summary |
| review | `ocw review` | 是 | 否 | 写 compact review decision |
| archive | `ocw round close` | 是 | 否 | 追加 ledger record，不创建 `archive/` |
| legacy archive inspect | `ocw migrate detect` / cold read | 否 | 可选 | 只读或迁移，不作为正常模型 |

## 7. 旧版本识别、迁移、清理、卸载

### 7.1 detect report

`ocw migrate detect` 必须识别：

- 当前 Python package / CLI 版本。
- 项目内协议版本。
- 是否存在 `.governance/changes/**`。
- 是否存在 `.governance/archive/**`。
- 是否存在 `.governance/runtime/**`。
- 是否存在 `.governance/index/**`。
- 是否存在 `.governance/local/**`。
- 是否存在 active legacy change。
- 是否存在未迁移 archive。
- 是否存在 git-tracked legacy runtime artifacts。
- 是否存在已部分迁移的 mixed layout。

### 7.2 migration

`ocw migrate lean --dry-run` 只报告计划，不写破坏性变更。

`ocw migrate lean --confirm` 必须：

- 创建默认 compact layout。
- 从旧 active state 提取当前 round。
- 将旧 manifest、contract、verify、review、evidence index 转换为 compact active round。
- 将旧 archive receipts 转换为 ledger compact records。
- 将旧运行目录移动到 `.governance/cold/legacy/` 或标记为 cleanup candidate。
- 更新 `.gitignore`，避免 legacy runtime/cache 进入普通上下文。
- 生成 migration receipt。
- 不把旧目录完整复制进 active model。
- 如果 compact active state 与 legacy active change 同时存在，且两者摘要、scope、approval 或 review 状态不一致，迁移必须阻断并请求人/团队裁决；不得自动合并或猜测哪一份更权威。

### 7.3 cleanup

`ocw hygiene --cleanup --dry-run` 必须列出：

- 将删除的路径。
- 将移动的路径。
- 将保留的路径。
- git-tracked 文件。
- 需要人确认的风险。

`ocw hygiene --cleanup --confirm` 必须：

- 不删除项目源代码。
- 不删除未迁移 active state。
- 不删除被人/团队标记保留的 cold artifacts。
- 对 git-tracked legacy files 要求额外确认。
- 生成 cleanup receipt。

### 7.4 uninstall

`ocw uninstall --dry-run` 只报告将移除的 open-cowork 文件。

`ocw uninstall --confirm` 必须：

- 只移除 open-cowork governance files。
- 不删除项目代码。
- 不删除外部 evidence artifact。
- 生成 uninstall receipt。

未来类似机制变更沿用：

```text
识别 -> dry-run -> 迁移 -> 验证 -> 清理 receipt
```

## 8. 文件级实施计划

新增文件：

- `src/governance/lean_paths.py`
- `src/governance/lean_state.py`
- `src/governance/lean_render.py`
- `src/governance/lean_round.py`
- `src/governance/lean_rules.py`
- `src/governance/lean_migration.py`
- `src/governance/lean_archive.py`
- `tests/test_v0311_lean_state.py`
- `tests/test_v0311_gates.py`
- `tests/test_v0311_migration.py`
- `tests/test_v0311_pressure.py`

修改文件：

- `src/governance/cli.py`
- `src/governance/hygiene.py`
- `src/governance/activation.py`
- `src/governance/preflight.py`
- `src/governance/evidence.py`
- `src/governance/review.py`
- `src/governance/verify.py`
- `src/governance/participants.py`
- `src/governance/change_package.py`
- `src/governance/runtime_events.py`
- `src/governance/index.py`
- `src/governance/archive.py`
- `src/governance/status_views.py`
- `src/governance/continuity.py`
- `docs/README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/agent-playbook.md`
- `docs/glossary.md`
- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`

当前注意：

- `.governance/AGENTS.md` 和 `.governance/agent-playbook.md` 已有未提交本地修改。
- 实施阶段可以先不碰它们，但发布前必须完成 dogfood/update；否则是 release blocker。

## 9. 任务拆分

### 任务 1：精简路径、默认读取集与 legacy 分类

实现：

- `LEAN_LAYOUT_FILES` 包含 `AGENTS.md`、`agent-entry.md`、`agent-playbook.md`、`state.yaml`、`current-state.md`、`ledger.yaml`、`evidence.yaml`、`rules.yaml`。
- `LEAN_LAYOUT_DIRS` 包含 `templates/`。
- `DEFAULT_READ_SET` 包含 `AGENTS.md`、`agent-entry.md`、`current-state.md`、`state.yaml`。
- `LEGACY_HEAVY_DIRS` 包含 `changes`、`archive`、`runtime`、`index`、`local`。

测试：

```python
def test_default_read_set_matches_v0311_spec(tmp_path):
    paths = default_read_set_paths(tmp_path)
    assert [path.name for path in paths] == [
        "AGENTS.md",
        "agent-entry.md",
        "current-state.md",
        "state.yaml",
    ]
```

验证：

```bash
pytest tests/test_v0311_lean_state.py -q
```

### 任务 2：精简状态初始化与 `current-state.md` 渲染

实现：

- `ocw init` 创建默认布局。
- 初始化 `state.yaml` 最小权威 schema。
- 通过 schema validation 校验 `state.yaml`、`rules.yaml`、`evidence.yaml`、`ledger.yaml`，并复用统一枚举定义。
- 初始化空 `ledger.yaml`、`evidence.yaml`、`rules.yaml`。
- 创建 `agent-entry.md` 和 `templates/`。
- 渲染 `current-state.md`。

测试：

- 初始化后默认布局完整。
- 不创建 legacy heavy dirs。
- `current-state.md` 少于 200 行。
- `state.yaml` 少于 400 行。

验证：

```bash
pytest tests/test_v0311_lean_state.py -q
python -m governance.cli init
python -m governance.cli status
```

### 任务 3：协作者初始化与角色绑定

实现：

- `ocw round participants init` 写入 sponsor、owner_agent、orchestrator、executor、reviewer、advisors。
- 记录权限边界、输出责任、review 独立性。
- `role_bindings` item 必须包含 role、actor、responsibility、authority_scope、output_responsibility、independence_requirement、evidence_ref。
- 计算 required、initialized、missing roles。
- 缺失必要角色时 `participant_initialization.status=blocked`。
- 单 Agent 场景也必须显式记录 owner agent 和 reviewer 策略。

测试：

- 缺 executor 阻断 execution gate。
- 缺 reviewer 阻断 execution gate。
- executor 与 reviewer 相同且无 bypass evidence 时阻断。
- human/team bypass 必须有 reason、approved_by、approved_at、approval_evidence_ref、impact_scope。

验证：

```bash
pytest tests/test_v0311_gates.py -q
```

### 任务 4：授权证据模型与 Gate

实现：

- `ocw round approve` 不接受单纯 `--by human:*` 作为充分授权。
- approval 必须记录 requested_by、approved_by、approval_source、approval_channel、approval_evidence_ref、created_by、created_at、reason。
- 无 evidence ref 时 gate 保持 pending/blocked。
- execution gate 和 closeout gate 分开记录。

测试：

- Agent 传 `--by human:mlabs` 但无 `approval_evidence_ref` 时不能批准。
- 有外部 evidence ref 时才能 approve。
- scope/done definition 变更也必须记录 approval evidence。

验证：

```bash
pytest tests/test_v0311_gates.py -q
```

### 任务 5：Round 状态机

实现：

- 持久化 phase 使用规格枚举。
- `round start` 创建 `intent-scope`。
- `round participants init` 和 plan 写入后进入 `plan-contract`。
- execution gate approve 后进入 `execute-evidence`。
- verify/review 后进入 `verify-review`。
- closeout gate approve 后进入 `closeout`。
- 同一份 `state.yaml` 输入在 CLI handler、preflight helper、status renderer 和测试 helper 中必须得到相同 gate decision。

测试：

- 未完成必要产出不能进入下一阶段。
- 未授权不能进入 `execute-evidence`。
- verify fail 不能进入 `closeout`。
- review revise/reject 不能进入 `closeout`。
- review status/decision 非法组合不能通过 schema validation。

验证：

```bash
pytest tests/test_v0311_gates.py tests/test_state_consistency.py -q
```

### 任务 6：有界 evidence 与 ledger

实现：

- `ocw evidence add` 只写 refs 和摘要。
- evidence 超过 1,000 条或 512 KB 时 hygiene 警告。
- `round close` 只向 `ledger.yaml` 追加 compact record。
- ledger 超过 500 条或 512 KB 时 hygiene 警告。

测试：

- evidence 不嵌入长输出。
- ledger 只追加 compact record。
- 超阈值触发 warning，不自动轮转。
- `resume/status/preflight` 不读取 ledger/evidence，除非按需。

验证：

```bash
pytest tests/test_v0311_lean_state.py tests/test_v0311_pressure.py -q
```

### 任务 7：外部规则生命周期

实现：

- `rule add` 记录适用阶段、失败影响、命令或检查方式、授权证据。
- `rule suspend` 记录 reason、期限、范围、授权证据。
- `rule resume` 记录 actor、reason、授权证据。
- `rule remove` 记录 reason、范围、授权证据。
- active round 中 blocking rule 变更必须有 human/team approval evidence。

测试：

- blocking rule 失败阻断 closeout。
- warning rule 失败只记录警告。
- advisory rule 失败只作为参考。
- active round 中暂停 blocking rule 无 evidence 时失败。

验证：

```bash
pytest tests/test_v0311_gates.py tests/test_run.py tests/test_cli.py -q
```

### 任务 8：Review 独立性与 closeout

实现：

- `ocw review` 写 compact review decision。
- executor 不能批准自己的最终 Review，除非有 human/team bypass evidence。
- `ocw round close` 必须检查 verify pass、review approve、closeout gate approve、closeout summary、carry-forward、ledger append。

测试：

- executor 自批失败。
- approve review 但无 closeout gate 仍失败。
- closeout 缺 summary 失败。
- closeout 成功后追加 ledger record，并重置 active state。

验证：

```bash
pytest tests/test_v0311_gates.py tests/test_retrospective.py tests/test_continuity.py -q
```

### 任务 9：旧版本 detect、migrate、cleanup、uninstall

实现：

- `migrate detect` 输出完整 detect report。
- `migrate lean --dry-run` 不写破坏性变更。
- `migrate lean --confirm` 转换 active change 和 archive receipts。
- `hygiene --cleanup --dry-run` 输出 cleanup plan。
- `hygiene --cleanup --confirm` 执行安全清理并写 cleanup receipt。
- `uninstall --dry-run` 输出 uninstall plan。
- `uninstall --confirm` 安全移除 open-cowork 文件并写 uninstall receipt。
- 更新 `.gitignore`。
- git-tracked legacy files 需要额外确认。

测试：

- active legacy change 转换为 active round。
- archive receipt 转换为 ledger record。
- dry-run 不删除文件。
- cleanup receipt 生成。
- uninstall receipt 生成。
- git-tracked legacy file 无额外确认时阻断。

验证：

```bash
pytest tests/test_v0311_migration.py -q
```

### 任务 10：旧命令 shim 与 legacy 目录回归守卫

实现：

- 旧命令默认映射到 compact model。
- 无法映射且会创建 legacy dirs 的旧命令失败。
- 增加测试 fixture：普通 round 执行中一旦创建 legacy heavy dirs 即失败。

测试：

- 默认完整 round 不创建 legacy dirs。
- compatibility migration 测试可以故意创建 legacy dirs。
- `--legacy-layout` 必须显式且有 warning。

验证：

```bash
pytest tests -q
```

### 任务 11：长周期、多 Agent、多项目压力测试

模拟：

- 一个项目、一个 Agent、100 轮。
- 一个项目、多个个人域 Agent、100 轮。
- 团队域 participants、独立 reviewer、外部 rules、100 轮。
- 多个项目，每个项目重复多轮。

断言：

- 默认读取集文件数量固定。
- 默认读取集总大小有界。
- `current-state.md < 200 行`。
- `state.yaml < 400 行`。
- 单轮生成文件数量接近常数。
- `resume/status/preflight` 不扫描 cold history。
- ledger/evidence 紧凑增长并触发 hygiene warning。
- 未授权 gate 不能推进。
- 缺协作者初始化不能执行。
- review 失败不能 closeout。
- 自动降级实现被识别为失败。
- 同一 `state.yaml` fixture 通过不同入口得到同一 gate decision。

验证：

```bash
pytest tests/test_v0311_pressure.py -q
```

### 任务 12：文档与 Agent-first 入口

必须更新：

- `README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/agent-playbook.md`
- `docs/glossary.md`
- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`

要求：

- 文档都是中文。
- 继续强调 Agent-first，不让人背 CLI。
- 把 lean protocol 描述为默认模型。
- 不再把 `.governance/changes/**`、`.governance/archive/**` 描述为正常模型。
- 解释旧版本如何识别、迁移、清理、卸载。
- 解释个人域单 Agent、个人域多 Agent、团队域多 Agent 示例。

当前约束：

- `.governance/AGENTS.md` 和 `.governance/agent-playbook.md` 已有本地修改，实施前要先确认是否纳入本轮变更。
- 若发布前无法更新 `.governance/*` 入口文件，则 v0.3.11 不得发布。

验证：

```bash
rg -n "V4|v4|4\\.0|auto.*downgrade|minimal implementation" docs src .governance
rg -n "\\.governance/(changes|archive|runtime|index|local)" docs .governance
```

第二条命令只允许迁移、兼容、废弃说明命中；验证脚本需按上下文过滤，避免把合法废弃说明误报为失败。

### 任务 13：open-cowork 自身 dogfood 迁移

目标：

- open-cowork 仓库自身在 v0.3.11 tag 前完成 lean self-dogfood。

步骤：

1. `ocw migrate detect`
2. `ocw migrate lean --dry-run`
3. 人确认迁移范围。
4. `ocw migrate lean --confirm`
5. `ocw hygiene --cleanup --dry-run`
6. 人确认清理范围。
7. `ocw hygiene --cleanup --confirm`
8. 运行完整验证。

验收：

- 默认读取集符合 v0.3.11。
- 旧重目录不再是 active model。
- migration receipt 和 cleanup receipt 存在。
- `.governance/AGENTS.md`、`.governance/agent-entry.md`、`.governance/agent-playbook.md` 已更新为 lean protocol。

### 任务 14：发布准备

发布前 gate：

- 方案与规格一致性复核通过。
- 第三方只读 Review 无阻断问题。
- `pytest tests -q` 通过。
- 长周期压力测试通过。
- 旧项目迁移测试通过。
- open-cowork 自身 dogfood 迁移完成。
- 文档更新完整。
- 人明确授权发布。

只有在人明确授权并确认实际发布分支后才能执行。下面命令是示例，不能机械套用远端分支名：

```bash
git tag v0.3.11
git push origin codex/main
git push origin v0.3.11
gh release create v0.3.11 --title "v0.3.11 Lean Protocol Reset" --notes-file <release-notes-file>
```

## 10. 端到端示例

### 10.1 个人域单 Agent

```text
人：请用 open-cowork 管理这个项目接下来的修改。
Agent：运行 ocw init/resume，读取默认读取集。
Agent：ocw round start，记录 intent-scope。
Agent：完成 owner_agent 和 reviewer 策略初始化。
人：批准计划和执行 gate。
Agent：ocw round approve，记录 approval evidence。
Agent：执行完整 scope，登记 evidence refs。
Agent：ocw verify，运行内置验证和规则。
Agent：请求独立 review 或 human bypass。
Agent：ocw round close，追加 ledger compact record。
```

### 10.2 个人域多 Agent

```text
Codex：owner_agent / orchestrator。
Hermes：reviewer。
OOSO：executor 或 advisor。
state.yaml：记录角色、权限边界、输出责任、review 独立性。
所有 Agent 通过同一个 state.yaml 判定 gate，不各自维护流程状态。
```

### 10.3 团队域多 Agent

```text
团队 sponsor 批准 scope。
owner_agent 维护 state.yaml。
executor 执行 scope in。
reviewer 独立审查。
team policy 以 rules.yaml blocking rule 表达。
closeout 必须有 team approval evidence。
```

## 11. 验收标准

代码验收：

- `pytest tests -q` 通过。
- 默认命令不创建 legacy heavy dirs。
- `resume/status/preflight` 不扫描 cold history。
- 100 轮压力测试后默认读取集数量固定、大小有界。
- ledger/evidence 超阈值只 warning，不自动重写历史。

机制验收：

- 未初始化协作者不能执行。
- 无外部 evidence 的 gate approval 不能推进。
- Agent 不能伪造 human/team approval。
- executor 不能批准自己的最终 Review。
- 未完成完整 scope 且无人/团队批准变更时不能 closeout。
- blocking external rule 失败不能 closeout。
- closeout gate 未批准不能关闭。
- 旧安装可 detect、dry-run migrate、confirm migrate、dry-run cleanup、confirm cleanup、dry-run uninstall、confirm uninstall。

文档验收：

- 所有新增产出文档为中文。
- 文档保持 Agent-first。
- 文档解释旧版本升级、清理、卸载。
- 文档解释如何避免长周期、多轮、多 Agent 导致治理状态膨胀。

发布验收：

- open-cowork 仓库自身完成 lean self-dogfood。
- 第三方 Review 无阻断问题。
- 人明确授权发布。

## 12. 当前工作区注意事项

- 当前已有未提交本地修改：
  - `.governance/AGENTS.md`
  - `.governance/agent-playbook.md`
- 当前新增文档：
  - `docs/superpowers/plans/2026-04-29-v0311-lean-protocol-reset.md`
  - `docs/superpowers/reviews/2026-04-29-v0311-lean-protocol-reset-review.md`
  - `docs/superpowers/reviews/2026-04-29-v0311-lean-protocol-reset-second-review.md`
  - `.agent-state/tasks/v0311-lean-plan-hermes-review/execution-contract.json`
  - `.agent-state/tasks/v0311-lean-plan-second-review/execution-contract.json`
- 本计划已完成二次 Review，未发现阻断问题；进入源码实现前仍需遵守第一批实现前置要求：先固化 schema、统一枚举、gate validation、role binding、bypass approval、review 状态组合、decision_needed 和跨入口一致性测试。

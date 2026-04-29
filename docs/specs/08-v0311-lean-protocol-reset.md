# v0.3.11 轻量协议重置

## 目标

v0.3.11 重置 open-cowork 的运行时模型，使一个项目即使在几十到上百轮闭环、数十到上百天周期、单 Agent 或多 Agent 协作下持续使用，也不会因为 open-cowork 自身的机制、流程和规范让项目越来越慢、越来越重，最终无法推进。

这是一次 breaking-level 的协议简化，但版本定义为 v0.3.11，不定义为 v4.0。原因是 open-cowork 仍处于正式大面积推广前的协议成熟阶段，本次目标是在 v0.3 系列内完成轻量化基础模型。

## 不可妥协的结果

1. 一个项目实施 open-cowork 100 轮后，默认 Agent 读取集仍然必须很小。
2. 当前治理状态的文件数量和文件大小必须有明确上限。
3. 单轮闭环不能在一个文件足以满足人、团队和 Agent 消费时生成目录树式中间产物。
4. 个人域单 Agent、个人域多 Agent、团队域多 Agent 必须共用同一套紧凑状态模型。
5. 历史记录默认必须是追加式摘要，不再复制整轮工作目录。
6. 大命令输出、日志、长 review 记录、session dump 和源资料必须以摘要、hash、路径或外部引用记录，不得嵌入默认治理上下文。
7. `resume`、`status`、`preflight` 和 review 入口不得扫描冷历史。
8. 不得出现“自动降级”“最小实现替代完整实现”“事后伪造授权”这类流程绕过。
9. 不同个人域、不同团队域、不同 Agent runtime 上执行 open-cowork 时，流程状态和 gate 判定必须一致；允许执行质量因 Agent 能力不同而不同，但不允许流程语义不同。

## 支持的实施场景

### A. 个人域单 Agent，一个或多个项目

open-cowork 必须帮助一个 Agent 在多个项目中保持接续能力，但不能把每个项目变成不断增长的治理档案库。Agent 默认只读取项目入口、紧凑状态和当前轮次摘要。旧轮次保留在紧凑 ledger 中，只有在人明确要求历史分析时才读取。

### B. 个人域多 Agent，一个或多个项目

open-cowork 必须让 Codex、Hermes、OMOC/OpenCode、Claude Code、Gemini 或其他个人域 Agent 围绕同一个紧凑状态协作。Agent 参与情况记录为当前轮次中的角色、职责、授权和 decision records，不再为每个 Agent 或每一步扩散文件目录。

### C. 团队域多 Agent，一个或多个项目

open-cowork 必须支持多个团队成员和多个 Agent 协同推进项目，同时保持项目状态轻量。团队协作通过 participants、role bindings、gates、review decisions、external rules 和 carry-forward records 表达。团队规模增加不得导致每一步生成物数量成倍增加。

## 新的治理目录结构

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

可选冷存储可以存在，但绝不属于默认读取集：

```text
.governance/cold/
  legacy/
  artifacts/
```

默认废弃：

```text
.governance/changes/
.governance/archive/
.governance/runtime/
.governance/index/
.governance/local/
```

这些旧目录可以被迁移、清理或作为冷历史保留，但 v0.3.11 的正常命令不得再创建它们。

## 文件职责

### `.governance/state.yaml`

唯一的机器权威当前状态文件。

它记录：

- 协议版本
- active round id
- 当前阶段
- gate 状态
- scope in / scope out
- owner、participants 和角色绑定
- 当前需要的人/团队决策
- 验证状态
- review 状态
- 外部规则状态
- carry-forward 摘要
- 有界 evidence refs

它不得包含完整命令输出、长 review transcript、长日志或复制的源文档。

### `.governance/current-state.md`

面向人、团队和 Agent 的短摘要，由 `state.yaml` 生成。

它应该能在一个屏幕内读完，包含：

- 当前目标
- 当前阶段
- owner 和关键参与者
- 是否阻塞
- 下一步决策
- 最新验证结果
- 最新 review 结果
- 外部规则状态
- carry-forward notes

这个文件允许重复 `state.yaml` 中的少量信息，因为它服务人类和通用 Agent 阅读；但它不是权威状态，必须可从 `state.yaml` 再生成。

### `.governance/ledger.yaml`

追加式紧凑轮次 ledger。

每轮只追加一条 compact round record：

- round id
- 起止时间
- 目标
- scope digest
- participants 摘要
- 最终状态
- 验证摘要
- review 摘要
- external rules 摘要
- evidence refs
- closeout 摘要
- carry-forward item

ledger 是历史事实索引，不保存每轮完整工作文件。

### `.governance/evidence.yaml`

有界证据索引。

每条 evidence item 包含：

- evidence id
- round id
- kind
- path 或 external ref
- 短摘要
- 可选 hash
- created by
- created at

大型证据保留在自然位置：构建日志、CI 输出、截图、测试报告、本地 session recovery 文件或外部系统。open-cowork 只记录引用和摘要。

### `.governance/rules.yaml`

项目级外部规则注册表。

它记录团队或个人加入的额外规则，例如：

- review lint
- security lint
- style checks
- CI policy
- architecture review
- legal / compliance review
- team-specific done definition

规则必须支持友好地加入、暂停、恢复和取消。规则变更本身需要记录 actor、reason、time 和适用范围。规则不得通过隐式默认值偷偷改变当前 active round 的验收标准；已经启动的 round 如需新增或取消规则，必须记录 human/team approval。

## 轮次模型

v0.3.11 用一个紧凑 round object 取代文件繁重的 change package。

必需字段：

```yaml
round_id: R-20260429-001
goal: "面向人的简短目标"
phase: intent-scope|plan-contract|execute-evidence|verify-review|closeout
scope:
  in: []
  out: []
participants:
  sponsor: human
  owner_agent: agent
  orchestrator: agent
  executor: agent
  reviewer: agent-or-human
participant_initialization:
  status: pending|complete|blocked
  required_roles: []
  initialized_roles: []
  missing_roles: []
gates:
  execution: pending|approved|blocked
  closeout: pending|approved|blocked
external_rules:
  active: []
  suspended: []
evidence_refs: []
verify:
  status: not-run|pass|fail|blocked
  summary: ""
review:
  status: not-requested|approve|revise|reject
  reviewer: ""
implementation_commitment:
  mode: full-scope
  downgrade_allowed: false
closeout:
  status: open|closed
  summary: ""
carry_forward: []
```

CLI 可以把 active round 序列化在 `state.yaml` 中，并在 round 关闭时把 compact copy 追加到 `ledger.yaml`。

## 流程简化

旧的九步流程压缩为五个对人和团队更友好的阶段。阶段减少不代表约束减弱；每个阶段都必须有清晰边界、明确产出物和质量要求。

### 1. 意图与范围

目的：确认人/团队真正要完成什么，哪些内容在本轮内，哪些不在本轮内。

边界：

- 不修改项目代码。
- 不进入执行。
- 不自行把完整需求降级为局部需求。

产出物：

- `state.yaml` 中的 `goal`
- `scope.in`
- `scope.out`
- 初始验收标准摘要
- 当前 round id

质量要求：

- 目标必须是人能读懂的一句话或短段落。
- scope in/out 必须能被 Agent 用来判断是否越界。
- 已确认需求不得被 Agent 自行缩小。

### 2. 计划与契约

目的：把本轮目标变成可执行计划、执行边界、角色绑定和验证方式。

边界：

- 没有人/团队授权，不进入实现。
- 没有完成 participant initialization，不进入实现。
- 没有明确验证方式，不进入实现。

产出物：

- `state.yaml` 中的 compact plan
- role bindings
- participant initialization result
- execution gate
- verification plan
- active external rules

质量要求：

- plan 必须覆盖完整 scope in。
- executor、reviewer、owner agent 等角色必须明确。
- reviewer 与 executor 的职责必须分离，除非人/团队明确记录 bypass。
- execution gate 未批准时不能推进到执行。

### 3. 执行与证据

目的：按照已批准计划执行，并记录足够但有界的证据。

边界：

- 只能在 scope in 内修改。
- 不能自动改为“最小实现”。
- 遇到无法完整实现的情况必须回到人/团队决策，而不是自行降级。

产出物：

- 项目代码或文档变更
- `evidence.yaml` 中的 evidence refs
- `state.yaml` 中的执行摘要
- 如有阻塞，记录 blocker 和所需决策

质量要求：

- evidence ref 必须能让 reviewer 找到关键证据。
- 长日志只记录摘要和路径。
- 执行结果必须对应 plan 和 scope，不得用“命令成功”替代实际完成度说明。

### 4. 验证与审查

目的：验证产物是否满足契约，并记录独立审查结论。

边界：

- 验证失败不能进入 closeout。
- review 要求 revise/reject 时不能 archive 或 closeout。
- executor 不能批准自己的最终 review，除非有明确的 human/team bypass 记录。

产出物：

- `state.yaml` 中的 verify summary
- `state.yaml` 中的 review decision
- `evidence.yaml` 中的验证证据引用
- external rules 的执行结果

质量要求：

- verify summary 必须说明运行了什么、结果是什么、失败时失败在哪里。
- review decision 必须明确 approve/revise/reject。
- 外部规则失败必须阻断，除非人/团队明确授权绕过并记录 reason。

### 5. 收束与接续

目的：关闭本轮，留下下一轮可恢复状态。

边界：

- closeout gate 未批准不能关闭。
- 未完成 verify/review 不能关闭。
- 不能复制整轮工作目录作为默认 archive。

产出物：

- `ledger.yaml` 中的一条 compact round record
- 更新后的 `state.yaml`
- 更新后的 `current-state.md`
- carry-forward items

质量要求：

- closeout 摘要必须说明完成了什么、没有完成什么、剩余风险和下一步。
- ledger record 必须足够支持历史追溯，但不能包含长日志或大文本。
- 默认接续入口必须保持短小。

## 强约束规则

1. 未经人/团队明确授权，不得推进 execution gate 或 closeout gate。
2. 未完成阶段规定产出物，不得进入下一阶段。
3. 不得伪造、模拟或事后补写授权来掩盖流程绕过。
4. 不得把未完成事项描述成已完成。
5. 不得自行把 scope in 改成更小范围。
6. 不得把完整实现替换成“最小实现”“临时实现”“后续再补”，除非人/团队明确批准变更 scope 或 done definition。
7. 不同 Agent runtime 必须通过同一个 `state.yaml` 读取和写入流程状态，不能各自维护一套互相冲突的流程判断。

## 协作者初始化

任何多 Agent 或团队场景都必须完成协作者初始化。单 Agent 场景也必须显式记录 owner agent 和 reviewer 策略。

初始化至少记录：

- sponsor
- owner agent
- orchestrator
- executor
- reviewer
- optional advisors
- 每个角色的权限边界
- 每个角色的输出责任
- review 独立性要求
- 缺失角色和阻断状态

如果缺少必要角色，`participant_initialization.status` 必须是 `blocked`，流程不得进入执行。允许人/团队用显式授权降低角色要求，但必须记录 reason、approved_by、approved_at 和影响范围。

## 外部规则机制

open-cowork 必须支持人/团队在流程中加入、暂停、恢复或取消外部规则。

规则操作要求：

- `rule add`：加入规则，记录名称、类型、适用阶段、命令或检查方式、失败影响。
- `rule suspend`：暂停规则，记录原因和期限。
- `rule resume`：恢复规则，记录 actor 和 reason。
- `rule remove`：取消规则，记录原因和适用范围。

规则类型包括但不限于：

- review lint
- test lint
- security check
- architecture check
- documentation check
- release checklist
- team policy

规则的失败影响必须明确：

- `blocking`：失败即阻断。
- `warning`：失败记录警告，但不阻断。
- `advisory`：只作为审查参考。

已经启动的 active round 中新增、暂停或取消 blocking rule，必须经过人/团队授权。

## 默认读取集

Agent 进入已实施项目时默认只读取：

```text
.governance/AGENTS.md
.governance/agent-entry.md
.governance/current-state.md
.governance/state.yaml
```

按需读取：

```text
.governance/ledger.yaml
.governance/evidence.yaml
.governance/rules.yaml
```

冷历史永远不默认读取。

## 上下文预算规则

1. `current-state.md` 目标少于 200 行。
2. `state.yaml` 目标少于 400 行。
3. `ledger.yaml` 保留 compact round records，并支持显式轮转。
4. `evidence.yaml` 只记录摘要和引用。
5. `rules.yaml` 只记录规则定义和状态，不记录长输出。
6. 会产生大量输出的命令必须把 artifact 写到默认读取集之外，并登记短 evidence ref。
7. `resume`、`status`、`preflight` 和 review 入口不得扫描冷历史。

## 旧版本识别、卸载、迁移和清理

v0.3.11 必须考虑已经安装旧版本 open-cowork 的环境，以及未来类似大机制变更时的升级路径。

### 旧版本识别

新增或增强诊断能力：

- 识别当前项目是否有旧版 `.governance/changes/**`、`.governance/archive/**`、`.governance/runtime/**`、`.governance/index/**`、`.governance/local/**`。
- 识别当前 Python package / CLI 版本。
- 识别项目内协议版本。
- 识别是否存在 active legacy change。
- 识别是否存在未迁移 archive。
- 识别是否存在被 git 跟踪的旧运行时产物。

### 升级与迁移

v0.3.11 的安装、初始化、setup 和 onboard 入口必须自动检测旧 heavy layout、旧 lean protocol version 和迁移需求。人/团队的默认入口仍是自然语言交给 Agent；Agent 不应要求人额外理解或执行迁移命令。

v0.3.11 同时提供 Agent 内部使用的显式迁移命令，用于排障、dry-run 或受控恢复，例如：

```text
ocw migrate lean
```

迁移必须：

1. 读取可用的当前 active state。
2. 创建 `state.yaml`、`current-state.md`、`ledger.yaml`、`evidence.yaml` 和 `rules.yaml`。
3. 把旧 archive receipts 转换为 compact ledger records。
4. 把旧 active change 的 manifest、contract、verify、review 和 evidence index 转换为当前 round。
5. 把旧运行目录移动到 `.governance/cold/legacy/` 或标记为可清理。
6. 更新 `.gitignore`，避免旧 runtime/cache 进入普通上下文。
7. 生成迁移摘要，说明迁移了什么、保留了什么、建议清理什么。

迁移必须保留审计可追溯性，但不得把旧目录完整复制进新的 active model。

### 卸载与清理

v0.3.11 应支持清理功能，但必须安全、可预览、可确认。

建议命令：

```text
ocw uninstall --dry-run
ocw uninstall --confirm
ocw hygiene --cleanup --dry-run
ocw hygiene --cleanup --confirm
```

清理策略：

- 默认先 dry-run，列出将删除、移动或保留的路径。
- 不删除项目源代码。
- 不删除未迁移的 active state。
- 不删除被人/团队标记为保留的 cold artifacts。
- 对 git-tracked 文件必须提示并要求明确确认。
- 清理完成后生成 cleanup receipt。

未来出现类似大机制变更时，默认安装实施入口必须沿用“自动识别 -> 自动升级/迁移 -> 验证 -> 失败即停止”的升级模式；清理和卸载仍沿用“dry-run -> 显式确认 -> receipt”的破坏性动作模式。

## 命令方向

CLI 仍然是 Agent 内部工具，不是要求人记忆的主界面。

推荐命令模型：

- `ocw init` / `ocw setup` / `ocw onboard`：创建或升级紧凑布局，自动迁移旧 heavy layout 并验证。
- `ocw resume`：只读取紧凑默认读取集。
- `ocw round start`：在 `state.yaml` 创建或替换 active round。
- `ocw round participants init`：初始化 owner、executor、reviewer 和协作者边界。
- `ocw round approve`：记录 human/team gate approval。
- `ocw rule add|suspend|resume|remove`：管理外部规则。
- `ocw evidence add`：向 `evidence.yaml` 追加有界 evidence ref。
- `ocw verify`：更新 compact verify summary。
- `ocw review`：更新 compact review decision。
- `ocw round close`：追加一条 compact ledger record，并重置 active state。
- `ocw migrate lean`：显式把旧治理树转换为 v0.3.11 compact state，主要供 Agent 排障、dry-run 或受控恢复使用。
- `ocw hygiene`：报告文件数量、大小、默认读取集大小、冷历史和清理候选。
- `ocw uninstall`：预览并执行安全卸载/清理。

旧命令可以在一个 release 内作为兼容 alias 保留，但正常文档和生成的 Agent 入口必须指向 lean commands。旧命令如果需要创建 `changes/`、`archive/`、`runtime/`、`index/` 或 `local/`，必须失败并给出迁移指导，不能静默重建旧模型。

## 测试策略

v0.3.11 必须新增防膨胀测试和流程一致性测试。

### 单元测试

- `init/setup/onboard` 只创建或升级紧凑默认布局；遇到旧 heavy layout 时自动迁移、写 receipt 并验证，验证失败必须返回失败。
- `round start` 只更新 `state.yaml` 和 `current-state.md`。
- `round participants init` 在缺少必要角色时阻断执行。
- `round approve` 只在明确 actor 和 gate 下写入授权。
- `rule add|suspend|resume|remove` 正确更新 `rules.yaml`，并要求 active round 中的 blocking rule 变更有授权。
- `evidence add` 只追加有界引用，不嵌入长输出。
- `round close` 只追加一条 compact ledger record。
- `resume` 使用紧凑默认读取集。
- `migrate lean` 能转换代表性旧项目且不丢失关键摘要。
- `uninstall --dry-run` 不删除文件，只输出计划。
- `hygiene --cleanup --dry-run` 能识别可清理旧产物。

### 长周期压力测试

模拟：

- 一个项目、一个 Agent、100 轮。
- 一个项目、多个 Agent、100 轮。
- 多个项目，每个项目重复多轮。
- 团队式 participants 和独立 reviewer。
- 外部规则在不同阶段加入、暂停、恢复和取消。

断言：

- 默认读取集文件数量保持固定。
- 默认读取集总大小保持有界。
- 单轮生成文件数量接近常数。
- `resume/status/preflight` 不扫描冷历史。
- ledger 和 evidence 增长是紧凑且可轮转的。
- 未授权 gate 不能推进。
- 缺少协作者初始化不能执行。
- review 失败不能 closeout。
- 自动降级实现会被测试识别为失败。

### 回归守卫

普通 round 执行如果创建以下 legacy 目录，测试必须失败：

```text
.governance/changes/
.governance/archive/
.governance/runtime/
.governance/index/
.governance/local/
```

只有 compatibility migration 测试可以故意创建这些目录。

## 文档更新

需要更新：

- `README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/agent-playbook.md`
- `docs/glossary.md`
- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`

文档必须说明 open-cowork 是 Agent-first 且默认轻量。文档不得继续把 `.governance/changes/**` 和 `.governance/archive/**` 描述为正常操作模型。

## 发布验收标准

v0.3.11 满足以下条件才可以发布：

1. 新项目初始化为 lean layout。
2. `resume` 只读取 compact default read set。
3. 一个完整 round 可以完成意图与范围、计划与契约、执行与证据、验证与审查、收束与接续，且不创建 legacy runtime trees。
4. 未授权 gate 不能推进。
5. 未完成协作者初始化不能执行。
6. 未完成完整 scope 且无人/团队批准变更时不能 closeout。
7. 外部 blocking rule 失败不能 closeout，除非有明确 bypass。
8. 旧项目迁移能生成 compact state 和 ledger records。
9. 旧版本识别、dry-run 清理、迁移 receipt 和 cleanup receipt 可用。
10. 长周期压力测试通过。
11. v0.3.10 项目有清晰迁移路径。
12. 文档把 lean protocol 描述为默认模型。
13. open-cowork 仓库自身在发布前完成 lean self-dogfood 迁移。

## 实施决策

v0.3.11 固定以下实施决策：

1. `ledger.yaml` 是默认 ledger 文件。`ocw hygiene` 在超过 500 条 compact round records 或 512 KB 时警告。自动轮转只能通过显式 `ocw hygiene --rotate-ledger` 执行，避免 Agent 在正常工作中突然改写历史结构。
2. `evidence.yaml` 是默认 evidence index。`ocw hygiene` 在超过 1,000 条 refs 或 512 KB 时警告。大型证据始终放在默认读取集之外，只记录摘要和引用。
3. `rules.yaml` 是默认外部规则注册表。active round 中 blocking rule 的新增、暂停或取消必须有授权记录。
4. 正常 v0.3.11 命令不得创建 legacy directories。兼容 shim 可以为迁移读取 legacy directories，也可以在旧命令被使用时警告。
5. 旧命令名可以在一个 release 内作为 alias 保留，前提是能映射到新的 round model。如果旧命令需要创建 `changes/`、`archive/`、`runtime/`、`index/` 或 `local/`，必须失败并给出迁移指导。
6. `current-state.md` 从 `state.yaml` 生成，手工编辑不具备权威性。
7. open-cowork 仓库必须在 v0.3.11 tag 前 dogfood lean layout。

# V0.2.5 Agent-first Dogfood 发现与迭代需求

日期：2026-04-24
目标项目：open-cowork 本仓库
模拟角色：新的团队成员个人域 Agent
模拟意图：在当前 open-cowork 项目迭代中实施 open-cowork 框架规范和流程，并记录所有 open-cowork 相关问题作为后续迭代需求。

## 1. 本次模拟过程

1. 新 Agent 先读取仓库级 `AGENTS.md`、`README.md`、`docs/getting-started.md`。
2. 执行 `./bin/ocw version`，确认当前版本是 `0.2.5`。
3. 执行 `./bin/ocw --root . status`，发现当前 `.governance/` active change 仍停留在旧的 `v0.2.3-onboarding-setup` draft。
4. 执行 `./bin/ocw onboard --target . --mode quickstart --yes`，观察已有项目的 onboarding 行为。
5. 执行 `./bin/ocw pilot --target . --change-id dogfood-v025-agent-first ... --yes`，在当前项目中创建新的 dogfood change。
6. 读取生成的 `.governance/AGENTS.md`、`.governance/current-state.md`、`.governance/agent-playbook.md`、`contract.yaml`、`bindings.yaml`。
7. 尝试用 `ocw run` 记录本报告文件为 changed artifact，暴露 runtime 写边界与 contract scope 不一致问题。

## 2. 关键发现

### F-001：仓库自身运行态没有随 V0.2.5 迁移到 Agent-first

现象：

- 仓库已经发布 `v0.2.5`，根目录已有 `AGENTS.md`。
- 但 `.governance/` 仍指向旧的 `v0.2.3-onboarding-setup`，状态是 `drafting`。
- `.governance/AGENTS.md`、`.governance/current-state.md`、`.governance/agent-playbook.md` 在执行新的 `pilot` 前不存在。

影响：

- 新 Agent 按 Agent-first 入口进入后，会看到仓库级叙事与运行时事实冲突。
- 这会削弱 open-cowork 自身 dogfood 的可信度。

需求：

- 提供 `ocw migrate agent-pack` 或 `ocw onboard --refresh-agent-pack`，用于为已有 `.governance/` 项目补齐 Agent-first 文件。
- V0.2.x 发布后，open-cowork 本仓库自身应始终保持 `.governance/` 与当前版本叙事一致。

优先级：P0

### F-002：已有 active change 未关闭时，pilot 会静默切换 active change

现象：

- 运行 `ocw status` 时，active change 是 `v0.2.3-onboarding-setup`，状态 `drafting`。
- 执行 `ocw pilot --change-id dogfood-v025-agent-first` 后，current change 被直接切换到新 change。
- 旧 change 仍留在 `changes-index.yaml` 中，状态仍是 `drafting`，没有 abandonment、superseded、closed 或 carry-forward 标记。

影响：

- Agent 可以继续往前走，但治理事实留下悬挂 change。
- 后续 continuity、archive、status、digest 容易混淆“旧 draft 是被废弃、被替代，还是仍待处理”。

需求：

- `pilot` / `change prepare` 在发现已有 active change 未归档时，应明确提示并要求一种策略：continue / supersede / abandon / archive-first。
- 提供机器可读的 stale active change 处理原语，例如 `ocw change supersede`、`ocw change abandon`。
- `status` 应把 stale / superseded / abandoned 与普通 draft 区分开。

优先级：P0

### F-003：onboard 仍然输出 CLI-first 下一步命令，且建议了不存在的默认 change-id

现象：

- `ocw onboard --target . --mode quickstart --yes` 成功后输出：`Next commands you can run`。
- 其中包括 `continuity digest --change-id personal-demo`，但当前项目并没有 `personal-demo`。

影响：

- 与 V0.2.5 Agent-first 原则冲突。
- 容易让新 Agent 或人误以为还需要复制执行命令。
- 建议不存在的 `change-id` 会直接造成下一步失败或困惑。

需求：

- `onboard` 输出应改为 Agent-first 状态摘要和下一步意图建议，而不是命令清单。
- 如果没有 active change，应建议“创建或准备一个 change”，但不要引用不存在的固定 `personal-demo`。
- 如果已有 active change，应基于真实 current change 输出下一步。

优先级：P1

### F-004：contract scope 与 runtime write boundary 不一致

现象：

- 本次 dogfood contract 的 `scope_in` 包含 `docs/**`。
- 尝试记录 `docs/archive/reports/2026-04-24-v025-agent-first-dogfood-findings.md` 为 `ocw run --modified` artifact 时失败：
  `ValueError: artifact 'docs/archive/reports/...' is outside the allowed write boundary`。
- 原因是 `cmd_run` 当前仍使用硬编码 `allowed_write_scope=[".governance/**", "src/**", "tests/**"]`，没有读取 contract 的 `scope_in`。

影响：

- Agent 按 contract 执行仍会被 runtime 拒绝。
- contract 不再是可信执行边界，破坏 open-cowork 的核心语义。
- 文档类 change、配置类 change、脚本类 change 都会遇到同类问题。

需求：

- `ocw run` 必须以 active contract 的 `scope_in` / `scope_out` 作为实际写边界。
- hard-coded fallback 只允许用于缺失 contract 的 draft 友好提示，不应覆盖 contract。
- 增加测试：contract 允许 `docs/**` 时，`ocw run --modified docs/x.md` 应通过。

优先级：P0

### F-005：contract validation 没有检测 scope_in 与 scope_out 重叠

现象：

- 本次 pilot 显式传入 `.governance/**` 到 `scope_in`。
- 生成的 contract 同时保留默认 `scope_out`：`.governance/index/**`、`.governance/archive/**`、`.governance/runtime/**`。
- `contract validate` 仍然通过。

影响：

- Agent 不知道 scope_in 与 scope_out 冲突时哪个优先。
- runtime 行为可能与 contract 阅读结果不一致。

需求：

- contract validation 应检测 scope_in / scope_out 的包含关系和重叠关系。
- 如果允许“scope_out 优先”，必须在 validation 输出和 generated contract 中显式说明。
- `change prepare` 应避免生成明显自相矛盾的 scope。

优先级：P0

### F-006：生成的 current-state.md 是一次性快照，后续状态变化不会自动更新

现象：

- `pilot` 生成 `.governance/current-state.md`，显示 Step 5。
- 但后续 `contract validate`、`run`、`verify`、`review`、`archive` 并未在文档中声明会自动刷新 current-state。

影响：

- 后续 Agent 可能读取过期的 `current-state.md`。
- V0.2.5 将该文件作为 Agent-first handoff 核心入口，如果不自动刷新，会形成新的漂移点。

需求：

- 在每个状态变更命令后刷新 `.governance/current-state.md`。
- 或将其改为由 `runtime-status` 生成的投影，并在文件中标注生成时间、来源和刷新命令。
- 增加 stale current-state 检测。

优先级：P1

### F-007：人类汇报模板仍中英混排且字段偏抽象

现象：

- `.governance/agent-playbook.md` 中标题为 `Human update template`，字段为 `Project goal / Current phase / Current step` 等英文。
- 对中文团队成员来说，第一次打开仍有工具感。

影响：

- 与“后续文档中文输出”和降低心智负担的方向不完全一致。
- Agent 可能照抄英文模板，而不是输出自然中文项目汇报。

需求：

- 生成的目标项目 playbook 默认中文字段。
- 可保留英文锚点，但面向人的默认模板应是中文。
- 支持 profile / locale，例如 `--locale zh-CN`。

优先级：P2

### F-008：Agent-first 采用流程缺少“一句话后 Agent 如何补全参数”的自动推导层

现象：

- 文档告诉人可以说一句话。
- 但底层 `pilot` 仍需要 `change-id`、`title`、`goal`、`scope-in`、`verify-command`。
- 当前 Agent 必须自己推导这些参数，缺少框架提供的 discovery / infer / confirm 支持。

影响：

- 不同 Agent 会各自发明参数推导逻辑。
- 体验质量依赖 Agent 自身能力，而不是 open-cowork 框架能力。

需求：

- 提供 `ocw adopt` 或 `ocw apply`：输入自然语言目标和 target，自动扫描项目类型、建议 scope、推导 verify command、生成候选 change-id，并输出人类确认摘要。
- 支持 `--dry-run` 输出 adoption plan。
- 支持 Agent 使用的 JSON 输出格式。

优先级：P0

### F-009：diagnose-session 能发现上下文预算问题，但没有和 Agent-first 入口联动

现象：

- `onboard` 会运行 `diagnose-session` 并提示 full scan 约 272k tokens，推荐 read set 约 396 tokens。
- 但 `.governance/AGENTS.md` / current-state 没有自动纳入或强调 recommended read set。

影响：

- Agent-first 入口仍可能让 Agent 读过多文件。
- session 压缩和 provider drop 风险没有被前置约束。

需求：

- Agent handoff pack 应包含 recommended read set 或指向 session diagnosis。
- `.governance/AGENTS.md` 应明确“先读最小集合，不要全仓扫描”。
- 对超预算项目，`pilot` 输出应强提醒 bounded context。

优先级：P1

## 3. 建议形成的后续迭代主题

### Theme A：Agent-first 采用闭环补齐

目标：让人一句话后，Agent 能用 open-cowork 完成 target discovery、change 参数推导、scope 建议、verify command 探测、handoff pack 生成和人类确认摘要。

包含需求：F-001、F-003、F-008、F-009。

### Theme B：治理状态一致性与旧 change 生命周期

目标：避免 active change 静默漂移，给 supersede / abandon / stale / archive-first 等状态提供明确语义。

包含需求：F-002、F-006。

### Theme C：contract 即真实执行边界

目标：确保 contract validation、runtime write boundary、run evidence、scope_in/out 语义完全一致。

包含需求：F-004、F-005。

### Theme D：中文团队试用体验打磨

目标：把面向人的默认输出和生成文档改成自然中文，保留机器锚点但不让人读起来像命令手册。

包含需求：F-007。

## 4. 建议优先级

P0：F-001、F-002、F-004、F-005、F-008

P1：F-003、F-006、F-009

P2：F-007

## 5. 本次 dogfood 结论

V0.2.5 已经把入口叙事从 CLI-first 推向 Agent-first，但当前实现仍处于“Agent-first 文档入口 + CLI 主链工具”的中间态。真正的下一步不是继续暴露更多命令，而是补齐 Agent 采用壳、运行态迁移、状态一致性和 contract/runtime 一致性。

最重要的一句话：open-cowork 必须让 Agent 相信 contract 是事实，让人相信 Agent 能一句话完成采用，而不是把人重新拖回命令行流程。

## 6. 追加发现

### F-010：手工 evidence 文件无法作为 run artifact 记录

现象：

- 将本报告复制到 `.governance/changes/dogfood-v025-agent-first/evidence/dogfood-findings.md` 后，尝试通过 `ocw run --modified .governance/changes/.../evidence/dogfood-findings.md` 记录 artifact。
- `ocw run` 返回：`ValueError: artifact '.governance/changes/.../evidence/dogfood-findings.md' touches a reserved governance boundary`。
- 去掉 `--modified` 后，`ocw run` 可以成功，但生成的 `changed-files-manifest.yaml` 中 `created/modified` 为空，无法表达本次实际写入的分析报告。

影响：

- 分析、审计、复盘、需求收集这类“文档即产物”的任务很难被 evidence 准确表达。
- Agent 只能把报告内容写进 command-output summary，而不是作为一等 artifact 被治理链路记录。

需求：

- 为 analysis/report 类型任务提供一等 evidence artifact 类型，例如 `--evidence-doc` 或 `ocw evidence add`。
- 允许当前 change 自身的 `evidence/**` 被记录为 evidence ref，但仍禁止修改 contract / bindings / manifest 等 truth source。
- `changed-files-manifest.yaml` 应能区分 application artifact、governance generated artifact、manual evidence artifact。

优先级：P1

### F-011：V0.2.5 生成的 `.governance/AGENTS.md/current-state.md/agent-playbook.md` 没有被 gitignore 覆盖

现象：

- `.gitignore` 忽略了 `.governance/index/`、`.governance/changes/`、`.governance/archive/`、`.governance/runtime/`。
- 但 V0.2.5 新增的 `.governance/AGENTS.md`、`.governance/current-state.md`、`.governance/agent-playbook.md` 不在忽略范围内。
- dogfood 后 `git status --short` 显示这些文件为 untracked。

影响：

- 团队成员试用后会看到仓库出现未跟踪文件，不知道是否应该提交。
- 与 `.governance/README.md` 中“运行时生成且默认不提交”的说明不一致。

需求：

- 明确 `.governance/AGENTS.md/current-state.md/agent-playbook.md` 是 runtime handoff artifacts 还是应提交的项目协作入口。
- 如果默认不提交，应更新 `.gitignore`。
- 如果推荐提交，应更新 `.governance/README.md` 和 onboarding 文档，说明哪些 `.governance` 根文件应提交、哪些不应提交。

优先级：P1

### F-012：status 的 human summary 与真实步骤状态不同步

现象：

- `ocw verify` 后 manifest 已到 `step7-verified`，`ocw status` 显示当前阶段是 Phase 3 / Step 7。
- 但 status 的 `project_summary` 仍是 `- [ ] Step 5: Confirm contract.yaml and bindings.yaml are acceptable.`。
- `.governance/current-state.md` 也仍停留在 Step 5。

影响：

- 人看 status 会同时看到 Step 7 和 Step 5，产生认知冲突。
- Agent 读取 current-state 会拿到过期下一步，可能重复执行或错误等待人确认。

需求：

- status 的 human summary 应基于当前 manifest/current step 动态生成。
- 每次状态变更后刷新 current-state，或在 status 输出中标记 current-state stale。
- verify 流程应检测 current-state 与 runtime/index 是否一致。

优先级：P0

### F-013：continuity digest 使用的 runtime projection 没有随 verify 刷新

现象：

- `ocw status` 在 verify 后显示当前阶段为 Phase 3 / Step 7。
- `ocw continuity digest --change-id dogfood-v025-agent-first` 仍显示 `status: step5-prepared / Phase 2 / 方案与准备`。
- digest 推荐读取 `.governance/runtime/status/change-status.yaml`，但该 projection 未自动刷新到最新状态。

影响：

- Handoff / digest 是 Agent 接续的重要入口，一旦落后于真实 manifest，会把下一个 Agent 带回旧阶段。
- 这会直接放大 session 压缩和 Agent 接力时的上下文漂移。

需求：

- 状态变更命令完成后应自动刷新 runtime status projection，或让 digest 在读取前强制 materialize 最新 projection。
- digest 输出应标注 projection 生成时间和来源状态。
- 增加测试：run/verify 后 digest 的 status 必须与 manifest/current-change 对齐。

优先级：P0

## 7. 最终优先级修订

P0：F-001、F-002、F-004、F-005、F-008、F-012、F-013

P1：F-003、F-006、F-009、F-010、F-011

P2：F-007

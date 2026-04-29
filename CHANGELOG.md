# 变更日志

## 0.3.11

- 将默认治理结构切换为 lean layout：新项目默认生成 `.governance/state.yaml`、`current-state.md`、`evidence.yaml`、`ledger.yaml` 和 `rules.yaml`，不再默认创建重型 runtime / change / archive 树。
- 增加 lean activation / resume / status 路径，新会话和跨 Agent 接续只读取紧凑权威状态，避免长周期、多轮次、多 Agent 项目被历史产物拖慢。
- 增加 lean round、participant initialization、gate approval、evidence、external rule 和 ledger closeout 命令，强约束协作者初始化、执行授权、独立 review、验证结果和 closeout approval。
- 增加旧项目检测、迁移、dry-run cleanup、migration receipt、cleanup receipt 和 uninstall 支持，为 v0.3.10 及更早安装环境提供可审计升级路径。
- 更新 Agent-first 文档、getting started、glossary 和 superpowers adoption 指引，将 CLI 降为 Agent 内部维护结构化协作事实的工具。
- 增加 v0.3.11 回归与压力测试，覆盖 lean schema、resume 读取集、gate 阻断、外部规则、迁移兼容、长周期状态增长和仓库自身 dogfood。

## 0.3.10

- 增加治理强约束层：`ocw audit` 检查 Step 1-9 required outputs、状态一致性、human gate reconciliation、writer metadata、canonical artifact digest、scope drift、flow bypass recovery 和 reviewer independence。
- 将 preflight、verify、review、archive 接入 gate-specific audit filtering，在缺少基线、必需产物、合法 human approval、执行 evidence 或独立 review 时阻断继续推进。
- 增加 Step Output Contract 与 canonical artifacts：Step 7/8 同步生成 `VERIFY_REPORT.md` / `REVIEW_REPORT.md` 与结构化 YAML，并用 `source_digest` 防止人类可读报告和机器事实漂移。
- 强化 Step 5 baseline binding、人类审批溯源、acknowledgement/approval 区分，以及未解决 bypass recovery 对 review/archive 的阻断。
- 增加规则源校验与 recovery 审计，支持内置规则包、项目 policy、change-local rules 和 skill adapter 声明的可审查加载。
- 更新 Agent-first 入口、v0.3.10 规格、governance playbook 和回归测试，覆盖审计命令、required output、canonical writer、防手写事实绕过、review/archive gate 与发布前清理验证。

## 0.3.9

- 增加 Team Operating Loop：`ocw team status` / `ocw team digest` 聚合 active changes、分派、阻塞、审查队列、周期性意图、carry-forward 和复盘资产。
- 增加团队参与者命令：`ocw participant discover/register/list/assign/update`，支持本地个人域 Agent 候选探测、远程团队成员 Agent 声明式登记和步骤参与者调整。
- 增加分派、阻塞和审查队列：`ocw assignment set`、`ocw blocked set/clear`、`ocw reviewer queue`，并阻断 reviewer 自审风险。
- 增加周期性意图与 carry-forward 候选池：`ocw recurring-intent add/trigger`、`ocw carry-forward list/add/promote`；触发和提升只创建 Step 1 草稿，不进入 Step 6。
- 增加团队复盘资产：`ocw retrospective add/list` 写入 `.governance/team/retrospectives/`，并被 team digest 引用。
- 增加执行前治理 guard：`ocw preflight check` 在已启用 open-cowork 的项目中校验 active change、contract、Step 5 批准、Step 6 readiness，并支持 `--path` 对待修改文件执行 `scope_in` / `scope_out` 范围校验。
- 增加绕过流程后的 recovery 记录：`ocw preflight recovery` 只能作为异常恢复路径，记录 bypass reason、已修改文件、缺失证据和恢复动作，不能伪装成正常 evidence。
- 收紧多 Agent 协作安全：Agent 登记参与者默认进入待人工审阅状态；reviewer 自审阻断会同时读取 team assignment 与 change package bindings 中既有 Step 6 executor / owner。
- 将 v0.3.9 规格、README、版本号和回归测试更新到完整实现状态，覆盖团队操作循环、参与者接入、执行前 guard、恢复路径、步骤边界和发布清理。

## 0.3.8

- 增加完整实现治理约束：需求、`scope_in`、任务完成定义和验收标准默认要求完整实现，未经人明确批准不得降级为最小实现、部分实现或延期实现；验证阶段会阻断未批准的未完成任务。
- 增加步骤报告时间字段 `started_at`、`completed_at`、`duration_seconds`，并在缺少历史时间源时使用 `unknown` / `not_recorded`。
- 增加归档后的 `FINAL_ROUND_REPORT.md`，从 intent、step reports、verify、review 和 archive receipt 聚合整轮闭环报告；归档收据和最终状态快照会引用最终报告、接手资料索引和接手摘要。
- 增加运行环境画像、运行事件接入、适配器输出校验、`evidence append --adapter` 和证据索引能力，使外部执行结果能以结构化 evidence input 进入证据链。
- 扩展通用终端 / 文件命令适配输出，记录运行环境、authority、执行时间、变更文件、命令、验证摘要、风险和后续事项。
- 审查报告现在可展示运行证据来源、authority 分级和运行事件冲突策略，明确运行事件不能替代治理权威事实。
- 补齐 v0.3.7 审计遗留项：接手资料最小 / 标准 / 深度真实分层、来源索引、分批阅读状态、压缩检查点、证据索引、安全应用预览、成员职责边界模板与接手摘要长度保护。
- 增加 v0.3.8 回归测试，覆盖报告耗时、最终闭环报告、运行证据适配、运行事件、证据索引、接手资料分层和完整实现门控。

## 0.3.7

- 增加 `ocw profile list/show/apply`，提供轻量协作、个人多 Agent 协作、团队标准协作和团队严格协作四种基础协作模式；大量资料阅读改为可叠加的 Agent 内部模式，而不是单独档位。
- 增加成员/Agent 职责边界目录 `.governance/participants/`，记录角色、权限、审查资格和工作边界，为“超级个体 -> 超级组织”协作提供最小成员事实面。
- 增加 `ocw context-pack create/read` 和 `ocw handoff --compact`，为 active change 生成接手资料索引和接手摘要；这些材料只指向权威事实，不替代 contract、intent、verify、review 等真相源。
- 将 project activation / resume 的内部建议读取顺序接入接手资料索引和接手摘要，使新会话优先读取最小权威材料，再按需深入。
- 补充 v0.3.7 回归测试和规格文档，锁定协作模式、成员职责边界、接手资料索引、接手摘要和接续读取顺序行为。

## 0.3.6

- 增加 `ocw resume` 确定性接续入口，作为新会话、跨 Agent、跨成员接手项目时的稳定触发点。
- 将 project activation 输出改为 `protocol_trigger: command`，并把 recommended read set 指向当前 change 的权威事实。
- 将可再生本地投影迁入 `.governance/local/**`，包括 current-state、PROJECT_ACTIVATION 和 runtime status，降低多人/多 Agent 合并冲突。
- 增加 `.governance/.gitignore` 默认规则，忽略 local projection、旧 root 投影和 runtime status。
- 增加 `ocw index rebuild`，可从 change manifest 和 archive receipt 重建 active changes、changes index 和 archive map。
- 生成的 Agent Entry / Playbook 去除单个 change id 绑定，改为要求先运行 `ocw resume` 并按返回的 recommended read set 接续。
- 修正 `ocw resume --list` 的副作用，list-only 模式不再写入本地 activation / current-state 投影；当 current pointer idle/stale 但只有一个 active change 时，resume 会确定性接续该 change。
- 补齐 xSearch v0.3.3 dogfood 反馈闭环：Step report 在 intent scope 为空时回退合并 contract scope / acceptance，并记录 `merged_from` 与 `fact_conflicts`，避免再次出现 `scope_in: none` 与执行事实不一致。
- Step 9 report 现在展示 archive preview 文件清单与 carry-forward 项；Step 8 report 可展示 reviewer invocation heartbeat、runtime 和 timeout policy。
- 新增 `ocw review-invocation`，用于记录长时间 reviewer 调度的 `started/running/completed/failed/timeout`、心跳、timeout policy 和 artifact ref。
- 更新 v0.3.6 回归覆盖，锁定 missing / idle / single / multi active changes 的 resume 行为、generic Agent Entry、index rebuild、facts merge、Step 9 archive preview 和 reviewer heartbeat。

## 0.3.5

- 完成 “Zero-Command Human Onboarding and Multi-Agent Project Activation”：README 和 getting-started 进一步下沉 CLI 细节，普通人不再需要记忆 open-cowork 命令。
- 增加项目级 `.governance/index/active-changes.yaml`，记录同一项目内多个未归档 change，支持并行需求场景。
- 增强 `ocw activate --change-id <change-id>`，任意 Agent / 新会话可显式接续指定 change；多个 active changes 时默认要求选择，不再从聊天历史猜测。
- 增加 `.governance/agent-entry.md` 生成与 `docs/agent-skill.md`，让 Codex、Claude Code、Hermes、OMOC 等进入目标项目后执行同一套激活、读取、汇报和边界规则；平台 Skill 仅作为可选适配层。
- README 和快速开始保留三类典型场景：个人域单一 Agent、本地个人域多 Agent、团队多人域协作，并说明项目级 Agent Entry 的触发方式。
- 补齐 human step report 的 `artifact_summary`、`review_gate_vs_decision` 展示，避免只在 Markdown 报告中有决策材料。
- 增加 v0.3.5 回归覆盖，锁定并行 active changes、显式 activation、Agent Entry 生成和人类文档 CLI 降噪。

## 0.3.4

- 将标准 9 步名称改为中文动作名 + 英文锚点，降低 Step 1-9 的理解成本。
- 增加 `activate` 项目级激活入口，输出 active change、当前步骤、推荐读取集和跨 Agent 接续指令，并落盘 `.governance/PROJECT_ACTIVATION.yaml`。
- 重写 README 的人类入口，明确人只需要对 Agent 说什么、CLI 是 Agent 内部工具，并加入流程图和最小操作面。
- 增加 `docs/glossary.md`、`docs/specs/README.md`，并收束 `docs/README.md` / `docs/archive/README.md` 的阅读分层，区分当前规格、Agent 执行面和历史证据。
- 基于 xSearch v0.3.3 dogfood 反馈继续收束 v0.3.4：Step report 统一投影 contract / intent 权威事实，Step 3/4/5 展示 design、tasks、scope、verification commands，避免 `scope_in: none` 造成报告与执行不一致。
- 修正 human gate 语义：`intent confirm` 自动满足 Step 1 approval；非 gate step 可记录 acknowledgement；Step 8 允许先记录 reviewer decision，再由人决定是否接受该 decision，archive 前仍强制 Step 8/9 human approval。
- 增加连续迭代 baseline separation：`change prepare` 写入 `baseline.yaml`，记录 parent archived change 和 dirty worktree，帮助 reviewer 区分历史归档基线、本轮增量和无关噪声。
- 扩展 `ocw verify`：默认明确记录 `state-only`，也可用 `--run-commands` 执行 contract verification commands 并写入 `product_verification`。
- 允许 `change prepare` 在缺少 `--goal` 时复用既有 intent / contract 目标；只有完全没有 goal 来源时才阻断。
- 清理仓库文档树：移除历史 plans、reports 和旧规格中间稿，只保留当前 README、上手指南、Agent 文档、术语表和 5 份当前规格。
- 增加 Codex session log 诊断：`diagnose-session` / `session-recovery-packet` 可识别 remote compact stream disconnected，并在恢复包中记录最后 token 计数和错误事件。
- 增加 v0.3.4 回归覆盖，锁定 Step 名称、项目 activation、文档地图、术语表和 README 的 CLI-first 降噪。

## 0.3.3

- 增加 strict step gate：human-gated step 只能按当前状态和下一待确认 gate 顺序批准，避免 Agent 批量推进或一次性请求多个 step approval。
- 增加可选 approval token policy；配置 `approval-policy.yaml` 后，`ocw step approve` 必须提供 sponsor-held token，否则只记录 untrusted attempt，不写入有效 approval。
- 为 `change prepare` 增加 scope overlap preflight，遇到 `.governance/**` 等冲突时输出人类可读恢复建议，不再暴露 Python traceback。
- 将 Step report 升级为 decision-grade panel：所有 step 投影 confirmed intent，关键 step 展示 design / tasks / contract / review / archive 摘要，并消除 Python dict repr 泄漏。
- 分离 Step 8 review entry gate 与 review decision 文案，降低“批准进入 review”和“review approve”混淆。
- 增加 `review-lifecycle.yaml`，结构化记录 request_changes、blocking findings、fix evidence requirement、rework round 和 re-review 链路，并让 `ocw revise` 自动带入 reviewer findings。
- 收束 Step 9 archived report：archive 后显示 closeout / archive preview，不再保留等待 human confirmation 的尾部提示。
- 更新 v0.3.3 回归覆盖，纳入 memorix 与 xSearch 真实 dogfood 暴露的 strict gate、签批真实性、report 摘要和 review lifecycle 问题。

## 0.3.2

- 统一 Step 5 approval 后的运行时状态投影，进入 Step 6 时同步 manifest validation objects，避免 `ocw status` 因旧验证对象产生误阻断。
- 扩展 `participants list`，显示 change bindings 中的 participant type、runtime availability、runtime reviewer 和 fallback reviewer，使真实本地 Agent 职责与 human approver 分层更清楚。
- 为 archive closeout 增加短 `FINAL_STATUS_SNAPSHOT.yaml` 引用，并让 `status --last-archive` 输出更短的归档摘要，降低长会话收束和上下文压缩风险。
- 更新 v0.3.2 回归覆盖，验证状态投影一致性、真实 participant 分层、archive final snapshot 和版本报告。

## 0.3.1

- 将 Step 1 设为新 change package 的默认起点，避免 `change create` / `change prepare` 在人类可见确认前让 Step 1-5 看起来已经完成。
- 增加面向人的 intent、participants、单个 change status 和最近归档摘要视图，方便 Agent 汇报进展而不暴露 CLI-first 细节。
- 在面向人的 step report 中加入 Step 6 / Step 7 / Step 8 证据摘要，包括执行产物、验证证据、review 运行证据和独立 reviewer 调度元信息。
- 增加带审计的 `review-revise` 恢复路径，通过 `revise` 命令和 revision history 让未通过的 review 回到 Step 6，而不是形成含糊的死状态。
- 增加默认 `scope_out` 排除项，覆盖不稳定或生成型目录，并将其贯穿 adoption 和 change preparation。
- 扩展 review decision 记录，加入真实本地 Agent review 调度、fallback 和失败透明度相关的 reviewer runtime evidence 字段。
- 更新 continuity / version 测试，并补充 v0.3.1 回归覆盖：Step 1 可见性、状态视图、证据聚合、revise 回路、review runtime evidence 和版本报告。

## 0.3.0

- 将标准 9 步运行流程提升为人类可见的 Step 1-9 报告，同时仅把传统四阶段保留为解释性映射。
- 将 `change prepare` 与 Step 1-5 完成状态分离，避免 prepare 暗示隐藏的人类批准或跳步。
- 在 status snapshot 和 step progress 中增加 `gate_type`、`gate_state` 和 `approval_state`，移除 review-only 步骤里误导性的 approval pending 语义。
- 增加面向人的 step report，包含 `framework_controls`、`agent_actions_done`、`agent_actions_expected`、清晰的输入/输出、完成标准、下一步进入标准，以及简短的 approve / revise / reject 确认选项。
- 强化 Step 5、Step 8、Step 9 的 human gate 可追溯性，包括 Step 8 review approval 引用，以及 archive 一致性检查中的 Step 5/8/9 gate summary。
- 加固 reviewer mismatch bypass 审计，要求记录人类可读原因、记录者和证据引用。
- 更新 Agent-first adoption、onboarding、current-state 和 playbook 文档，以支持人类可见参与和 closeout 可读性。
- 增加 V0.3 回归覆盖：prepare-state 语义、human-gate report、status approval 语义、review/archive 可追溯性和 idle current-state 一致性。

## 0.2.9

- 强制要求 `ocw review` 前完成 Step 8 human approval，`ocw archive` 前完成 Step 9 human approval。
- 将 reviewer mismatch 从 warning 提升为阻断性 review error，除非显式记录带审计的 bypass。
- 增加 approval provenance 字段：`recorded_by` 和 `evidence_ref`。
- 在 `archive-receipt.yaml` 中记录归档后的 Step 9 report，补齐 archive traceability。
- 扩展人类可读的 `ocw step report` 文本输出，加入输入、输出、完成标准和参与者职责。
- 增加 9 步 `ocw status` 进度表，展示 human-gated steps 的 approval state。
- 更新 v0.2.9 review/archive gate closure 的 smoke 和回归覆盖。
- 更新 Agent-first 文档，支撑 v0.2.9 发布和下一轮外部真实实践反馈。

## 0.2.8

- 为 `ocw participants setup` 增加明确的 step participant mapping，支持 `--step-owner`、`--step-assistant` 和 `--step-reviewer`。
- 在 participant setup 后重新运行 `ocw change prepare` 时保留既有 participant bindings。
- 增加 `ocw step approve`，并在 `ocw run` 前强制 Step 5 human gate。
- 在 intent、prepare、run、verify、review、archive 流程中生成默认 Step 1-9 reports。
- 为 draft-contract 场景下的 `ocw step report` 增加人类可读恢复提示。
- 在 `ocw contract validate` 中增加 intent / contract scope drift 检测。
- 增加 reviewer mismatch warning 和最终 archive state consistency snapshot。
- 更新 adoption、bootstrap、quickstart 和 smoke-test 指南，以支撑 v0.2.8 enforceable human-gates flow。

## 0.2.7

- 增加 `ocw participants setup`，用于创建个人域 participant profile 和 9 步 owner / assistant / reviewer / human-gate matrix。
- 增加 `ocw intent capture` 和 `ocw intent confirm`，让需求、优化、缺陷、范围、风险、验收标准和人类确认在执行前可见。
- 增加 `ocw step report`，落地人类可读 step report，包含 owner、输入、输出、完成标准、下一步进入标准、阻断项和人类决策。
- 增加 archive-time `.governance/current-state.md` 同步和 `ocw status --sync-current-state`。
- 扩展 `ocw hygiene` / `ocw doctor`，加入人类可读与机器可读的 state consistency diagnostics。
- 更新 bootstrap、quickstart 和 smoke-test release checks，以支撑 v0.2.7 human-control flow。

## 0.2.6

- 增加 `ocw adopt --dry-run`，基于自然语言目标、source docs 和个人域 Agent inventory 生成 Agent-first adoption plan。
- 为 `ocw change prepare` 增加 `--source-doc` 支持，并在生成的 intent、requirements 和 manifest 中记录 source documents。
- 将 `ocw run` 写入边界与 contract 的 `scope_in` / `scope_out` 对齐，并增加 scope conflict validation。
- 在 Agent handoff 输出中增加有边界的 recommended read set，避免 archive history 导致上下文爆炸。
- 增加 `ocw hygiene` / `ocw doctor`，用于分类 runtime artifacts、Agent handoff files、pending docs、tracked truth sources 和 ignored governance artifacts。
- 支持在 contract 明确授权时，将人工分析/报告 evidence refs 作为一等 evidence inputs。
- 更新 onboard / pilot 默认行为，让 Agent 从 adoption planning 和 `current-iteration` 开始，而不是固定 `personal-demo` 路径。
- 更新 bootstrap、quickstart 和 smoke-test release checks，用于验证 `ocw version`、adoption planning 和 hygiene diagnostics。

## 0.2.5

- 增加仓库级 `AGENTS.md` 作为 Agent-first adoption 入口。
- 增加 `docs/agent-adoption.md` 和 `docs/agent-playbook.md`，说明自然语言 adoption 和 Agent 操作规则。
- 通过 `change prepare` 和 `pilot` 为目标项目生成 `.governance/AGENTS.md`、`.governance/agent-playbook.md` 和 `.governance/current-state.md`。
- 重写 README 和 getting-started 文档，使其围绕 Agent-first 使用方式，而不是 CLI-first 操作方式。
- 更新 pilot 和 change prepare 输出，让 Agent 读取 handoff files，而不是要求人复制长命令提示。

## 0.2.4

- 增加 `ocw version` / `open-cowork version`，用于升级诊断。
- 增加 `scripts/update.sh` 和 `scripts/bootstrap.sh --clean`，支撑从 V0.2.3 到 V0.2.4 的平滑升级。
- 增加 `ocw change prepare`，为 change package 填充 intent、requirements、design、tasks、contract 和 bindings。
- 增加 `ocw pilot`，作为一条命令完成个人域 pilot setup 的路径。
- 更新 README 和 getting-started 文档，补充升级、重装、guided pilot 和 Agent prompt 说明。

## 0.2.3

- 增加 `ocw onboard` 和 `ocw setup`，支持交互式或脚本化 project onboarding。
- 增加 `open-cowork` console script alias，让首次使用命令更清晰。
- 更新 bootstrap shim fallback，同时暴露 `ocw` 和 `open-cowork` 命令。
- 调整 `scripts/quickstart.sh`，在 bootstrap 后调用 onboarding flow。
- 更新 README 和 getting-started 文档，说明 onboarding / setup 用法。

## 0.2.2

- 扩展 `README.md`，加入定位、背景、目标、场景、四阶段/九步骤流程、路线图、功能状态和文档索引。
- 增加 `scripts/quickstart.sh`，支持一条命令安装并初始化目标项目。
- 更新 `docs/getting-started.md`，优先推荐 quickstart 路径，同时保留手动 setup。

## 0.2.1

- 将 onboarding 文档整合到 `docs/getting-started.md`。
- 将历史 plans 和 reports 移入 `docs/archive/`。
- 将 `docs/README.md` 重写为简洁文档地图。
- 将 governance 和 community 文档本地化为中文。
- 明确 `.governance/` 是 runtime artifact storage，而不是文档区。

## 0.2.0

- 落地 Milestone 1 complex collaboration runtime chain。
- 增加 verify / review / archive gates 和最小 state transition protection。
- 增加 runtime status 和 timeline 的机器可读输出。
- 增加 continuity primitives：handoff、owner transfer、increment、closeout、sync、history、export 和 digest。
- 加固 governance reserved boundaries 和 archive / maintenance consistency checks。
- 增加 grouped sync summaries 和 digest reading compression，便于人和团队使用。
- 增加 bootstrap 和 smoke-test scripts，支撑团队首次 adoption。
- 增加个人域多 Agent pilot 指南和 role-mapping samples。
- 在 contract completion 前，让 draft change 的 `status` 和 `continuity digest` 输出更友好。
- 更新 onboarding docs，以匹配当前 CLI 和 v0.2 readiness。

## 0.1.0

- 清理仓库，便于公开分享。
- 从 tracked baseline 中移除 runtime residue。
- 增加 packaging（`pyproject.toml`）和可安装的 `ocw` entrypoint。
- 增加开源 onboarding docs（`README`、`docs/getting-started.md`、`CONTRIBUTING`）。
- 增加 session diagnosis / recovery 命令名（`diagnose-session`、`session-recovery-packet`）。
- 加固测试，使其使用自包含 fixtures，而不是依赖仓库内历史数据。

# 变更日志

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

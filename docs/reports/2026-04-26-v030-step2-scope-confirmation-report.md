# V0.3.0 Step 2 意图澄清与范围定义确认报告

Change: `v0.3-human-participation-closeout-readability`
Step: `2 / 意图澄清与范围定义`
Status: `confirmed`
Owner: `analyst-agent`
Human gate: `approved by human-sponsor`

本文是 V0.3.0 标准 9 步运行流程的 Step 2 确认报告。它承接 Step 1 已确认的输入接入与问题定界结果，将其转化为本轮 V0.3.0 的目标、范围、非目标、优先级、验收标准和复杂度档位，作为 Step 3 方案塑形的输入。

## 1. Step 2 输入物

- `docs/reports/2026-04-26-v030-step1-input-framing-report.md`
- `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_V029_DOGFOOD_REPORT_ZH.md`
- `docs/reports/2026-04-26-v030-context-compression.md`
- `docs/plans/2026-04-26-v030-human-participation-candidate-input.md`
- `docs/plans/2026-04-26-v030-human-participation-implementation-plan.md`
- `docs/specs/07-standard-9-step-runtime-flow.md`
- `docs/specs/08-role-binding-spec.md`
- `docs/specs/04-change-package-spec.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/requirements.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/tasks.md`

## 2. V0.3.0 目标

V0.3.0 要解决 open-cowork 当前在标准流程表达、人类参与、步骤边界、状态可读性和收束审计上的混乱，使 Agent-first 协作不再表现为 Agent-only 后台执行。

目标可以表述为：

> 固化标准 9 步运行流程和传统人视角阶段映射，明确每一步的输入、输出、gate、owner、完结动作和下一步进入条件；同时把 step report、status、review、archive 和 bypass trace 做成人能理解、能确认、能审计的协作界面。

## 3. 范围内

V0.3.0 范围内包含：

1. **标准流程术语与 prepare 状态分离**
   - `change prepare` 不得暗示 Step 1-5 已完成。
   - current-state、status、handoff 必须能正确表达当前标准步骤。

2. **adoption / onboarding 的人类参与入口**
   - 展示或指向 owner matrix。
   - 提醒 Step 5 / Step 8 / Step 9 human gate。
   - 引导 Agent 向人确认参与者、owner、reviewer、human gate 和 final decision owner。

3. **标准 9 步每一步边界清晰**
   - 每一步报告和状态都应明确输入、输出、gate、owner、完结动作、下一步进入条件。
   - 不只修 Step 1/2 边界，而是修全流程边界表达。

4. **Step report 人类可读格式**
   - 增加或明确 `--format human`。
   - 报告内容可直接作为人类状态汇报。

5. **framework_controls / agent_actions 分离**
   - 人能看出框架强制了什么，以及 Agent 实际做了什么。

6. **status approval 语义修正**
   - 至少区分 `not-required`、`required-pending`、`approved`、`bypassed`。
   - 避免非 gating 步骤显示 misleading pending。

7. **idle closeout 可读性**
   - archive 后可看到最近归档轮次的 closeout 摘要或明确入口。

8. **review / archive 审计链集中**
   - `review.yaml` 直接引用 Step 8 approval。
   - final consistency 汇总 Step 5/8/9 gate 状态。

9. **reviewer mismatch bypass 风险确认**
   - bypass 必须有 reason、recorded_by、evidence_ref。
   - status/review 中必须显著显示 bypass。

## 4. 范围外

V0.3.0 明确不包含：

- Dashboard / TUI / Web UI。
- 云端多人审批系统。
- 企业 RBAC。
- 跨仓库团队协作平台产品化。
- 对外部 `/Users/mlabs/Programs/xsearch/**` 仓库的修改。
- 在未进入 Step 6 前进行实现代码修改。
- 在 review approve 和 Step 9 human approval 前归档。

## 5. 优先级

### P0

- R-000：标准流程术语与 prepare 状态分离。
- R-001：adoption / onboarding 展示完整人类参与路径。
- R-002：标准 9 步每一步边界清晰，且 Step 1 确认可追踪。
- R-003：step report 提供人类可读格式。
- R-004：step report 区分 framework_controls 与 agent_actions。
- R-005：status approval 语义无歧义。

### P1

- R-006：idle status 支持最近归档轮次 closeout。
- R-007：review trace 引用 Step 8 approval。
- R-008：final consistency 汇总 human gates。
- R-009：reviewer mismatch bypass 要求人类可读风险接受。

## 6. 复杂度档位

本轮采用 `standard` 档位。

理由：

- V0.3.0 涉及 CLI 输出、状态语义、step report schema、review/archive trace、文档和测试，多模块联动，不适合 Lite。
- 当前目标仍限定在本地文件协议和 CLI/Agent 输出层，不包含 Dashboard、云端系统或企业 RBAC，因此不需要 Strict。

## 7. 验收标准

V0.3.0 的验收标准为：

1. prepare 后的状态不再误导为 Step 1-5 已完成。
2. Agent / 文档 / CLI 输出统一使用标准 9 步运行流程和传统阶段映射。
3. adoption / onboarding 能让人看到 owner matrix 和 Step 5/8/9 gate 提醒。
4. 每一步 report 能表达输入、输出、gate、owner、完结动作和下一步进入条件。
5. step report 支持人类可读格式。
6. step report 区分 `framework_controls` 和 `agent_actions`。
7. status approval 语义明确区分 `not-required`、`required-pending`、`approved`、`bypassed`。
8. idle 状态能展示或指向最近 archive closeout。
9. `review.yaml` 能直接追踪 Step 8 approval。
10. final consistency 能集中展示 Step 5/8/9 human gate summary。
11. reviewer mismatch bypass 缺少 reason、recorded_by、evidence_ref 时失败。
12. 全量单测、smoke test、contract validate、hygiene 均通过。

## 8. Human sponsor 确认

Human sponsor 已确认：

> 确认 Step 2 通过：V0.3.0 的目标、范围、非目标、优先级、验收标准和复杂度档位可以作为 Step 3 方案塑形输入。允许进入 Step 3。

## 9. Step 2 结论

Step 2 已完成。V0.3.0 可以进入 Step 3：方案塑形。

Step 3 应产出设计基线和方案方向，尤其需要说明：

- 如何先固化标准流程语义，再优化 human-facing 输出；
- 如何把“每一步边界清晰”落到 step report、status、handoff 和测试；
- 哪些模块需要修改；
- 哪些测试先写；
- 如何避免再次把准备态误投影为执行态。

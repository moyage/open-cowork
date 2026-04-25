# V0.2.6 External Dogfood Feedback: Personal-domain Multi-agent Adoption

日期：2026-04-25
反馈来源：

- `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_ADOPTION_REPORT_ZH.md`
- 另一个团队成员对 open-cowork v0.2.6 初步体验的口头/文字反馈

本文是外部 dogfood 反馈归档报告，不是已批准的实现计划。它记录 v0.2.6 在真实个人域多 Agent 试用中的体验落差，并为 v0.2.7 候选输入提供事实材料。

## 1. 背景

open-cowork 的定位是 Agent-first collaboration governance protocol，覆盖个人域、团队多人域、多 Agent 面对复杂项目和复杂任务的协作治理场景。

v0.2.6 已经完成 Agent-first adoption closure，重点修复：

- 自然语言目标到 adoption plan；
- source docs 绑定；
- bounded read set；
- role suggestions；
- contract scope；
- evidence / verify / review / archive；
- repository hygiene / doctor。

本次外部 dogfood 的核心问题不是“工具完全不可用”。相反，工具能完成从 onboarding 到 archive 的闭环。但从人的视角，当前体验仍然没有充分体现 open-cowork 声称的协作治理定位。

## 2. 已验证的可用性

xsearch 试用报告显示，v0.2.6 已能完成以下链路：

1. `open-cowork 0.2.6` 可用性校验。
2. `ocw onboard --target ... --mode quickstart --yes` 初始化项目。
3. `ocw adopt --dry-run` 生成 adoption plan。
4. 创建并准备 change。
5. `contract validate` 校验契约。
6. 执行项目验证命令并记录 `run`、`verify`、`review`。
7. `archive` 完成归档闭环。

已生成并可复用的产物包括：

- `.governance/AGENTS.md`
- `.governance/current-state.md`
- `.governance/agent-playbook.md`
- `.governance/changes/<change-id>/*`
- `.governance/archive/<change-id>/*`
- `.governance/index/*`

因此，v0.2.6 的技术闭环成立；问题集中在“人是否能感到自己正在有效治理多 Agent / 多人协作”。

## 3. 关键体验落差

### 3.1 个人域多 Agent 场景的定位落差

反馈者认为，个人域不是“一个 Agent 跑完整条 CLI 流程”，而是一个人拥有多个不同属性、不同擅长点的 Agent 组合。

在一个真实项目从意图到落地，再到闭环后继续收集新需求、旧优化、Bug 修复并持续迭代的过程中，open-cowork 应该提供一套框架，让人能从自己的视角控制和约束不同 Agent：

- 哪个 Agent 负责立项和意图澄清；
- 哪个 Agent 负责需求收集、分析和设计；
- 哪些 Agent 参与评审；
- 哪个 Agent 负责技术方案和 change package；
- 哪个 Agent 执行实施；
- 哪个 Agent 做监督审计；
- 哪个 Agent 做测试、验收和最终 review；
- 人在哪些关口确认、授权或否决。

当前 v0.2.6 虽然生成了 bindings 和 governance artifacts，但用户没有感受到这套参与者编排和人类控制面。体验更像“Agent 使用 CLI 跑完一条治理流程”，而不是“人通过 open-cowork 管理个人域多 Agent 协作”。

### 3.2 团队域场景的缺口在个人域已提前暴露

反馈者指出，团队域本质上是个人域的扩展：

- 原本本地个人域中的某些 Agent，换成其他团队成员；
- 或换成其他团队成员控制的个人域 Agent；
- 每个人都需要在流程中知道自己和自己的 Agent 负责什么、参与什么、何时评审、何时决策。

团队域中的协作问题包括：

- 谁负责项目立项；
- 谁负责需求收集、分析和设计；
- 谁参与需求评审；
- 谁负责技术方案设计；
- 谁参与技术评审并形成变更包；
- 谁负责执行和实施；
- 谁负责执行过程监督审计；
- 谁负责测试和验收；
- 谁拥有最终业务决策权。

当前测试还只停留在个人域，但个人域已经没有清楚体现这些机制。因此如果直接扩展到团队域，风险会更明显。

### 3.3 与单 Agent harness / workflow 项目的差异不够明显

反馈者明确提到，当前 open-cowork 的初步体验甚至不如一些定位为单 Agent 协作的 harness 或 workflow 实践项目，例如：

- `/Users/mlabs/Programs/oh-my-openagent`
- `/Users/mlabs/Programs/deer-flow`

这不是说 open-cowork 应该转向这些项目的定位，而是相反：open-cowork 不应该退化为单 Agent workflow。它必须在“复杂协作治理、多参与者角色、人的可见控制、持续迭代闭环”上拉开差异。

如果人的感受仍然是“一个 Agent 自动跑完”，那 open-cowork 的定位叙事和实际体验之间存在明显不一致。

## 4. xsearch 报告中的可复现工具问题

### F-001：`ocw` 路径可发现性问题

现象：同一环境中，`ocw version` 可用，但后续 shell 中 `ocw` 可能不在 PATH，需要改用绝对路径。

影响：个人域用户容易误判为安装失败。

候选方向：安装后增加 PATH 检测与修复提示，或提供 `ocw doctor --shell-path`。

### F-002：`contract validate` 参数心智负担

现象：用户自然输入 `ocw contract validate <change-id>` 会报错，正确方式是 `--change-id`。

影响：首次使用者容易踩坑。

候选方向：支持位置参数与 `--change-id` 双写法，或在错误提示中给出正确示例。

### F-003：`run` 阶段 artifact 边界报错可读性不足

现象：`--modified .governance/**` 会报 outside write boundary，因为 contract 的 `scope_in` 未包含 `.governance/**`。

影响：用户不清楚为何 evidence 目录可写，而 `.governance/**` 不能作为普通 modified artifact。

候选方向：报错信息附允许路径列表和推荐替代参数示例。

### F-004：归档后 `current-state.md` 未同步

现象：`status` 显示 lifecycle=idle 且已归档，但 `.governance/current-state.md` 仍显示 active change / step5。

影响：下一位 Agent 可能被误导。

候选方向：`archive` 时刷新 `current-state.md`，或提供 `ocw status --sync-current-state`。

### F-005：verify 与快照时序语义不清

现象：`verify` 通过，但 `STATUS_SNAPSHOT.yaml`、`STEP_MATRIX_VIEW.md` 仍停留在归档前阶段语义。

影响：审计时需要人工辨别“检查通过”和“快照生成时点”的关系。

候选方向：verify 输出增加 `snapshot_generated_at` 与 `lifecycle_at_verify` 字段，并在状态输出中解释快照时点。

## 5. 人类团队成员视角的 P0 问题

### H-001：缺少 Owner / 参与者配置入口

人的预期：安装并实施 open-cowork 时，应有明确环节让人设置 4 个阶段 9 个步骤的 owner、辅助参与者、reviewer、human gate 和最终决策权。

实际体验：`onboard` / `adopt` / `change prepare` 自动生成默认 `bindings.yaml`，但没有让人逐步确认每一步谁负责、谁协助、谁 review、谁拥有最终决策。

影响：框架声称支持多 Agent 协作，但实施初期无法建立真实团队/个人域角色映射，后续执行容易变成“CLI 自动跑完”。

### H-002：缺少意图输入与确认关卡

人的预期：open-cowork 应围绕明确意图推进，包括本次迭代新增需求、优化项、Bug 修复、验收标准和非目标。

实际体验：`--goal` 能生成 change，但流程中没有充分让用户看见并确认需求清单、非目标、风险和验收口径。执行器可以在意图未充分澄清时进入 verify/review/archive。

影响：治理对象可能从“真实项目迭代”退化为“治理工具自身的试跑”。

### H-003：每一步缺少可见阶段报告和推进门槛

人的预期：4 阶段 9 步每一步都应输出阶段报告，包含当前步骤、owner、参与者、目标、输入物、产出物、完成标准、进入下一步标准、阻断项和需要人决策的内容。

实际体验：虽然有 `STEP_MATRIX_VIEW.md`、`STATUS_SNAPSHOT.yaml` 等文件，但它们没有在执行流中形成逐步呈现、逐步确认的体验。

影响：人无法建立对流程状态的信任，也难以判断某一步是否真的完成、是否应该允许进入下一步。

## 6. 初步归因

v0.2.6 解决了 Agent-first adoption 的结构化闭环，但它仍偏向“Agent 能调用工具维护治理事实”。

下一阶段需要补齐的是“human-visible collaboration control plane”：

- 人能配置谁参与；
- 人能确认要做什么；
- 人能看到每一步处于什么状态；
- 人能决定是否进入下一步；
- Agent 能围绕这些人类决策点执行，而不是绕过它们自动闭环。

## 7. 对 v0.2.7 的建议方向

建议将 v0.2.7 的主题定为：

**Human-visible Collaboration Gates**

候选目标：

1. 增加 participants/profile setup，用于个人域和团队域参与者配置。
2. 增加 intent capture / confirmation，用于需求、优化、Bug、范围、非目标和验收标准确认。
3. 增加 step report / step gate，用于 4 阶段 9 步的可见推进。
4. 增加 current-state 同步与 doctor 一致性检查。
5. 修复 CLI 易用性和错误提示问题。

v0.2.7 不应优先扩展 Dashboard、TUI、云端协作或企业审批流。当前最重要的是让人的第一轮真实协作感受对齐 open-cowork 的定位。

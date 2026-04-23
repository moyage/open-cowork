# open-cowork PRD

## 1. 文档目的
本文件定义 open-cowork 在规格化阶段的产品需求基线，用于约束后续工程执行，不替代执行 contract，不直接宣称任何实现已完成。

项目副标题：
基于分层治理与严格边界控制的协同治理规范与流程框架，聚焦于执行约束、角色边界与事实源保护，实现“意图 → 受控执行 → 证据闭环 → 可持续迭代维护”的低侵入协同体系。

## 2. 产品定义
open-cowork 是一个协同治理框架，不是单一 workflow engine、harness builder、spec tool、plugin 或 research agent。

它解决的问题不是“让某个 Agent 更能干”，而是：
1. 把多源输入收束为清晰、可执行、可验证的 change。
2. 让多主体在低冲突、低漂移条件下协同。
3. 让执行结果以证据而不是口头声称进入验证与审查。
4. 让通过审查的结果被归档，并进入稳定事实与维护上下文。

## 3. 目标与非目标
### 3.1 主目标
构建一个可工程化落地的协同治理框架，使个人域、团队成员、多个 Agent、多个 AI Coding Agent 能围绕统一治理模型完成复杂任务与复杂项目，并维持长期可迭代性。

### 3.2 关键目标
- 把输入转化为结构化 change package。
- 在固定 9 步骨架内完成协同与 gate 控制。
- 保证 evidence / verify / review / archive 链路不可绕过。
- 默认低侵入接入，不强迫用户改造现有本地栈。
- 让产物进入后续维护，而不是停留在“一次性交付”。

### 3.3 非目标
- 不构建重型平台化云服务。
- 不自研完整 AI coding executor。
- 不要求统一底层 agent、harness 或 IDE。
- 不在 MVP 提供大量 workflow 模板、Web UI、多平台 marketplace。
- 不把 README 作为机器事实真相源。

## 4. 目标用户与场景
### 4.1 目标用户
1. 个人域开发者：已有本地工具链，希望低侵入接入治理能力。
2. 小团队协作者：需要在多人、多 Agent 并行条件下控制漂移和审查。
3. 治理/维护角色：负责 stable facts、archive、索引、维护上下文更新。

### 4.2 核心场景
1. 从模糊意图生成可执行 change package。
2. 将 change 分派给一个 executor adapter 在隔离环境执行。
3. 自动或半自动收集 evidence，并形成 verify result。
4. 由独立 reviewer 给出 approve / reject / revise decision。
5. 将批准结果归档，并刷新 stable facts 与 iteration maintenance context。

## 5. 核心价值主张
- 对外简单：用户入口短、路径清晰。
- 对内可治理：固定 9 步、双层角色绑定、结构化审计。
- 对执行层低侵入：通过目录、文件契约、命令接口、桥接接口接入。
- 对长期维护友好：当前事实、运行态、历史归档、索引分层治理。

## 6. MVP 范围
### 6.1 MVP 必须包含
- 分层治理目录。
- 一个 change package 结构。
- 一个 execution contract 结构。
- 一个 executor adapter interface 与一个真实 adapter 接入位。
- 一个 verify gate。
- 一个 review gate。
- 一个 archive 与 stable facts update 流程。
- 一个最小索引与维护上下文刷新机制。

### 6.2 MVP 明确不做
- 多 executor marketplace。
- 深 IDE / 深环境适配。
- 重型中心化服务。
- 大规模 workflow 模板库。
- 自研 AI coding runtime。

## 7. 使用复杂度分级
### Lite
- 更多 auto-pass。
- 更少必填字段。
- 适合低风险单 change。

### Standard
- 关键节点 review-required。
- 适合常规团队协作。

### Strict
- 关键节点 approval-required。
- 更严格的 evidence、verify、review、archive 要求。
- 适合高风险或长期维护关键 change。

## 8. 成功标准
### 规格阶段成功标准
- 10 类核心规格文档齐备且互不冲突。
- 可直接支持 Step 5 角色绑定与 Step 6 执行准备。
- 后续执行方无需重新定义顶层目标。

### MVP 实现成功标准
- 能跑通一个真实闭环：intent -> change -> contract -> execute -> evidence -> verify -> review -> archive -> stable facts update。
- 全链路中每一步都有结构化输入/输出。
- 审计方可基于产物而非对话声称判断完成度。

## 9. 约束
- 不重定义顶层目标。
- 不扩大 MVP。
- 不修改 9 步骨架。
- 不默认高侵入接入。
- 不把个人域具体例子写死进通用机制。

## 10. 风险
- 术语外溢导致用户理解成本过高。
- 执行层与治理层边界被弱化。
- README 或历史 archive 反向污染 stable facts。
- 为适配具体工具而损害通用低侵入原则。

## 11. 本文与其他规格关系
- 术语定义见 `02-terminology.md`
- 目录治理见 `03-fact-layer-directory-spec.md`
- 变更单元见 `04-change-package-spec.md`
- 执行约束见 `05-execution-contract-spec.md`
- 审计链路见 `06-evidence-verify-review-schema.md`
- 运行流程见 `07-standard-9-step-runtime-flow.md`

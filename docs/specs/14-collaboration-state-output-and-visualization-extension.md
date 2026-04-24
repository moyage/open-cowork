# open-cowork 协同状态输出与可视化扩展规范

## 1. 目的
本文件定义 open-cowork 如何对协同项目/任务中的参与者状态、步骤状态、change 状态与关键事件进行结构化记录与输出，以支持后续二次开发可视化插件、模板或外部集成。

本文件解决的问题不是“当前就实现一个 dashboard”，而是为未来不同展示层提供稳定、可消费、可追溯的状态语义与输出接口。

## 2. 定位与边界
### 2.1 本文件属于什么
- 属于框架级扩展能力规格。
- 属于运行态输出与派生展示支持规范。
- 属于协同治理可观测性的一部分。

### 2.2 本文件不做什么
- 不要求当前 MVP 内置图形化 dashboard。
- 不指定前端框架、UI 技术栈或可视化库。
- 不把某一种插件、模板或面板形式写死为框架标准实现。
- 不把可视化展示层提升为事实权威层。

## 3. 核心原则
- 状态必须结构化输出，不能只存在对话或临时日志中。
- 展示层是派生层，不是事实源。
- 当前状态、历史事件、稳定事实必须分层。
- 参与者状态、步骤状态、change 状态必须可区分但可关联。
- 输出必须支持多种展示方式消费，而不是为某一 UI 形式定制。
- 可视化扩展可以晚于 MVP 实现，但状态输出语义不应晚于框架设计。

## 4. 记录对象
框架至少应支持记录以下四类对象：

### 4.1 Participant State（参与者状态）
用于描述协同参与者在某个 change 或步骤中的当前状态。

示例参与者类型：
- human sponsor
- orchestrator
- analyst / architect
- executor
- verifier
- reviewer
- maintainer
- adapter / tool actor
- optional external system actor

### 4.2 Step State（步骤状态）
用于描述 Step 1-9 中某一步当前处于何种状态，例如未开始、进行中、待审、阻断、已完成。

### 4.3 Change State（变更状态）
用于描述某个 change 当前所处的生命周期位置与 gate 状态。

### 4.4 Event / Transition Record（事件/状态流转记录）
用于记录状态变化本身，以及与该变化相关的触发动作、时间、关联参与者、关联产物、关联 gate。

## 5. 参与者抽象要求
### 5.1 抽象原则
- “参与者”是状态记录对象，不要求等同于具体产品、Agent 或人。
- 一个主体可以承担多个角色。
- 一个角色可以在不同 change、不同步骤中被不同主体承担。
- 状态记录时必须同时保留 role 与 actor identity，而不能只记录自然语言名字。

### 5.2 最小字段建议
```yaml
actor_id: coordinator-1
actor_type: agent
role: analyst
change_id: CHG-20260420-001
step: 5
status: in_progress
```

### 5.3 注意事项
- 不得把某个具体个人域工具写死为唯一 actor 类型。
- 不得把“人”“Agent”“工具”混成同一种无差别节点。
- 同一 actor 的当前状态与历史事件要分开存放或可区分读取。

## 6. 状态模型要求
### 6.1 参与者状态
参与者状态至少应允许表达以下语义：
- idle
- assigned
- ready
- waiting_input
- in_progress
- blocked
- output_submitted
- waiting_review
- completed
- superseded

### 6.2 步骤状态
步骤状态至少应允许表达以下语义：
- not_started
- in_progress
- waiting_gate
- blocked
- passed
- failed
- completed

### 6.3 change 状态
change 状态至少应允许表达以下语义：
- drafting
- step5_ready
- step6_running
- verify_pending
- review_pending
- approved
- revise_required
- rejected
- archived

### 6.4 状态设计约束
- 状态词必须可稳定复用，避免同义泛滥。
- 状态值要服务于机器消费与展示映射，而不是只为文案好看。
- 状态值可以扩展，但基础语义必须稳定。
- 不允许用自由文本替代结构化状态字段。

## 7. 状态流转记录要求
### 7.1 何时产生流转记录
以下情况至少应产生一条结构化 event：
- 参与者被绑定到某步骤/某 change
- 参与者状态发生变化
- step 状态发生变化
- change 进入下一 step
- gate 状态变化
- evidence/verify/review 关键结果落盘
- archive/stable/index 更新完成

### 7.2 最小事件字段建议
```yaml
schema: collaboration-event/v1
change_id: CHG-20260420-001
event_id: EVT-20260420-001
entity_type: participant
entity_id: coordinator-1
role: analyst
step: 5
event_type: status_transition
from_status: assigned
to_status: in_progress
trigger: contract_ready
timestamp: 2026-04-20T18:30:00Z
refs:
  files:
    - .governance/changes/CHG-20260420-001/bindings.yaml
```

### 7.3 事件与事实的边界
- 事件记录“发生了什么变化”。
- 当前状态记录“现在是什么状态”。
- stable facts 记录“经治理确认的长期有效事实”。
- archive 记录“已完成 change 的历史材料”。
- 可视化层可以消费这些信息，但不能反向替代它们。

## 8. 输出层设计要求
### 8.1 输出目标
框架必须允许把协同状态输出为稳定、可解析的结构化产物，以供：
- 终端状态查看
- 本地状态页
- 第三方可视化插件
- 外部管理系统集成
- 团队协作模板/看板

### 8.2 输出形态
建议至少支持：
- 当前状态快照（snapshot）
- 历史事件时间线（timeline / event log）
- 结构化索引引用（index pointers）

### 8.3 最低要求
即使当前没有 UI，也至少应有：
- 当前 change 状态输出
- 当前步骤状态输出
- 当前参与者状态输出
- 关键事件时间线输出

## 9. 推荐目录与文件形态
本文件不强制固定目录，但建议在运行态与索引层保留清晰分层。

建议示意：
```text
.governance/
  runtime/
    status/
      change-status.yaml
      participants-status.yaml
      steps-status.yaml
    timeline/
      events.log
      events-YYYYMM.yaml
  index/
    current-change.yaml
    actor-map.yaml
    state-output-map.yaml
```

说明：
- `runtime/status/` 用于当前快照。
- `runtime/timeline/` 用于事件流或时间线。
- `index/` 用于导航、映射、引用，不作为唯一事实源。

## 10. 可视化扩展接口要求
### 10.1 总原则
可视化插件、模板或外部展示层应通过读取结构化状态输出工作，而不是直接侵入核心治理逻辑。

### 10.2 框架必须支持的能力
- 让外部展示层能够识别 actor、role、step、change、event、gate。
- 让不同展示形式共享同一套底层状态语义。
- 让展示层可以只读消费，不要求它拥有事实写入权。
- 让展示层可按项目、change、参与者、步骤筛选。

### 10.3 可以支持但当前不强制的展示形式
- timeline
- kanban / board
- swimlane
- graph
- heatmap
- role-centric panel
- project progress overview

## 11. 治理边界
- 可视化层不得成为 stable facts 权威来源。
- runtime 状态不得直接冒充已批准事实。
- 历史事件与当前状态必须可区分。
- 展示输出缺失，不等于治理流程不存在；但关键状态不落盘则视为治理可观测性不足。
- 不允许为了适配某个 UI 模板而破坏通用状态语义。

## 12. 与现有规格的关系
- `03-fact-layer-directory-spec.md` 负责 stable / changes / runtime / archive / index 分层；本文件补充 runtime 与派生展示的协同状态输出要求。
- `04-change-package-spec.md` 定义 change package；本文件补充 change 在协同过程中的状态表达与事件记录。
- `06-evidence-verify-review-schema.md` 定义 evidence / verify / review 的结构化保存；本文件补充参与者、步骤和 change 的协同状态记录。
- `07-standard-9-step-runtime-flow.md` 定义生命周期骨架；本文件补充步骤状态与跨步骤流转的可观测输出。
- `08-role-binding-spec.md` 定义角色与绑定；本文件补充绑定后的参与者状态如何记录与输出。
- `12-index-and-artifact-governance.md` 定义索引与产物治理；本文件补充状态输出如何被索引层与展示层引用。

## 13. MVP 要求与后续演进
### 13.1 MVP 至少要求
- 定义参与者状态、步骤状态、change 状态的基础语义。
- 能输出结构化当前状态快照。
- 能输出关键事件记录。
- 能被未来插件/模板以只读方式消费。

### 13.2 MVP 明确不要求
- 内置完整图形 dashboard。
- 实时动画式可视化。
- 多端同步显示。
- 复杂权限系统。

### 13.3 后续可演进方向
- 更细粒度的 actor taxonomy
- 更丰富的事件类型
- 可配置的状态映射
- 面向不同团队的展示模板
- 与外部协作系统的适配器

## 14. 阻断与反模式
以下情况视为反模式或后续实现 blocker：
- 没有结构化状态输出，却声称支持团队可视化协作。
- 把 dashboard 作为唯一真相源。
- 把 runtime 状态误当 stable facts。
- 状态只有自然语言描述，没有 machine-readable 字段。
- 为某一个 UI 形态定制核心状态结构，导致扩展性丧失。

## 15. 本轮结论
open-cowork 当前阶段不需要实现可视化产品本身，但必须把“协同参与者状态流转记录与输出”定义为框架级能力，以支持后续二次开发的可视化插件、模板和集成界面。

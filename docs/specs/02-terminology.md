# open-cowork 术语表（双层术语）

## 1. 目的
建立“用户层术语”和“系统层术语”的双层映射，确保外部低心智负担、内部可治理，并避免治理单元与执行子项混淆。

## 2. 术语设计原则
- 用户层优先使用直观词汇。
- 系统层保留治理精度，但不默认暴露给普通用户。
- 同一概念禁止在不同文档中多名混用。
- README 与 CLI 默认优先使用用户层术语。
- 治理单元与执行子项必须分层命名，不得混用。

## 3. 双层术语映射表
| 用户层术语 | 系统层术语 | 含义 | 默认是否对外暴露 |
|---|---|---|---|
| 变更 | change | 一个可独立评审、执行、验证、归档的治理单元 | 是 |
| 变更包 | change package | 承载一个 change 全链路材料的结构化文件集合 | 部分 |
| 计划 | intent + requirements + tasks | 从意图到任务拆解的上游规格集合 | 是 |
| 执行说明 | execution contract | 给执行者的受约束执行描述 | 部分 |
| 执行证据 | execution evidence | 执行阶段产生的结构化事实与附件 | 是 |
| 验证结果 | verify result | 对执行产物进行检查后的结构化结果 | 是 |
| 审查决定 | review decision | 审查方给出的 approve/reject/revise 决策 | 是 |
| 当前事实 | stable facts | 当前有效、可高权重读取的稳定事实层 | 部分 |
| 历史记录 | archive | 已完成 change 的归档材料 | 是 |
| 索引 | index | 面向检索、导航、聚合的元信息层 | 否 |
| 运行态 | runtime | 临时执行态与中间状态，不可当长期事实 | 否 |
| 角色绑定 | role binding | 抽象角色与具体参与方的绑定 | 部分 |
| 审查门 | gate | auto-pass / review-required / approval-required | 部分 |
| 复杂度档位 | policy level | Lite / Standard / Strict | 是 |

## 4. 用户层术语
推荐对外默认使用：
- 变更
- 变更包
- 执行说明
- 执行证据
- 验证结果
- 审查决定
- 当前事实
- 历史记录

可在新手提示、向导式 CLI、README 快速开始中临时使用的口语化表达：
- 任务：仅作为“要推进的一件事”的自然语言提示，不作为 change 的正式中文定义。
- 任务拆解：对应 tasks.md 中的执行子项。

不建议对外默认使用：
- runtime
- stable facts authority
- gate policy matrix
- phase transition
- maintenance refresh context

## 5. 系统层术语
### change
change 是治理单元，不是执行拆解项。它必须能够独立被评审、执行、验证、审查、归档。

### change package
一个 change 的结构化承载单元，覆盖 intent、requirements、design、tasks、contract、evidence、review 等。

### execution contract
约束执行边界、验证要求、证据要求、可操作范围的执行契约。

### verify result
验证者对结果做出的结构化判断，不等于最终审查决定。

### review decision
独立审查者或审批方给出的最终阶段性决策。

### stable facts
当前权威事实层，供 AI 高权重读取与后续迭代引用。

## 6. change 与 task 的边界
- change 是治理单元。
- task 是 change 内部的执行步骤、子任务或顺序安排。
- 一个 change 可以包含多个 tasks。
- 多个 tasks 并不会自动构成一个可独立评审的 change。
- 当文档涉及 contract、verify、review、archive、bindings、policy level 时，应优先使用 change，而不是 task。
- `tasks.md` 中的 tasks 应译为“任务”或“任务拆解”，不得反向作为 change 的正式中文定义。

## 7. 术语使用规则
- PRD、README、CLI 帮助优先用户层术语。
- schema、目录规范、审计文档允许使用系统层术语。
- 同一段落首次出现系统层术语时，应给出用户层对应词。
- 不得把内部治理词汇堆给普通用户作为起步门槛。
- 不得把 change 直接正式翻译为“任务”；如确需在新手帮助文案中使用“任务”，必须同时保持系统定义仍为“变更（change）”。

## 8. 禁止事项
- 把项目直接叫成 workflow engine / harness / plugin。
- 把 review 和 verify 混为一谈。
- 把 archive 当作 current truth。
- 把 runtime 临时状态称为稳定事实。
- 把 change 与 task 混用，导致“治理单元”和“执行子项”边界消失。

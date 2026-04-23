# open-cowork PRD

## 1. 文档角色

本 PRD 用于把 `open-cowork` 的产品定义、能力边界与迭代重点收束成一份正式基线。

它不再沿用早期“规格阶段项目”的口径，而是面向一个正在被夯实的复杂协作底层框架与协议体系。

## 2. 产品定义

`open-cowork` 是一个：

> 面向个人域与团队协作、用于组织多个“超级个体”在复杂项目与复杂任务中协同推进的底层框架与协议体系。

这里的“超级个体”并不是营销措辞，而是对现实的一种判断：

- 每个人都可能借助 AI 大模型、Agent 与 AI Coding 工具获得极强的局部执行能力；
- 但复杂项目往往无法由单一个人域独立完成；
- 因此真正的关键问题，不是单体能力，而是多个强个体如何被高质量组织起来。

`open-cowork` 就是围绕这个问题存在的。

## 3. 目标用户

### U1. 个人域中的强执行者

已经拥有成熟本地工具链，希望在保留个人效率的同时进入更稳定的协作结构。

### U2. 多个个人域构成的协作网络

不论团队规模大小，只要存在多人、多 Agent、多人域协作，就会面临协议、边界、验证与连续性问题。

### U3. sponsor / maintainer / reviewer / owner

需要看清楚：

- 当前在推进什么；
- 推进到了哪里；
- 哪些结论已经稳定；
- 哪些风险需要判断；
- 哪些地方必须人工介入。

## 4. 核心使用场景

1. 把模糊输入收束成结构化任务入口。
2. 在多人、多 Agent 条件下为复杂任务建立统一协作协议。
3. 在个人域工具异构的前提下统一任务流转、验证与交付格式。
4. 让执行结果以结构化证据而非聊天声称进入判断链。
5. 让 handoff、owner transfer 与下一轮接续成为默认能力。
6. 让复杂项目在中断、角色变化和上下文压缩后仍能恢复。

## 5. 产品目标

### G1. 把复杂任务组织成受控协作过程

不是让某个单一执行体更强，而是让多个参与者可以围绕统一协议稳定协作。

### G2. 统一协议，而不是统一工具

允许个人域异构；
把统一秩序锚定在任务入口、阶段流转、验证定义、交付协议与复盘机制上。

### G3. 让“完成”变成可判断的状态，而不是主观感觉

复杂协作的结果必须进入 evidence、verify、review、archive 与 continuity。

### G4. 让个人能力上升为团队能力

高频实践不应只停留在少数高手的本地经验中，而应逐步沉淀为模板、规则、协议与协作原语。

### G5. 让复杂协作更接近工程系统，而不是更长的对话

系统必须可控、可恢复、可验证、可协作，而不是只是“看起来更聪明”。

## 6. 非目标

`open-cowork` 当前不以以下方向为目标：

- 做成唯一的大一统 AI Coding Runtime
- 做成生态级治理系统
- 做成重型中心化协作平台
- 要求所有参与者统一本地 Agent、模型、IDE 或 CLI
- 在现阶段优先追求大而全的产品壳，而忽视底层协议与闭环质量

## 7. 能力模型

### 7.1 最小核心协议面

在完整能力模型之外，`open-cowork` 还需要定义一组“框架成立所必需的最小核心协议面”。

它们是第一版必须成立的最小内核，不应被后续增强项淹没：

1. 结构化任务入口与 change package
2. execution contract 与角色绑定
3. `execute -> evidence -> verify -> review -> archive` 主链
4. 最小 continuity packet
   - 至少包含 handoff、当前状态、当前判断点、下一步
5. 默认人类状态面
   - 至少包含 4 阶段视图、current phase、owner、waiting-on、next decision

这组协议面回答的是“什么成立了，`open-cowork` 才算真正开始成为一个复杂协作底座”。
其余能力可以逐步增强，但不应替代这组最小内核。

### 7.2 能力展开

### C1. 复杂协作闭环主链

必须逐步具备：

- change create
- contract validate
- execute
- verify
- review
- archive

### C2. 边界与状态硬化能力

必须逐步具备：

- step-entry enforcement
- owner / reviewer / verifier separation
- write-boundary protection
- truth-source / artifact boundary
- forbidden actions guard
- state transition consistency

### C3. 连续性原语

必须逐步具备：

- handoff package
- owner transfer continuity
- increment package
- standard state semantics
- escalation / sync packet

### C4. 协议与适配层

必须逐步具备：

- tool-agnostic collaborator contract
- adapter contract
- machine-readable runtime status
- 可供外部系统只读消费的稳定输出

### C5. 人类协作体验层

必须逐步具备：

- 默认 4 阶段视图
- 9 步底层骨架的可展开表达
- owner / participants / waiting-on / next decision 可见
- operator-facing reading pack
- 项目中心而非流程中心的状态表达

## 8. 默认协作模型

### 8.1 底层骨架

底层保留细粒度协作骨架，用于约束执行、验证与审查链路。

### 8.2 默认人类视图

默认对人展示 4 个阶段：

1. 定义与对齐
2. 方案与准备
3. 执行与验证
4. 审查与收束

### 8.3 设计原则

- 底层可以细，但默认体验必须清楚；
- 机器产物可以多，但人默认要读的文档必须少；
- 流程结构要服务项目推进，而不是反过来让项目围着流程汇报。

## 9. 当前版本差距

相对于目标状态，当前版本仍主要缺少：

1. 主链闭环未完全做实。
2. 边界阻断仍偏逻辑声明，尚未全部落实为真实约束。
3. handoff / owner transfer / increment 等连续性原语仍需标准化。
4. 人类可感知的阶段视图、进度快照和阅读包还不完整。
5. 不同 Agent / 工具链的协议接入层仍需进一步抽象和稳定。

## 10. 成功判断标准

当 `open-cowork` 能同时满足以下条件时，才能认为产品方向初步成立：

1. 复杂任务可以通过结构化主链稳定推进到归档与接续。
2. 关键边界违规可以被阻断或被稳定暴露，而不只是事后解释。
3. change 或项目可以在 session 中断、owner 变化后恢复推进。
4. 人和团队能在不阅读全部 runtime artifacts 的前提下理解当前状态与下一步。
5. 不同个人域与不同工具栈可以在不被强制统一的前提下协同工作。

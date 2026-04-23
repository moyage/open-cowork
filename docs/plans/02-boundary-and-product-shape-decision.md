# open-cowork 边界与产品形态决议

## 1. 目的

本文件用于固化一组顶层共识，约束后续白皮书、PRD、执行计划、change package 与实现方向。

它集中回答三个问题：

1. `open-cowork` 是否应承担完整生态治理。
2. `open-cowork` 的主身份应是复杂协作底层框架，还是完整用户 / 团队 / 企业级工具产品。
3. `open-cowork` 是否应把自己定义成一个主导型协作 agent。

## 2. 已达成共识

### C1. `open-cowork` 不承担完整生态治理

`open-cowork` 应继续聚焦项目级与任务级的复杂协作，不扩展为生态级治理中枢。

它适合承接的，是：

- 单项目或单 workstream 的复杂协作闭环
- change package、contract、evidence、review、archive、continuity
- 多角色、多 Agent、多工具条件下的协作协议与边界约束
- 项目内或项目邻近的升级与同步协议

它不应承接的，是：

- 多项目组合治理
- 跨项目仲裁
- 生态级战略治理
- 从创始人域到官方发布的总机制
- 全局连续性 / 记忆治理系统

结论：
项目级复杂协作与生态级治理应分层。生态治理应由独立上层项目负责，`open-cowork` 作为其下层项目协作底座与协议内核。

### C2. `open-cowork` 的主身份是复杂协作底层框架与协议体系

`open-cowork` 的主定位应是：

- 低侵入
- 协议优先 / 产物优先
- 工具无关
- 可开箱接入
- 可被不同 AI Agent、AI Coding 环境、workflow、harness 接入
- 面向多个“超级个体”协同的项目级复杂协作底座

它可以拥有：

- 友好的 CLI
- 可选 TUI
- 可视化只读面板
- 团队状态浏览器

但这些应被视为外层壳，而不是项目的第一性定义。

结论：
`open-cowork = framework/protocol first, product shell second`

### C3. `open-cowork` 可以具备 agent-usable capability，但不应把自己定义成主导型协作 agent

`open-cowork` 应提供可被 agent 调用的协作能力，例如：

- 生成 handoff package
- 生成 continuity input
- 生成 review / escalation packet
- 检查状态一致性
- 输出 machine-readable status

但它不应把自己定义成：

- 团队总控 PM agent
- 主导型 orchestration agent
- 替代 Hermes / OMOC / OpenAgent 的统一工作代理

结论：
`open-cowork` 可以有辅助 agent 能力，也可以有可选的 agent shell，但核心身份仍是复杂协作协议层，而不是执行主脑。

## 3. 边界分层模型

### 3.1 `open-cowork` 负责的层

- 项目级复杂协作组织
- 变更单元治理与执行约束
- 角色与写边界约束
- evidence / verify / review / archive / continuity
- 项目内或项目邻近的升级与同步协议
- 面向人的默认状态面与压缩阅读入口

### 3.2 上层生态治理项目负责的层

- 多项目组合管理
- 项目间依赖、资源冲突与阶段编排
- 战略同步、优先级裁决、组合视图
- 创始人域 / Labs 层 / 项目层之间的发布链
- 跨项目升级评审与生态级事实治理

## 4. 对后续迭代的直接约束

后续迭代必须优先补强：

1. 项目级复杂协作闭环的真实性，而不是继续扩顶层范围。
2. 最小核心协议面，而不是先堆更多增强概念。
3. 连续性、交接、owner transfer、增量同步这些项目级协作原语。
4. tool-agnostic 协议和 adapter 能力，而不是某个单一 agent 的深绑定。
5. 第一版就纳入最小人类状态面，而不是把人类体验层放到最后再补。

后续迭代不得默认滑向：

1. 重型 orchestration platform。
2. 企业级一体化控制台先行。
3. 生态级总治理系统。
4. 以单一 agent 身份吞并协作底座定义。
5. 将 `Package A-E` 误解为“一包一个版本”。

## 5. 对顶层文档与版本策略的直接约束

后续白皮书、README、PRD、执行计划应明确写出：

- `open-cowork` 是项目级复杂协作底层框架与协议体系。
- 它不是完整生态治理系统。
- 它的主身份是底层框架 / 协议层，不是先定义成企业级产品。
- 它可以支持 agent 调用，但不应被定义成统一主导 agent。
- `Package A-E` 是能力包，不是版本包。
- 推荐采用 `1 个版本、2 个内部里程碑` 的推进方式。

## 6. 一句话结论

`open-cowork` 应被重申为一个面向个人域与团队协作的、低侵入、协议优先、工具无关的项目级复杂协作底层框架与协议体系；生态级治理另立上层项目承接，产品壳与辅助 agent 能力可以演进，但不应反向定义其核心身份。

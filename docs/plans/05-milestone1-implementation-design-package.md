# open-cowork Milestone 1 实施设计包

## 1. 文档目的

本设计包用于把 `CHG-20260424-001` 进一步拆成可执行的实施结构，供后续代码实现、验证与评审直接使用。

它不替代 Change Package，而是回答：

- 这一轮怎么拆工作；
- 先做什么，后做什么；
- 各模块之间如何衔接；
- 每一步完成后如何判断可以进入下一步。

## 2. 实施目标

围绕 `Milestone 1`，在不扩大范围的前提下，完成以下 4 个最小成立面：

1. 主链闭环成立
2. 最小边界成立
3. 最小 continuity 成立
4. 最小人类状态面成立

## 3. 实施原则

1. 不追求一次补全所有长期能力。
2. 先让主链真实成立，再补足边界，再补 continuity 与人类状态面。
3. 每一块能力都必须对应可验证产物。
4. 人类状态面不是可选层，属于 `Milestone 1` 范围内的成立条件。
5. 所有新增结构必须能映射回顶层文档中的最小核心协议面。

## 4. 建议实施顺序

### Stage 1. 主链骨架打通

目标：
- 先把 `change -> contract -> execute -> verify -> review -> archive` 串成真实最小链路。

交付：
- 最小 change package 创建能力
- contract validate 能力
- execute 到 archive 的基础流转
- 对应最小测试样例

进入下一阶段条件：
- 主链不再是 placeholder，而有真实输入输出与落盘产物。

### Stage 2. 边界与状态硬化最小集

目标：
- 给主链加上最小真实约束，避免“看起来走通，实际上可绕过”。

交付：
- Step 6 准入检查
- owner / reviewer / verifier separation 检查
- 最小 write-boundary 约束
- state consistency 基本检查

进入下一阶段条件：
- 至少一类关键违规能够被真实阻断或真实暴露。

### Stage 3. continuity 最小成立

目标：
- 让主链在 session 中断或交接后可继续推进。

交付：
- 最小 continuity packet
- handoff 输出结构
- 当前阶段 / 当前判断点 / 下一步输入摘要

进入下一阶段条件：
- 不依赖回放完整聊天历史，也能恢复推进。

### Stage 4. 人类状态面最小成立

目标：
- 让人和团队可以看清当前状态，而不需要阅读全部 runtime artifacts。

交付：
- 默认 4 阶段视图
- current phase
- current owner
- waiting-on
- next decision
- 项目中心摘要

完成条件：
- 默认阅读入口能支持 owner / reviewer / sponsor 判断当前处境与下一步。

## 5. 模块级设计建议

### M1. Change 与 Contract 层

职责：
- 创建与装载 change package
- 校验 contract 是否满足最小可执行要求

建议涉及：
- CLI 入口
- change package 读写模块
- contract 校验模块

### M2. Run / Verify / Review / Archive 层

职责：
- 串起主链
- 保证 evidence、verify、review、archive 的落盘顺序和结构

建议涉及：
- runtime orchestration 入口
- evidence 记录
- verify / review / archive 结构写入

### M3. Boundary / State 层

职责：
- 承担 Step 6 准入、角色冲突、写边界和状态一致性最小检查

建议涉及：
- step gate
- role binding 检查
- state consistency 检查
- write-boundary 检查

### M4. Continuity / Human Status 层

职责：
- 输出 continuity packet
- 输出给人阅读的状态摘要

建议涉及：
- continuity 模块
- step matrix / phase mapping
- 项目中心摘要输出

## 6. 建议文件级工作包

### WP-A. CLI 与入口打通

目标：
- 让 `Milestone 1` 最小主链具备可触发入口。

建议优先检查：
- `src/governance/cli.py`
- `src/governance/run.py`
- `src/governance/change_package.py`

### WP-B. 主链真实落盘

目标：
- 保证主链每个节点都有真实落盘产物，而不是只在内存中流过。

建议优先检查：
- `src/governance/evidence.py`
- `src/governance/review.py`
- `src/governance/archive.py`
- `src/governance/index.py`

### WP-C. 边界最小硬化

目标：
- 把最小边界检查接到主链入口与执行前。

建议优先检查：
- `src/governance/contract.py`
- `src/governance/state_consistency.py`
- 相关 write-boundary / role-binding 逻辑

### WP-D. continuity 与人类状态面

目标：
- 让复杂协作结果能被下一会话和人类阅读层接住。

建议优先检查：
- `src/governance/continuity.py`
- `src/governance/step_matrix.py`
- `status` 或相关输出入口

## 7. 测试与验证设计

### T1. 主链样例测试

至少需要一个端到端样例，验证：
- change 创建
- contract 校验
- execute
- evidence 写入
- verify / review / archive 落盘

### T2. 边界测试

至少需要覆盖：
- 角色冲突
- Step 6 准入失败
- 写边界违规
- 状态不一致

### T3. continuity 测试

至少需要验证：
- continuity packet 生成
- packet 中字段完整
- 能支持下一会话恢复判断

### T4. 人类状态面测试

至少需要验证默认输出包含：
- phase
- owner
- waiting-on
- next decision
- 项目中心摘要

## 8. 建议评审点

### Review Gate 1：Stage 1 后

检查：
- 主链是否真实成立
- 是否仍有 placeholder 路径

### Review Gate 2：Stage 2 后

检查：
- 最小边界是否真实执行
- 是否仍然容易被绕过

### Review Gate 3：Stage 3 + 4 后

检查：
- continuity 是否足以恢复推进
- 人类状态面是否真的降低盲盒感

## 9. 实施期间明确禁止事项

1. 为了“显得完整”而把 `Milestone 2` 的能力提前塞进来。
2. 只补内部结构，不补默认人类状态面。
3. 用文档说明替代真实约束与真实落盘。
4. 继续生成大量默认要求人通读的文档。
5. 把实现工作拉向生态级治理或产品壳扩张。

## 10. 完成判断

本设计包对应的实现工作只有在以下条件同时满足时才可称为 `Milestone 1` 达标：

1. 最小核心协议面成立。
2. 主链闭环成立。
3. 最小边界成立。
4. 最小 continuity 成立。
5. 最小人类状态面成立。
6. 对外仍保持低侵入。

## 11. 一句话结论

`Milestone 1` 的实施，不是“多做几个命令”，而是把 `open-cowork` 的新定义第一次做成可运行、可验证、可接续、可被人理解的真实基线。

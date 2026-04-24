# open-cowork

`open-cowork` 是一个面向个人域与团队协作的复杂协作底层框架与协议体系。

它的目标，不是让某个单一 Agent 更强，而是把多个“超级个体”在复杂项目中的工作组织成可分工、可验证、可协同、可持续迭代的受控协作过程。

## 为什么会有这个项目

在 AI 时代，越来越多的人可以在个人域中借助大模型、Agent 与 AI Coding 工具获得极强的局部执行能力。

但复杂项目真正的难点，往往不在“单体够不够强”，而在：

- 多个人、多个 Agent、多个本地工具链如何一起工作；
- 如何避免每个局部都很强，但整体协同失焦；
- 如何让结果不是停留在聊天记录里，而是进入结构化项目事实；
- 如何在角色变化、上下文压缩和执行中断后继续推进。

`open-cowork` 就是为这类问题存在的。

## 核心理念

### 个人域异构，协作协议统一

`open-cowork` 不要求所有人统一本地 Agent、模型、IDE、CLI 或工作流工具。

它真正要统一的是：

- 任务入口
- 阶段流转
- 中间产物
- 验证定义
- 风险边界
- 交付格式
- 复盘与接续机制

### 方法融合，而不是标签自限

Harness、workflow、runtime、SoD、docs-as-code 等方法，只要有助于高质量、受控、可恢复的复杂协作，都可以被吸收。

`open-cowork` 不靠某个标签定义自己，而靠它要解决的问题定义自己。

### 项目级复杂协作优先

`open-cowork` 关注的是项目级和任务级的复杂协作闭环。

它不承担生态级项目组合治理、跨项目裁决或组织级战略编排；这些应由独立的上层项目承接。

## 适合什么场景

`open-cowork` 适合：

1. 个人域中的强执行者，希望把自己的高效实践接入更稳定的协作结构。
2. 多个个人域中的多个超级个体，需要围绕同一复杂任务或复杂项目进行分工、接力与审查。
3. 不同规模的团队或组织，只要存在多人、多 Agent、多工具栈协作，就可能需要这套框架。
4. sponsor / owner / reviewer / maintainer，需要更清楚地看到项目状态、风险、判断点和下一步。

换句话说，它的边界不在团队大小，而在是否需要组织复杂协同。

## 它提供什么

`open-cowork` 逐步提供的是一组复杂协作原语：

- 结构化任务入口与 change package
- 角色边界与执行约束
- evidence / verify / review / archive 闭环
- handoff、owner transfer、increment、sync 等连续性原语
- 面向人的阶段视图与状态快照
- 面向不同 Agent / 工具链的接入协议

## 默认理解方式

在底层，`open-cowork` 可以保留较细的协作骨架。
在人类默认视角下，建议用 4 个阶段来理解项目推进：

1. 定义与对齐
2. 方案与准备
3. 执行与验证
4. 审查与收束

底层可以细，默认体验必须清楚。

## 快速开始

### 1. 克隆并一键安装

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/bootstrap.sh
source .venv/bin/activate
```

`bootstrap.sh` 会优先使用标准 Python 安装方式；如果本地 `pip / setuptools` 太旧，会自动生成一个本地 `ocw` shim，保证首次试用不被安装工具版本卡住。

### 2. 验证本地安装

```bash
ocw --help
./scripts/smoke-test.sh
```

### 3. 在你的项目中初始化治理结构

进入你要接入 `open-cowork` 的目标项目根目录：

```bash
ocw --root . init
```

### 4. 查看当前协作状态

```bash
ocw --root . status
```

### 5. 读取默认接续摘要

```bash
ocw --root . continuity digest
```

### 6. 在出现上下文压缩或 session 不稳定时做诊断

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

## 当前状态

当前 `v0.2` 预备基线已经具备：

- 主链闭环：`change -> contract -> run -> verify -> review -> archive`
- 运行时状态与 timeline 的 machine-readable 输出
- handoff、owner transfer、increment、closeout、sync、history、export、digest 等 continuity 原语
- 治理保留区、状态回退、archive anchor、continuity refs 的最小硬化
- 面向团队首次试用的 bootstrap 与 smoke-test 脚本

## 文档入口

建议按下面顺序阅读：

1. `docs/specs/00-top-level-whitepaper.md`
2. `docs/specs/01-prd.md`
3. `docs/plans/01-execution-plan.md`
4. `docs/plans/02-boundary-and-product-shape-decision.md`
5. `docs/plans/03-human-team-experience-feedback-and-design-direction.md`
6. `docs/QUICKSTART.md`
7. `docs/PERSONAL_AGENT_PILOT.md`
8. `docs/reports/04-current-iteration-final-completion-and-next-round-candidate-input.md`

## 一句话总结

`open-cowork` 不是要替代每个人的个人域，而是要让多个强个人域在复杂项目中通过统一协议形成高质量协作。

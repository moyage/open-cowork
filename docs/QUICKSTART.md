# open-cowork 快速开始

本指南面向第一次接触 `open-cowork` 的个人域使用者和团队协作者。

目标不是一次学完全部概念，而是先用最低门槛把项目接入基本协作结构。

## 1. 安装

```bash
python3 -m pip install -e .
```

## 2. 在你的项目中初始化

```bash
ocw --root . init
```

这一步会创建最小治理目录与模板骨架，但不会强迫你改造现有仓库结构或工具链。

## 3. 查看当前状态

```bash
ocw --root . status
```

如果你只是先熟悉结构，这一步通常就足够。

## 4. 遇到 session / context 不稳定时

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

这两条命令用于在上下文被压缩、会话断裂或 Agent 难以继续推进时，帮助你快速定位问题并生成恢复输入。

## 5. 推荐的采用方式

### 个人域采用

1. 保留你现有的 Agent、IDE、脚本与仓库结构。
2. 只把 `open-cowork` 作为协作协议与治理层接入。
3. 先用它统一状态、边界、证据和接续，而不是一开始就替换全部工作流。

### 团队采用

1. 不强迫大家统一本地工具链。
2. 先统一任务入口、阶段语义、验证定义和交付结构。
3. 让 sponsor / owner / reviewer / maintainer 能看到同一套项目状态。
4. 逐步引入 handoff、review、archive 和 continuity 约束。

## 6. 建议下一步阅读

1. `README.md`
2. `docs/specs/00-top-level-whitepaper.md`
3. `docs/specs/01-prd.md`
4. `docs/plans/01-execution-plan.md`

## 7. 当前说明

当前公开版本已经具备基础命令与顶层文档基线。
后续迭代将继续把主链闭环、边界硬化、连续性原语和人类体验层逐步做实。

# 文档地图

本目录承载 `open-cowork` 的项目说明、上手指南、框架规格和历史迭代材料。

如果你是第一次打开这个仓库，请只按“新用户阅读路径”阅读，不需要进入 `docs/archive/`。

## 新用户阅读路径

1. `../README.md`
   - 项目是什么、适合谁、5 分钟如何开始。
2. `getting-started.md`
   - 安装、个人域多 Agent 试用、团队试用最小约定和常见问题。
3. `specs/00-top-level-whitepaper.md`
   - 顶层定位、问题背景、能力边界和长期方向。
4. `specs/01-prd.md`
   - 产品定义、用户、能力模型和成功标准。
5. `specs/04-change-package-spec.md`
   - change package 的结构和工作单元定义。
6. `specs/06-evidence-verify-review-schema.md`
   - evidence、verify、review 的最小闭环。

## 文档分区

| 路径 | 定位 | 默认是否需要阅读 |
| --- | --- | --- |
| `getting-started.md` | 唯一上手入口 | 是 |
| `specs/` | 当前框架规格和协议定义 | 按需 |
| `archive/plans/` | 历史迭代计划和设计过程记录 | 否 |
| `archive/reports/` | 历史总结、closeout 和复盘材料 | 否 |
| `.governance/` | 运行时治理产物目录，不是文档区 | 否 |

## 当前规格文档

- `specs/00-top-level-whitepaper.md`：顶层白皮书。
- `specs/01-prd.md`：产品需求与能力模型。
- `specs/02-terminology.md`：术语表。
- `specs/03-fact-layer-directory-spec.md`：事实层目录结构。
- `specs/04-change-package-spec.md`：变更包规格。
- `specs/05-execution-contract-spec.md`：执行契约规格。
- `specs/06-evidence-verify-review-schema.md`：证据、验证和审查规格。
- `specs/07-standard-9-step-runtime-flow.md`：底层 9 步运行流。
- `specs/08-role-binding-spec.md`：角色绑定规则。
- `specs/09-mvp-cli-entry-spec.md`：CLI 入口规格。
- `specs/10-test-audit-done-criteria.md`：测试、审计和完成标准。
- `specs/11-executor-adapter-interface.md`：执行器适配接口。
- `specs/12-index-and-artifact-governance.md`：索引和产物治理。
- `specs/13-round-close-report-and-closeout-package-spec.md`：轮次收束报告和 closeout package。
- `specs/14-collaboration-state-output-and-visualization-extension.md`：协作状态输出和可视化扩展。

## 历史材料

历史设计过程、Milestone 计划、closeout 和复盘材料已经移入：

- `archive/plans/`
- `archive/reports/`

这些文件保留项目演进证据，但不再作为默认阅读入口。新用户不要从这里开始。

## 说明

- 文档真相源优先级：`README.md` / `getting-started.md` / `specs/` 高于 `archive/`。
- 运行时生成的治理产物默认位于目标项目的 `.governance/`。
- 人类阅读文档不能直接充当机器事实真相源；机器事实应落在 `.governance/**` 结构化文件中。

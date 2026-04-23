# open-cowork 规格化阶段文件计划

## 1. 本轮边界
- 仅做规格化与后续工程执行计划
- 不进入工程实现、不生成运行时代码
- 不重定义顶层目标、不扩大 MVP、不改变标准 9 步骨架
- 不绕开 evidence / verify / review / archive 机制
- 默认采用低侵入接入，不把个人域具体示例写死进通用机制

## 2. 本轮计划产出文件

### 主干规格文档
1. `docs/specs/01-prd.md`
   - 项目目标、非目标、核心场景、MVP 价值、成功标准
2. `docs/specs/02-terminology.md`
   - 双层术语：用户层 / 系统层 + 映射规则
3. `docs/specs/03-fact-layer-directory-spec.md`
   - stable / changes / runtime / archive / index 目录与权威等级规范
4. `docs/specs/04-change-package-spec.md`
   - change package 最小结构、字段、Lite/Standard/Strict 裁剪规则
5. `docs/specs/05-execution-contract-spec.md`
   - execution contract 字段、边界表达、执行/验证/证据要求
6. `docs/specs/06-evidence-verify-review-schema.md`
   - evidence / verify result / review decision 的结构化 schema 规范
7. `docs/specs/07-standard-9-step-runtime-flow.md`
   - 标准 9 步的输入/输出/owner/gate/裁剪规则
8. `docs/specs/08-role-binding-spec.md`
   - 抽象角色、双层绑定、有限前置审查、角色冲突约束
9. `docs/specs/09-mvp-cli-entry-spec.md`
   - MVP 用户入口、最小 CLI、低侵入接入约束
10. `docs/specs/10-test-audit-done-criteria.md`
    - 测试策略、审计清单、规格完成/实现完成判定

### 配套文档
11. `docs/plans/01-execution-plan.md`
    - 从规格化进入工程执行的阶段计划，仅到执行准备，不直接实现
12. `docs/reports/01-status-report.md`
    - 已完成 / 未完成 / 阻断项 / 建议下一步

## 3. 目录规划
```text
<repo-root>/
  docs/
    specs/
    plans/
    reports/
```

## 4. 规格化优先级
P0：PRD、术语表、事实层目录规范、change package、execution contract、evidence/verify/review schema、标准 9 步流程
P1：角色与绑定规则、MVP CLI / 入口规格、测试/审计/完成标准
P2：执行计划、状态报告

## 5. 本轮完成标准
- 至少完成所有 P0 文档并落盘
- P1/P2 尽量完整落盘
- 各文档之间保持一致，不与输入包冲突
- 明确指出剩余缺口与后续进入工程执行前的 gate

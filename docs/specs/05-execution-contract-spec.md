# open-cowork Execution Contract 规范

## 1. 目标
execution contract 是执行者的受约束输入，用于约束黑盒或半黑盒执行，不允许执行者通过猜测扩 scope。

## 2. 设计原则
- 边界先于动作。
- 验证要求与证据要求必须前置写清。
- contract 服务于执行，而不是取代 design / requirements。
- 执行者没有 stable facts 最终写入权。
- schema 示例必须严格可解析，便于后续自动校验。

## 3. 最小字段集
```yaml
schema: execution-contract/v1
change_id: CHG-20260420-001
title: 规格化阶段主干文档建立
objective: >-
  在不进入工程实现的前提下，完成规格化主干文档。
scope_in:
  - docs/specs/**
  - docs/archive/plans/**
  - docs/archive/reports/**
scope_out:
  - src/**
  - package.json
  - external-config/**
allowed_actions:
  - create_docs
  - edit_docs
  - produce_plan
forbidden_actions:
  - implement_runtime
  - modify_external_agent_config
  - rewrite_top_level_goal
inputs:
  required:
    - docs/specs/00-specification-plan.md
    - docs/specs/01-prd.md
    - docs/specs/04-change-package-spec.md
outputs:
  required:
    - docs/specs/01-prd.md
    - docs/specs/07-standard-9-step-runtime-flow.md
verification:
  commands: []
  checks:
    - 所有文档落盘
    - 不进入工程执行
    - 不改变 9 步骨架
    - 不修改 docs 目录之外的文件
evidence_expectations:
  required:
    - file_write_record
    - output_manifest
review_handoff:
  required_reviewers:
    - reviewer
failure_policy:
  on_blocker: halt_and_report
```

## 4. 字段格式约束（建议）
- `schema`：固定使用 `execution-contract/v1`。
- `change_id`：建议匹配 `CHG-YYYYMMDD-序号`。
- `scope_in` / `scope_out`：使用字符串数组。
- `allowed_actions` / `forbidden_actions`：使用动作枚举字符串数组。
- `verification.commands`：使用命令字符串数组。
- `verification.checks`：使用检查项字符串数组。
- `review_handoff.required_reviewers`：使用角色字符串数组。
- `failure_policy.on_blocker`：建议使用固定值，如 `halt_and_report`。

## 5. 路径基准规则
- 所有显式路径默认相对项目根目录。
- 若 contract 专门约束某个 change package，可在文内额外声明“相对 `changes/<change-id>/`”。
- 同一份 contract 中不要混用“裸文件名”和“项目根相对路径”，避免执行者猜测路径基准。

## 6. 字段说明
### scope_in
允许触达或产出的文件 / 目录范围。

### scope_out
明确禁止改动范围，防止越权。

### allowed_actions / forbidden_actions
把允许动作和禁止动作显式化，避免黑盒执行者“顺手实现”。

### verification
可包含命令、静态检查、结构性检查、人工检查点。

### evidence_expectations
明确执行后必须交付哪些证据类型，而不是执行后临时补想。

### review_handoff
定义进入 review 之前必须移交给谁、至少需要哪些角色参与。

## 7. 工程实现型 contract 示例（首个真实 change package 草案）
```yaml
schema: execution-contract/v1
change_id: CHG-20260420-101
title: 首个工程实现变更包最小闭环落地
objective: >-
  在低侵入前提下，为 open-cowork 建立首轮工程实现所需的最小治理闭环，
  包括治理目录、change package、contract 校验、一个 executor adapter 接口以及
  evidence -> verify -> review -> archive 的最小链路。
scope_in:
  - .governance/**
  - src/**
  - tests/**
  - package.json
  - docs/specs/09-mvp-cli-entry-spec.md
scope_out:
  - .github/**
  - external-config/**
  - docs/specs/01-prd.md
  - docs/specs/07-standard-9-step-runtime-flow.md
allowed_actions:
  - create_code
  - edit_code
  - add_tests
  - run_tests
  - write_governance_files
forbidden_actions:
  - rewrite_architecture_baseline
  - modify_external_agent_config
  - mass_refactor_unrelated_modules
  - bypass_verify_review_archive
inputs:
  required:
    - docs/specs/03-fact-layer-directory-spec.md
    - docs/specs/04-change-package-spec.md
    - docs/specs/09-mvp-cli-entry-spec.md
    - docs/specs/11-executor-adapter-interface.md
outputs:
  required:
    - .governance/index/current-change.yaml
    - .governance/changes/CHG-20260420-101/contract.yaml
    - .governance/changes/CHG-20260420-101/verify.yaml
    - .governance/changes/CHG-20260420-101/review.yaml
    - src/**
    - tests/**
verification:
  commands:
    - npm test
    - npm run lint
  checks:
    - 首个 change package 可创建并可读取
    - run 必须基于 contract 执行
    - verify / review / archive 不可绕过
    - README 不作为机器事实源
    - 默认路径模式下普通用户无需直接编辑内部索引文件
evidence_expectations:
  required:
    - file_diff
    - command_output
    - test_output
    - changed_files_manifest
review_handoff:
  required_reviewers:
    - verifier
    - reviewer
failure_policy:
  on_blocker: halt_and_report
```

## 8. 表达规则
- contract 必须引用 change_id。
- contract 必须显式给出 forbidden_actions。
- contract 不得使用模糊词，如“必要时自行决定架构重构”。
- contract 若允许写代码，必须明确 allowed files / verification commands / rollback policy。
- contract 若用于默认路径模式，应明确哪些内部细节允许隐藏、哪些必须显式可审计。

## 9. 执行者权限边界
执行者可以：
- 在允许范围内创建 / 修改文档或代码。
- 产出结构化 evidence。
- 在 verify 失败时按 contract 允许范围纠偏。

执行者不可以：
- 改写顶层目标。
- 扩大 MVP。
- 跳过 verify / review / archive。
- 直接写 stable facts 作为最终真相。
- 修改外部 agent 配置作为默认操作。

## 10. 审核要点
- contract 是否足以约束黑盒执行。
- 执行者是否仍需要猜测边界。
- 是否显式体现 evidence / verify / review。
- 是否默认低侵入。
- 示例中的路径、字段、缩进是否可被机器解析。

## 11. 阻断条件
- 没有 scope_out。
- 没有 forbidden_actions。
- 没有 verification 或 evidence_expectations。
- contract 实际上允许执行者重新定义问题。
- contract 中路径基准不清，导致执行者需要自行猜测。

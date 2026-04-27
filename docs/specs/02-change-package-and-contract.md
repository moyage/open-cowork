# 02. Change Package and Contract

## Change package

一个 change package 是 `.governance/changes/<change-id>/` 下的工作单元，包含：

- `manifest.yaml`
- `intent-confirmation.yaml`
- `requirements.md`
- `design.md`
- `tasks.md`
- `contract.yaml`
- `bindings.yaml`
- `baseline.yaml`
- `evidence/`
- `step-reports/`
- `verify.yaml`
- `review.yaml`
- `review-lifecycle.yaml`

## Contract

`contract.yaml` 是执行边界。它至少包含：

- objective
- scope_in
- scope_out
- allowed_actions
- forbidden_actions
- validation_objects
- verification commands / checks
- evidence expectations

Step report 中 scope、acceptance 和 verification commands 必须优先显示当前权威事实。若 intent facts 缺失，应从 Contract 回退；若 intent 与 Contract 冲突，应明确显示 conflict。

## Baseline separation

`baseline.yaml` 记录 change prepare 时的 Git baseline：

- parent archived change
- dirty worktree entries
- reviewer guidance

Reviewer 应区分 previous archived dirty baseline、unrelated dirty artifacts 和 current delta。dirty baseline 不应自动等同于本轮变更失败。

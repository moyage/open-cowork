# 03. Evidence, Review, Archive

## Evidence

Evidence 是 Step 6 的执行证据，包括命令输出、测试输出、文件变更、产物引用和执行摘要。没有 evidence 不应进入 verify。

## Verify

`ocw verify` 默认执行 governance state verification，并在 `product_verification.mode` 中明确标记 `state-only`。

如果需要重跑 Contract 中的 verification commands，Agent 应使用 `ocw verify --run-commands`。命令结果会记录为：

- command
- status
- exit_code
- stdout
- stderr

## Review lifecycle

Step 8 的顺序是：

1. 独立 reviewer 运行 review。
2. `ocw review` 记录 approve / revise / reject。
3. 人批准是否接受该 review decision。
4. approve 才能进入 archive；revise 应进入 revision loop。

`review-lifecycle.yaml` 必须记录 request_changes、blocking findings、fix evidence requirement、rework round 和 re-review 链路。

## Archive

Archive 需要：

- passing verify result
- review decision = approve
- Step 8 human acceptance
- Step 9 archive approval

归档后 Step 9 report 必须是 closeout panel，不再显示等待 human confirmation。

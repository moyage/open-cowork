# v0.3.1 发布说明与下一轮真实实践反馈

发布版本：`0.3.1`
发布日期：2026-04-27
归档变更：`v0.3.1-human-participation-runtime`

## 发布摘要

v0.3.1 是对 v0.3.0 人类参与运行时的加固版本。本轮重点来自真实实践反馈：新变更必须清楚地从 Step 1 开始，`change prepare` 不能暗示前 5 步已经完成，状态视图应方便 Agent 向人汇报，review 的 `revise` 决策必须能打开清晰的修订回路，独立 review 调度必须留下运行证据，而不是只靠叙述声明。

## 主要变更

- 新 change package 默认从 Step 1 可见接入开始，不再让 `change prepare` 后的状态看起来像 Step 1-5 已完成。
- 增加面向人的 intent、participants、change status 和 last archive 状态视图。
- Step report 汇总执行证据、验证证据、review 运行证据，以及独立 reviewer 调度元信息。
- 增加通过 `ocw revise` 和 `revision-history.yaml` 记录的 `review-revise` 恢复路径。
- 默认排除不稳定或生成型目录，包括 `.git`、`.omx`、`.venv`、`dist`、`node_modules`、`.release`、`.governance/archive` 和 `.governance/runtime`。
- review decision 增加真实本地 Agent 调度、fallback 和失败透明度相关的运行证据字段。
- idle 状态下可展示最近归档 closeout 摘要，便于人和后续 Agent 接续。

## 发布验证

- `python3 -m unittest discover -s tests -v`：180 个测试通过。
- `./scripts/smoke-test.sh`：通过。
- `./bin/ocw version`：`open-cowork 0.3.1`。
- `./bin/ocw hygiene --format json`：`state_consistency.status = pass`。
- `git diff --check`：通过。
- `uv build --out-dir /tmp/open-cowork-dist-uv`：已生成 `open_cowork-0.3.1.tar.gz` 和 `open_cowork-0.3.1-py3-none-any.whl`。

## 归档证据

- `.governance/archive/v0.3.1-human-participation-runtime/archive-receipt.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/FINAL_STATE_CONSISTENCY_CHECK.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/review.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/step-reports/step-9.yaml`
- `docs/reports/2026-04-27-v031-final-retrospective-and-closeout-report.md`

## 独立 Review 证据

- Hermes 已作为 primary reviewer 被真实调度，但因 provider HTTP 403 quota / pre-consume token failure 失败。
- 在人批准 reviewer mismatch bypass 后，OOSO/OMOC 被真实调度为本地 fallback reviewer。
- OOSO 初次 review 要求 `revise`；revision round 1 完成后，OOSO rereview 结论为 approve。
- reviewer mismatch bypass 和运行证据已记录在 `human-gates.yaml`、`review.yaml` 和 final consistency summary 中。

## 下一轮真实实践反馈重点

请团队成员基于 v0.3.1 在真实个人域 Agent 工作流中测试，并重点反馈：

- 新 change 是否能在 prepare / execution 前清楚地从 Step 1 开始。
- `intent status`、`participants list`、`change status`、`status --last-archive` 是否足够支撑 Agent 向人汇报进展，而不把人拉回 CLI-first 细节。
- review `revise` 以及后续 rerun / rereview 是否是可恢复、可理解的，而不是新的混乱状态。
- 真实本地独立 reviewer 调度证据是否容易检查。
- archive closeout 和 idle status 是否能在上下文压缩后提供足够接续信息。
- Step 9 后是否仍存在报告措辞或 snapshot 产物造成的歧义。

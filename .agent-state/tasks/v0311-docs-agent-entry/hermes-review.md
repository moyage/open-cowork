# Hermes review summary: v0311-docs-agent-entry

## 第一轮 review

- 工具：真实本地 Hermes CLI
- 命令入口：`hermes chat -q ...`
- 原始输出：`.agent-state/tasks/v0311-docs-agent-entry/hermes-review.raw.txt`
- decision：`revise`

Hermes 第一轮认为主体文档方向正确，但要求收口前修正：

1. `.governance/current-state.md` 与已完成扫描、测试和 review 现实不同步，仍停留在 Step 6 / review 前语态。
2. `.governance/current-state.md` 容易混淆“历史批次已 approve”和“当前文档批次待 review”。
3. `.governance/agent-entry.md` 对单 active round 与多 active rounds 的接续规则表达不够精确。

## 修正

- `.governance/current-state.md` 更新为 Step 8 / 独立审查修订，明确历史批次已 approve、当前批次处于 Hermes revise 后复审流程，并引用验证证据。
- `.governance/agent-entry.md` 更新为：
  - exactly one active round：报告 scope/readiness 后可接续；
  - multiple active rounds 且人已指定目标：接续指定目标；
  - multiple active rounds 且人未指定目标：先询问目标。
- `.agent-state/tasks/v0311-docs-agent-entry/verify-result.md` 追加 revise 后复验证据。

## 复审

- 工具：真实本地 Hermes CLI
- 命令入口：`hermes chat -q ...`
- 原始输出：`.agent-state/tasks/v0311-docs-agent-entry/hermes-rereview.raw.txt`
- decision：`approve`

Hermes 复审结论：

- 无阻断问题。
- 本批次可通过。
- 当前入口文档未发现把旧 heavy layout 继续表述为 v0.3.11 默认模型的回归。

## 复审证据

Hermes 复审实际运行 / 核对：

- 定向入口文档扫描旧 heavy layout 默认路径：无输出。
- `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'`：31 tests OK。
- `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v03[45].py'`：14 tests OK。
- `PYTHONPATH=src python3 -m unittest discover -s tests`：278 tests OK。

## 残余风险

- `.governance/current-state.md` 仍是人工维护的可读摘要，后续 dogfood 迁移落地 `state.yaml` 后需要保持同步。
- 多 round 接续语义已在入口规则中澄清，后续 README / getting-started / agent-entry 改动时需要继续保持一致。

# open-cowork 当前规格

`docs/specs/` 只保留当前会生效的框架规格，不是试用过程记录。历史计划、dogfood 报告、实现过程记录和过期中间产物不再放在这里。

## 当前有效规格

| 文件 | 说明 |
| --- | --- |
| `00-overview.md` | 协议定位、适用边界和非目标。 |
| `01-runtime-flow.md` | 4 阶段 / 9 步运行流、gate 与 acknowledgement 语义。 |
| `02-change-package-and-contract.md` | 变更包、Contract、scope、baseline separation。 |
| `03-evidence-review-archive.md` | Evidence、Verify、Review、Archive、review lifecycle。 |
| `04-agent-adoption-and-doc-governance.md` | Agent-first 实施、项目级 activation、文档治理。 |
| `05-deterministic-resume-and-merge-safe-governance.md` | v0.3.6 确定性接续入口与可合并 `.governance/` 布局设计。 |

普通使用者不需要先读本目录。Agent、维护者和 reviewer 在审计协议行为时按需读取。

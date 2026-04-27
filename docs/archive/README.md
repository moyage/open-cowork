# 历史归档

`docs/archive/` 只保留归档入口说明。旧的 plans、reports 和 dogfood 中间材料已经从主文档树移出，避免新用户和 Agent 把历史过程当成当前操作手册。

历史证据，不是当前实施入口。

## 当前规则

- 当前使用说明放在 `../README.md`、`../getting-started.md`、`../agent-playbook.md`。
- 当前协议规格放在 `../specs/`。
- 历史材料通过 Git 历史或发布包追溯，不作为默认上下文读取集。
- Agent 不应默认全文扫描历史 archive；只有人明确指定某个 source doc，或 handoff/recovery packet 推荐了具体路径时，才按路径读取。

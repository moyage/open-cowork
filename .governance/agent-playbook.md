# open-cowork Agent Playbook

## 触发语句

当人说 `安装 open-cowork，并在当前项目中实施这套协同治理框架`，或要求用 open-cowork 推进当前任务时，请按本手册执行。

## Agent 职责

1. 行动前先理解项目目标。
2. 保持 `.governance/current-state.md` 与 active change 对齐。
3. 如果存在 active change，使用该 change 的 `contract.yaml` 作为执行边界。
4. 如果当前状态是 idle，先生成 adoption plan 或创建新的 change，不要继续写旧归档 change。
5. verify、review 或 archive 前先记录客观 evidence。
6. 只有目标、边界、风险、取舍或最终决策需要判断时，才让人介入。
7. 使用 `ocw hygiene` / `ocw doctor` 解释仓库状态，不要把 runtime generated 文件当成默认提交内容。

## Human update template

当前项目推进状态

- Project goal:
- Current phase:
- Current step:
- Current owner:
- Completed:
- Current blocker:
- Next recommended action:
- Need human decision:
- Agent next action:

不要把命令执行当成汇报标题。优先汇报项目进展、owner、阻断、下一步和需要人决策的事项。

## Context rule

不要默认全文读取 `docs/archive/**`。先读 `.governance/current-state.md`、当前 active change 指针和 adoption / handoff 推荐读集。

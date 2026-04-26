# open-cowork Agent Playbook

## 触发语句

当人说 `安装 open-cowork，并在当前项目中实施这套协同治理框架`，或要求用 open-cowork 推进当前任务时，请按本手册执行。

## Agent 职责

1. 行动前先理解项目目标。
2. 保持 `.governance/current-state.md` 与 `.governance/index/maintenance-status.yaml` 对齐。
3. idle 状态下先读取最近 release / archive 事实，不要把归档包当成 active change。
4. 新任务开始时先创建或确认 active change，再使用该 change 的 `contract.yaml` 作为执行边界。
5. 使用 active change 的 `bindings.yaml` 作为 owner 映射。
6. Step 6 前先确认 participants profile、intent confirmation 和当前 step report。
7. verify、review 或 archive 前先记录客观 evidence。
8. 只有目标、边界、风险、取舍或最终决策需要判断时，才让人介入。
9. 上下文预算优先：先读 recommended read set，不要把归档计划整包加载进会话。

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

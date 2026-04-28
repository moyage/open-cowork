# open-cowork Agent Playbook

## 触发语句

当人要求继续、接手、审查、验证或发布本项目工作时，先运行确定性入口 `ocw resume`。自然语言只是请求入口，不是协议触发条件。

## Agent 职责

1. 行动前先理解项目目标。
2. 先做项目级 resume；多 active change 时必须显式选择 change_id。
3. 保持 `.governance/local/current-state.md` 与 active change 对齐。
4. 使用 `ocw resume` recommended read set 中的 contract.yaml 作为执行边界。
5. 使用 `ocw resume` recommended read set 中的 bindings.yaml 作为 owner 映射。
6. Step 6 前必须完成 Step 1-5 的真实确认链，不能把 prepare 当成 Step 5 完成。
7. verify、review 或 archive 前先记录客观 evidence。
8. 只有目标、边界、风险、取舍或最终决策需要判断时，才让人介入。
9. 上下文预算优先：先读 recommended read set，不要把归档计划整包加载进会话。
10. 所有已确认需求都按完整实现推进；如需降级、拆分或延期，先停下记录影响并取得人的明确批准。

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

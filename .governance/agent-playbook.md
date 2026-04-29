# open-cowork Agent Playbook

## 触发语句

当人要求继续、接手、审查、验证或发布本项目工作时，先运行确定性项目 resume / status 入口。自然语言只是请求入口，不是协议触发条件。

## Agent 职责

1. 行动前先理解项目目标。
2. 先做项目级 activation；多 active round 时必须显式选择目标。
3. 保持 `.governance/current-state.md` 与 `state.yaml` 对齐。
4. 使用当前 round 的 scope 作为执行边界。
5. 使用 role bindings 作为 owner / reviewer / human gate 映射。
6. Step 6 前必须完成 Step 1-5 的真实确认链，不能把 prepare 当成 Step 5 完成。
7. verify、review 或 closeout 前先记录客观 evidence refs。
8. 只有目标、边界、风险、取舍或最终决策需要判断时，才让人介入。
9. 上下文预算优先：先读 recommended read set，不要把冷历史整包加载进会话。

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

# 08. v0.3.9 Team Operating Loop

v0.3.9 的目标是把多个拥有个人域 AI 能力的超级个体组织成可持续协作的超级组织，但仍保持 open-cowork 的协议层定位。它不实现 issue tracker、云端团队管理平台、GUI、desktop、web platform，也不接管 Agent runtime。

## 操作事实层

团队操作循环的事实写入 `.governance/team/**`：

- `operating-loop.yaml`：团队状态视图的结构化快照。
- `participants.yaml`：本地个人域 Agent、远程团队成员 Agent、能力、入口、所属域、默认角色和可担任步骤。
- `participant-events/`：参与者发现、登记、更新和分派事件。
- `assignments.yaml`：change / step 的 owner、executor、reviewer 和 participant 分派。
- `blocked.yaml`：阻塞项、waiting_on、next_decision、记录人、清除记录和历史。
- `reviewer-queue.yaml`：待审查 change、候选 reviewer、优先级和独立性状态。
- `recurring-intents.yaml`：周期性意图，只能触发 Step 1 change 草稿。
- `carry-forward.yaml`：归档或复盘后的下轮候选池。
- `retrospectives/`：团队复盘资产，包含 YAML 和人类可读 Markdown。

`.governance/team/**` 是团队当前操作面，不替代 `.governance/changes/<change-id>/` 中的 intent、contract、evidence、verify、review 和 archive 权威事实。

## 命令面

v0.3.9 提供以下 Agent-facing 命令：

- `ocw team status`
- `ocw team digest`
- `ocw participant discover`
- `ocw participant register`
- `ocw participant list`
- `ocw participant assign`
- `ocw participant update`
- `ocw assignment set`
- `ocw blocked set`
- `ocw blocked clear`
- `ocw reviewer queue`
- `ocw recurring-intent add`
- `ocw recurring-intent trigger`
- `ocw carry-forward list`
- `ocw carry-forward add`
- `ocw carry-forward promote`
- `ocw retrospective add`
- `ocw retrospective list`
- `ocw preflight check`
- `ocw preflight recovery`

这些命令是 Agent 内部维护治理事实的工具。人仍然通过自然语言表达目标、批准范围、确认开工、选择审查结论和批准归档。

## 参与者与多 Agent 协作

个人域环境下，Agent 可以运行 `participant discover` 探测本机可见候选，例如 Hermes、OMOC、OpenCode 或 Codex。自动探测只产生候选，不等于直接授权参与；参与者仍需通过登记或人类审阅进入事实层。

团队域环境下，远程团队成员的个人域 Agent 通过声明式参与者档案或邀请 / 注册事实接入。open-cowork 不会把本地不可调用的远程 Agent 伪装成本地可执行 Agent。

owner、executor、reviewer 和 participant 分派可以在项目执行过程中的任意步骤调整。每次调整必须进入结构化事实和事件历史，而不是只留在聊天上下文里。

## 安全边界

- reviewer 不能被分派给自己的执行结果；发现自审风险时命令必须阻断。
- reviewer 自审阻断必须同时读取 `.governance/team/assignments.yaml` 和 change package `bindings.yaml` 中既有 Step 6 executor / owner，不能只检查新写入的分派事实。
- recurring intent 和 carry-forward promote 只能创建或准备 Step 1 change 草稿，不能进入 Step 6，不能绕过 Step 5。
- blocked set / clear 必须保留历史，不能静默擦除阻塞事实。
- reviewer queue 只能排队或推荐审查者，不能替代 Step 8 review decision。
- team digest 是同步材料，不能把队列状态或聊天内容伪装为完成结论。
- 已启用 open-cowork 的项目修改项目文件前仍必须通过 preflight。
- `preflight check --path` 必须对待修改路径执行 `scope_in` / `scope_out` 范围校验；未声明待修改路径时只能证明治理门禁状态，不能声称具体文件已在范围内。
- Agent 发现或登记参与者不能伪造人类确认；由 Agent 记录的参与者必须标记为待人工审阅，只有真实 human gate 才能写入等价的人类确认状态。
- 事后补录只能作为 recovery：必须记录绕过原因、已修改文件、缺失的 contract / evidence / review 和恢复动作，不能伪装为正常执行证据。

## 完整实现要求

v0.3.9 的 planned commands、planned governance files 和 acceptance criteria 必须完整实现。未经人类 sponsor 明确批准，不得降级为文档占位、最小命令、部分延期或事后再补。

## 验收标准

- 同一项目多个 active changes 能在 team status / team digest 中展示。
- participant discover / register / list / assign / update 覆盖本地个人域 Agent 与远程声明式 Agent。
- assignment set 能记录 owner / executor / reviewer，并阻断 reviewer 自审。
- blocked set / clear 能影响 team status / digest，并保留历史。
- reviewer queue 能展示候选 reviewer、独立性和优先级。
- recurring intent 只能触发 Step 1 change 草稿。
- carry-forward list / add / promote 能形成下一轮候选池，并且 promote 不进入 Step 6。
- retrospective add / list 能生成团队复盘资产，并被 digest 引用。
- preflight check 在无 active change、Step 5 未批准、Step 6 未就绪或待修改路径越界时阻断执行。
- preflight recovery 能记录已绕过流程的事实，并明确区分 recovery 与正常 evidence。
- Step 1 未确认前不得生成 Step 2+ 报告或推进后续步骤。
- 全量测试通过：`python3 -m unittest discover -s tests`。

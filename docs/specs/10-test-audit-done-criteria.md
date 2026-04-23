# open-cowork 测试、审计与完成标准

## 1. 目标
定义规格阶段完成标准、工程执行前 gate、实现后测试与审计要求、缺陷分级与 blocker 规则。

## 2. 规格化完成判定
当且仅当以下条件同时满足时，规格化阶段可视为完成：
1. PRD、术语表、目录规范、change package、execution contract、evidence/verify/review schema、9 步流程、角色绑定、CLI 入口、测试审计标准全部存在。
2. 文档之间不冲突。
3. 不扩大 MVP，不改变 9 步骨架。
4. 明确 Lite / Standard / Strict 裁剪规则。
5. 后续执行方可直接据此进入 Step 5/6 的工程执行准备。

## 3. 工程执行前必须通过的 gate
- Step 5 角色绑定已明确。
- contract 已形成且边界清晰。
- 至少一个 executor adapter interface 已规格化。
- verify/review/archive 路径已定义。
- 阻断项已消除或被明确审批豁免。

## 4. MVP 实现后的测试要求
### 4.1 功能测试
- `init` 可建立治理目录。
- `change create` 可生成最小 change package。
- `contract generate` 可生成最小 contract 草稿。
- `run` 可通过一个 adapter 完成一次受控执行。
- `verify` 可生成 verify result。
- `review` 可记录 decision。
- `archive` 可归档并刷新 stable/index。

### 4.2 集成测试
- 从 propose 到 archive 跑通一个真实闭环。
- 验证 Step 8 与 Step 9 不可绕过。
- 验证 stable / archive / runtime 不混层。

### 4.3 审计测试
- README 不作为机器事实源。
- evidence 缺失时不得 claim 完成。
- executor 不得直接写 stable facts 最终版本。
- archive 后必须存在 index refresh 痕迹。

## 5. 缺陷等级
- blocker：违背顶层目标、MVP 边界、9 步骨架、evidence/verify/review/archive 链路、低侵入原则。
- major：主链路可运行但审计或维护能力明显不足。
- minor：文档不清、字段可补、非主链路问题。
- note：建议优化项。

## 6. blocker 示例
- 默认高侵入接入。
- 直接从 Step 3 跳到 Step 6。
- review 缺失明确 decision。
- Step 9 被跳过。
- stable 与 archive 混用。
- 项目被收缩成单纯 workflow engine / harness / plugin。

## 7. 审计清单
1. 是否忠实保持顶层定位。
2. 是否未扩大 MVP。
3. 是否保留标准 9 步骨架。
4. 是否有结构化 contract。
5. 是否有结构化 evidence。
6. verify 与 review 是否分离。
7. Step 8 是否有明确 decision。
8. Step 9 是否完成 archive + stable update + index refresh。
9. 是否默认低侵入接入。
10. 是否未把个人域具体例子写死进通用机制。

## 8. 本轮状态使用方式
本文件既用于规格阶段 closure，也用于后续工程执行完成后的独立审计基线。

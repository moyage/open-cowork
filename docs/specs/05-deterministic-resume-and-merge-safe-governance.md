# 05. Deterministic Resume and Merge-safe Governance

本规格定义 v0.3.6 的设计基线。它回应 v0.3.5 发布后暴露出的两个根本问题：

1. 新会话或另一个 Agent 不应依赖自然语言关键词来“猜测”是否触发 open-cowork。
2. 多人、多环境、多任务协作时，`.governance/` 内的事实、索引、投影和本地状态必须具备清晰的合并边界。

## 设计目标

- 提供一个确定性、跨语种、跨 Agent 的项目接续入口。
- 让人只需要知道一条稳定入口，而不是学习完整 CLI。
- 让 Agent 在新会话中可以从项目事实恢复，而不是从聊天历史恢复。
- 降低多人 / 多分支 / 多任务同时修改 `.governance/` 时的冲突概率。
- 明确哪些文件是权威事实，哪些文件是可重建索引，哪些文件是本地运行投影。

## 非目标

- 不把自然语言关键词识别作为协议层触发机制。
- 不要求团队统一 IDE、Agent runtime、工作台或个人域工具组合。
- 不在 v0.3.6 中引入中心化服务、数据库或远端锁。
- 不把所有 `.governance/` 文件都从 Git 中移除；只有本地投影和可再生状态默认不应成为团队合并负担。

## 确定性接续入口

v0.3.6 引入 `ocw resume` 作为人和 Agent 都可以记住的最小稳定入口。它是 `project activation` 的确定性包装，不依赖自然语言内容、语种或关键词。

推荐的人类入口是：

```text
请在当前项目运行 ocw resume。
```

这句话只是让 Agent 执行确定性命令；协议语义来自命令和参数，而不是自然语言本身。

### 命令形态

```bash
ocw resume
ocw resume --list
ocw resume --change-id <change-id>
ocw resume --format text
ocw resume --format json
```

语义：

- `ocw resume`：读取当前项目 `.governance/`，执行项目级接续判断。
- `ocw resume --list`：只列出可接续的 active changes，不选择、不执行。
- `ocw resume --change-id <change-id>`：接续指定 change。
- `--format text`：面向人和 Agent 的默认简洁汇报。
- `--format json`：给 Agent、脚本或其他 harness 的稳定机器输出。

### 默认行为

`ocw resume` 必须满足：

- 如果 `.governance/` 不存在，返回 `install-or-initialize`，提示 Agent 初始化，而不是假装已有状态。
- 如果没有 active change，返回 `open-new-change`，提示 Agent 捕获下一轮意图。
- 如果只有一个 active change，返回 `continue-active-change`，输出当前 step、owner、waiting_on、next_decision 和 recommended read set。
- 如果存在多个 active changes，返回 `choose-active-change`，列出候选项，并要求使用 `ocw resume --change-id <id>` 继续。
- 不从聊天历史、最近编辑文件或自然语言猜测当前 change。

### 与 `ocw activate` 的关系

`ocw activate` 保留为底层 activation primitive 和兼容入口。`ocw resume` 是推荐公开入口：

- 人类文档优先展示 `ocw resume`。
- Agent Entry 优先要求运行 `ocw resume`。
- 现有 `ocw activate --change-id <id>` 继续可用，但文档中定位为底层 / 兼容命令。

## Merge-safe `.governance/` 分层

`.governance/` 不应被看作一个普通文档目录。它是项目协作事实层，应按合并风险分层。

| 类型 | 典型位置 | 权威性 | 推荐合并策略 |
| --- | --- | --- | --- |
| 稳定入口规则 | `.governance/AGENTS.md`、`.governance/agent-entry.md`、`.governance/agent-playbook.md` | 稳定规则 | 少改，正常合并 |
| 单 change 权威事实 | `.governance/changes/<change-id>/contract.yaml`、`bindings.yaml`、`intent-confirmation.yaml`、`step-reports/**`、`evidence/**`、`verify.yaml`、`review.yaml` | 权威事实 | 按 change 隔离，正常合并 |
| 归档事实 | `.governance/archive/<change-id>/**` | 权威事实 | append / immutable，正常合并 |
| 共享索引缓存 | `.governance/index/active-changes.yaml`、`changes-index.yaml`、`archive-map.yaml` | 可重建索引 | 可由 change / archive 重建；冲突时重建 |
| 当前工作指针 | `.governance/index/current-change.yaml` | 本地偏好 / 兼容指针 | 不作为团队权威；冲突时由 `ocw resume --change-id` 明确选择 |
| 本地运行投影 | `.governance/current-state.md`、`.governance/PROJECT_ACTIVATION.yaml`、`.governance/runtime/status/**` | 可再生视图 | 默认忽略或迁移到 local runtime |
| 事件日志 | `.governance/runtime/timeline/**`、`.governance/runtime/sync-history/**` | 运行记录 | 按 change / actor / month 分片，避免多人写同一文件 |

## 权威源规则

v0.3.6 的合并原则是：权威事实优先，投影可重建。

- 当前 change 的执行边界以 `.governance/changes/<change-id>/contract.yaml` 为准。
- 角色和 owner 以 `.governance/changes/<change-id>/bindings.yaml` 为准。
- 执行与验证证据以 `.governance/changes/<change-id>/evidence/**`、`verify.yaml`、`review.yaml` 为准。
- 归档状态以 `.governance/archive/<change-id>/archive-receipt.yaml` 和 closeout artifacts 为准。
- `current-state.md`、`PROJECT_ACTIVATION.yaml`、runtime status 是投影，不得作为唯一权威源。
- active changes 列表可以由未归档的 change manifests 和 archive map 重建。

## v0.3.6 布局调整

### 稳定入口文件不再绑定 change

新项目生成的以下文件不应嵌入某个固定 `change_id`：

- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`

它们只描述通用接手规则。具体 change 由 `ocw resume` 输出或 `ocw resume --change-id <id>` 指定。

### 本地投影目录

引入本地投影目录：

```text
.governance/local/
```

默认写入：

- `.governance/current-state.md`
- `.governance/local/PROJECT_ACTIVATION.yaml`
- `.governance/local/runtime/status/**`

新项目应生成 `.governance/.gitignore`，默认忽略：

```gitignore
/local/
/PROJECT_ACTIVATION.yaml
/current-state.md
/runtime/status/
```

为兼容 v0.3.5，旧路径可以继续读取，但新写入优先进入 `.governance/local/`。如果团队希望提交共享快照，可以显式导出，而不是让每个 Agent 自动改同一个根目录投影。

### 索引重建

新增或明确以下内部能力：

```bash
ocw index rebuild
```

它从权威事实重建：

- `.governance/index/active-changes.yaml`
- `.governance/index/changes-index.yaml`
- `.governance/index/archive-map.yaml`

当这些索引文件发生 Git 冲突时，推荐处理方式是：

1. 保留权威 change / archive 目录。
2. 丢弃冲突中的索引文件内容。
3. 运行 `ocw index rebuild`。
4. 再运行 `ocw resume --list` 检查 active changes。

## Agent Entry 更新

目标项目 `.governance/agent-entry.md` 应明确：

1. 可靠接续入口是 `ocw resume`，不是自然语言关键词。
2. 多 active changes 时必须运行 `ocw resume --list` 或 `ocw resume --change-id <id>`。
3. 不得从聊天历史推断当前 change。
4. 只读取 `ocw resume` 返回的 recommended read set。
5. `.governance/local/**` 是本地投影，不应被当作团队权威事实。

## 文档更新要求

README、getting-started、agent-adoption 和 docs/specs 应同步表达：

- 人可以用自然语言要求 Agent “运行 `ocw resume`”，但协议触发点是命令。
- `ocw resume` 是新会话、跨 Agent、跨成员接续的统一入口。
- `.governance/current-state.md` 和 `PROJECT_ACTIVATION.yaml` 是可再生投影；v0.3.6 新项目默认将其迁移到 `.governance/local/`。
- 多人协作时优先按 change 目录隔离事实，索引冲突通过 rebuild 解决。

## 迁移策略

v0.3.5 项目升级到 v0.3.6 时：

1. 保留现有 `.governance/changes/**` 和 `.governance/archive/**`。
2. 将入口文件更新为不绑定固定 change 的通用模板。
3. 生成 `.governance/.gitignore`。
4. 后续 `resume` / activation 投影写入 `.governance/local/`。
5. 旧的 `.governance/current-state.md`、`.governance/PROJECT_ACTIVATION.yaml` 可以继续被读取，但不再作为推荐写入位置。
6. 如索引文件发生冲突，运行 `ocw index rebuild` 从权威事实恢复。

## 验收标准

v0.3.6 必须满足：

- `ocw resume`、`ocw resume --list`、`ocw resume --change-id <id>` 有测试覆盖。
- `ocw resume` 在 0 / 1 / 多 active changes 下输出确定性 recommended mode。
- 新生成的 `.governance/agent-entry.md` 不包含固定 change_id。
- 新生成的 `.governance/.gitignore` 忽略本地投影。
- activation / current-state 新写入默认进入 `.governance/local/`。
- `ocw index rebuild` 可从 change / archive 权威事实重建索引。
- README 和 getting-started 不把自然语言关键词识别描述成协议层触发机制。
- 兼容 v0.3.5 项目：旧 `.governance/current-state.md` 和 `.governance/PROJECT_ACTIVATION.yaml` 存在时不报错。

## 风险与取舍

- 将 `current-state.md` 迁入 local 会降低其作为团队共享快照的可见性；用 step report、review summary 和 archive closeout 承担团队共享阅读职责。
- `ocw resume` 增加了一个公开入口，但减少了人需要理解的命令总量。
- 索引重建要求权威 change / archive 文件足够完整；实现时必须补齐缺失字段的保守 fallback。
- 旧项目同时存在根目录投影和 local 投影时，Agent 必须优先信任权威事实与 local 最新投影，而不是简单按文件名读取。

## v0.3.6 实施顺序

1. 增加 `ocw resume` 命令和测试。
2. 调整 activation / current-state 写入位置到 `.governance/local/`，保留旧路径读取兼容。
3. 让生成的 Agent Entry / Playbook / AGENTS 不再嵌入固定 change_id。
4. 生成 `.governance/.gitignore`。
5. 增加 `ocw index rebuild`。
6. 更新 README、getting-started、agent-adoption、glossary 和 release note。
7. 跑完整测试、smoke test、build，再发布 v0.3.6。

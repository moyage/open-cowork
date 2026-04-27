# V0.3.1 Final Retrospective and Closeout Report

Change: `v0.3.1-human-participation-runtime`
版本：`0.3.1`
状态：Step 9 已归档，当前项目回到 `idle`
归档时间：`2026-04-27T00:53:58.871286+00:00`
归档入口：`.governance/archive/v0.3.1-human-participation-runtime/archive-receipt.yaml`

## 1. 轮次信息

本轮主题是 **Human Participation Runtime Hardening**。它承接 V0.3.0 的人类可见 Step 1-9、Step 5 / Step 8 / Step 9 hard gates 和 closeout 可读性能力，针对团队真实 dogfood 反馈中暴露的运行时问题做收束强化。

本轮 authoritative 状态如下：

| 项目 | 结果 |
| --- | --- |
| change id | `v0.3.1-human-participation-runtime` |
| archive | complete |
| review decision | approve |
| final consistency | pass |
| Step 5 gate | approved by `human-sponsor` |
| Step 8 gate | approved by `human-sponsor` |
| Step 9 gate | approved by `human-sponsor` |
| residual followups | none |
| 当前维护状态 | `idle`，最近归档变更为 V0.3.1 |

事实来源：

- `.governance/archive/v0.3.1-human-participation-runtime/archive-receipt.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/review.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/FINAL_STATE_CONSISTENCY_CHECK.yaml`
- `.governance/index/maintenance-status.yaml`
- `.governance/current-state.md`

## 2. 本轮变更汇总

V0.3.1 主要完成了七类运行时强化：

1. **Step 1 intent-only 可见性**
   - 新 change 不再被 `change prepare` 伪装成 Step 1-5 已完成。
   - 在 prepare 前也能生成/查看 intent 与 early step report。

2. **人类可读状态面**
   - 增强 `ocw intent status`、`ocw participants list`、`ocw change status`、`ocw status --last-archive`。
   - Agent 可直接把这些状态面转述给人，而不是要求人记 CLI 或 schema。

3. **review revise loop**
   - Step 8 `revise` 后能重新打开 revision loop。
   - 修订轮次写入 `revision-history.yaml`，避免 review-revise 状态只停留在口头。

4. **human report evidence aggregation**
   - step report 汇总 evidence、verification 和 reviewer runtime evidence。
   - 减少人为了验收而跨多个 YAML 文件追踪事实的成本。

5. **真实独立 review 调度证据**
   - Hermes 被真实调用，但因 provider HTTP 403 quota / pre-consume token failure 失败。
   - 在人已批准 fallback 的前提下，OOSO/OMOC 作为真实本地独立 reviewer 完成 review 与 rereview。
   - reviewer mismatch bypass 被记录到 `human-gates.yaml`、`review.yaml` 和 final consistency summary。

6. **archive 后 idle closeout 可读性**
   - 当前 `ocw status` 在 idle 状态下展示最近归档 closeout 摘要。
   - `ocw status --last-archive` 可直接查看最近 archive、review decision、final consistency 和 human gate summary。

7. **默认扫描排除和噪音控制**
   - contract / review runtime 默认排除 `.git`、`.omx`、`.venv`、`dist`、`node_modules`、`.release`、`.governance/archive`、`.governance/runtime` 等噪音区域。
   - 降低真实个人域实践中的上下文爆炸风险。

关键落地文件包括：

- `src/governance/status_views.py`
- `src/governance/revision.py`
- `src/governance/defaults.py`
- `src/governance/change_prepare.py`
- `src/governance/human_gates.py`
- `src/governance/step_report.py`
- `src/governance/review.py`
- `src/governance/cli.py`
- `tests/test_v031.py`
- `README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/specs/04-change-package-spec.md`
- `docs/specs/13-first-implementation-change-package.md`
- `CHANGELOG.md`
- `pyproject.toml`

## 3. 步骤和阶段信息

### Step 1 / 输入接入与问题定界

输入为团队对 V0.3.0 的真实 dogfood 反馈：人仍然很难判断当前处于哪一步、prepare 是否等价于已完成、review 失败如何恢复、独立 review 是否真实发生。

本步产出：

- `.governance/archive/v0.3.1-human-participation-runtime/STEP1_INPUT_FRAMING_V031.md`
- `intent.md`
- `intent-confirmation.yaml`

结论：Step 1 已由 `human-sponsor` 确认通过。

### Step 2 / 范围锁定

本轮范围锁定为运行时强化，不扩展成新的产品形态或 dashboard。

Scope in：

- `src/governance/**`
- `tests/**`
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- 当前 change evidence

Scope out：

- `.git/**`
- `.omx/**`
- `.venv/**`
- `dist/**`
- `node_modules/**`
- `.release/**`
- `.governance/archive/**`
- `.governance/runtime/**`

结论：Step 2 已由 `human-sponsor` 确认通过。

### Step 3 / 方案塑形

方案采用 additive runtime hardening，不推翻 V0.3.0 的 Step 1-9 框架。核心方向是：

- 保持 open-cowork Agent-first；
- 让 prepare / approve / revise / review / archive 的状态语义更准确；
- 把人需要看的状态投影成人类可读报告；
- 把真实 reviewer runtime evidence 纳入审计链。

结论：Step 3 已由 `human-sponsor` 确认通过。

### Step 4 / 变更包组装

Step 4 完成 requirements、design、tasks、contract、bindings 和 validation objects 组装。执行边界由：

- `.governance/archive/v0.3.1-human-participation-runtime/contract.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/bindings.yaml`

结论：Step 4 已由 `human-sponsor` 确认通过。

### Step 5 / 执行准备

Step 5 human gate 已批准，允许进入 Step 6 实施。审批记录在：

- `.governance/archive/v0.3.1-human-participation-runtime/human-gates.yaml`

结论：Step 5 approved。

### Step 6 / 执行

实施完成后记录了执行证据：

- `.governance/archive/v0.3.1-human-participation-runtime/evidence/execution-summary.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/evidence/changed-files-manifest.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/evidence/file-diff-summary.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/evidence/command-output-summary.yaml`

中途发生一次 Step 8 revise，随后进入 revision round 1。修复点包括：

- approval / lifecycle transition 后刷新 stored step reports；
- verification command 与真实 repo 命令对齐为 `python3 -m unittest discover -s tests`；
- readiness bookkeeping 不再留下错误的 intent / Step 1 blocker。

结论：Step 6 completed。

### Step 7 / 验证

归档内验证结果：

- `.governance/archive/v0.3.1-human-participation-runtime/verify.yaml`：pass
- `.governance/archive/v0.3.1-human-participation-runtime/evidence/test-output-summary.yaml`：`python3 -m unittest discover -s tests => Ran 180 tests OK`

本会话恢复后重新验证：

- `python3 -m unittest discover -s tests -v`：Ran 180 tests OK
- `./bin/ocw version`：`open-cowork 0.3.1`
- `./bin/ocw hygiene --format json`：`state_consistency.status=pass`
- `git diff --check`：pass
- `./bin/ocw status --last-archive`：显示 V0.3.1 archive、review approve、final consistency pass、Step 5/8/9 approved

结论：Step 7 verified。

### Step 8 / 审查与决策

本轮 Step 8 真实调度链如下：

1. **Hermes primary reviewer**
   - 已真实调用 Hermes。
   - Hermes provider 返回 HTTP 403：`pre_consume_token_quota_failed`。
   - 失败证据记录在 `.governance/archive/v0.3.1-human-participation-runtime/evidence/hermes-review/hermes-review-output.md`。

2. **OOSO/OMOC fallback reviewer**
   - 经人批准后，使用 OOSO/OMOC 作为真实本地独立 reviewer。
   - 初次 review decision 为 `revise`。
   - 修订后 OOSO/OMOC rereview decision 为 `approve`。

3. **reviewer mismatch bypass**
   - 因 Step 8 binding 原 reviewer 为 `hermes-reviewer`，实际 approve reviewer 为 `ooso-reviewer`，bypass 已记录。
   - 记录位置包括 `human-gates.yaml`、`review.yaml`、`FINAL_STATE_CONSISTENCY_CHECK.yaml`。

结论：Step 8 approve，且没有伪造 Hermes 审查结论。

### Step 9 / 归档与维护状态更新

Step 9 human approval 已记录，archive 已执行：

- `.governance/archive/v0.3.1-human-participation-runtime/archive-receipt.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/FINAL_STATE_CONSISTENCY_CHECK.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/step-reports/step-9.yaml`

维护状态已刷新：

- `.governance/index/maintenance-status.yaml`：`status: idle`
- `.governance/current-state.md`：最近归档变更为 `v0.3.1-human-participation-runtime`

结论：Step 9 archived。

## 4. 本轮复盘

### 4.1 本轮达成的目标

V0.3.1 达到了本轮核心目标：把 V0.3.0 已经建立的“人类可见流程骨架”继续推到可实践的运行时层面。

具体来说：

- 新 change 不再从 prepare 后被误读为 Step 1-5 已完成。
- 人可以通过 intent、participants、change status、last archive status 看到当前事实。
- Step 8 revise 不再是死状态，能打开 revision loop 并记录修订轮次。
- step report 能聚合 evidence 和 reviewer runtime evidence。
- 独立 review 的真实调度、失败、fallback 和 bypass 都有记录。
- archive 后的 idle 状态可读，不再只剩内部 YAML。

### 4.2 执行域问题

**问题 1：Hermes 真实调度失败，但不能降级为模拟。**

- 现象：Hermes 已真实启动并读取 review contract，但 provider 返回 HTTP 403 quota / pre-consume token failure。
- 根因：Hermes 当前 provider 账户或模型额度不足。
- 影响：不能使用 Hermes 完成本轮 Step 8 primary review。
- 处理：记录 Hermes 失败证据，经人批准后使用 OOSO/OMOC 作为真实本地 fallback reviewer。
- carry-forward：不作为 open-cowork V0.3.1 阻断；应作为本地个人域 Agent 环境维护事项继续跟进。

**问题 2：独立 review fallback 需要显式审计。**

- 现象：Step 8 binding 为 `hermes-reviewer`，实际 reviewer 为 `ooso-reviewer`。
- 根因：primary reviewer 环境失败后走了经人批准的 fallback。
- 影响：如果不记录，会造成 reviewer mismatch 和审计链断裂。
- 处理：写入 `human-gates.yaml` bypass、`review.yaml` runtime evidence、final consistency human gate summary。
- carry-forward：已在本轮闭合；后续仍应保持真实 reviewer 调度证据。

**问题 3：上下文爆炸中断了 Step 9 复盘输出。**

- 现象：另一个会话在 Step 9 最终复盘总结时中断。
- 根因：上下文窗口接近/超过阈值。
- 影响：archive 已完成，但人类可读最终报告未在该会话自然收束。
- 处理：本报告基于 authoritative archive artifacts 和当前工作区重新核验后补齐。
- carry-forward：后续 Step 9 后应优先生成短 closeout，再扩展详细复盘，避免报告阶段再次被上下文拖垮。

### 4.3 open-cowork 框架待观察点

**观察 1：归档后的 `STATUS_SNAPSHOT.yaml` 保留的是归档前 Step 8 视图。**

- 现象：archive 目录中的 `STATUS_SNAPSHOT.yaml` 显示 current_step=8、remaining_steps=[9]。
- 判断：不构成本轮阻断，因为 authoritative archive receipt、Step 9 report、final consistency、maintenance status 和 `ocw status --last-archive` 均显示 Step 9 archived / final consistency pass。
- 风险：审计者若误读 `STATUS_SNAPSHOT.yaml` 为最终状态，会产生困惑。
- 建议：下一轮可考虑让 archive-time status snapshot 明确标注 snapshot stage，或在 archive 后生成 final status snapshot。

**观察 2：Step 9 markdown report 的通用提示仍包含“等待确认”的措辞。**

- 现象：Step 9 report 顶部状态是 archived / approved，但尾部通用段落仍写着等待 human confirmation。
- 判断：不影响机器事实与 archive gate，但影响人类可读性。
- 建议：下一轮可优化 step report formatter，让 archived Step 9 显示“已归档，无下一步”，而不是复用 gate 前通用提示。

## 5. 本轮 close 结论

V0.3.1 已完成本轮预期目标，并已完成 Step 9 archive。

本轮证明了：

- open-cowork 可以把 dogfood 反馈转化为 Step 1-9 内的真实变更闭环。
- 新 change 的早期状态可以从 Step 1 开始对人可见，而不是被 prepare 隐藏。
- review revise 能形成可追踪修订轮次。
- 独立 reviewer 的真实调用、失败和 fallback 可以被审计记录。
- archive 后 idle 状态可以向人展示最近 closeout。

本轮没有证明：

- Hermes provider 环境已恢复可用。
- 所有未来 Agent 环境都能稳定完成真实独立 review。
- closeout / final report 已完全免疫上下文爆炸。
- archive-time snapshot 和 Step 9 markdown wording 已做到零歧义。

当前 residual followups：authoritative archive receipt 中为 `[]`。上面的两个框架观察项不阻断 V0.3.1 close，只建议作为后续候选优化输入。

## 6. 下一轮迭代参考建议

以下只作为下一轮候选输入，不等于下一轮已批准执行方案。下一轮仍必须从自己的 Step 1 / Step 2 重新确认目标、范围、非目标、优先级和验收标准。

### P0

- 修复本地个人域 Hermes provider / quota 环境，确保后续需要 Hermes 独立 review 时能真实完成，而不是每次依赖 fallback。
- 继续保持“真实调度，不模拟”的硬约束：任何 Hermes / OOSO / Openclaw 参与都必须有调用证据。

### P1

- 改善 archive-time final status snapshot，避免 `STATUS_SNAPSHOT.yaml` 与 archive receipt / final consistency 在人类阅读上产生歧义。
- 优化 archived Step 9 report 的 markdown wording，让报告尾部不再出现“等待确认”的通用提示。
- 将 closeout 先短后长：Step 9 archive 后先生成低上下文 final digest，再生成详细复盘。

### P2

- 进一步产品化 human approval options，减少人需要输入长确认句的负担。
- 把 status / participants / intent / closeout 的人类可读视图继续统一成更稳定的 Agent report interface。

## 7. 当前发布边界

本报告确认的是 V0.3.1 change 已完成 Step 9 archive 和复盘补齐。

截至本报告生成时，当前工作区仍存在未提交变更，`v0.3.1` 的正式 release commit / tag 尚未执行。正式发布流程应在本报告之后单独执行，并至少包含：

- 最终测试与 hygiene 检查；
- release commit；
- tag `v0.3.1`；
- 必要的发布说明或归档报告更新。

发布完成后的事实应以 release commit、tag `v0.3.1` 和 `docs/archive/reports/2026-04-27-v031-release-and-next-dogfood.md` 为准。

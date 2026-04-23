# open-cowork Milestone 2 Boundary Hardening Round 2 实施计划

## 1. 文档目的

本实施计划用于指导 `Milestone 2` 中 `治理保留区写边界 + 索引状态不可回退` 的最小实现。

目标不是做完整的安全执行层，而是先把：

1. executor 对治理保留区的误写
2. 同一 change 的索引状态回退

收成可测试、可解释、可继续扩展的一层约束。

## 2. 目标

本轮实现完成后，应具备：

1. `run_change(...)` 阻断治理保留区 artifacts
2. `set_current_change(...)` 的最小回退保护
3. `upsert_change_entry(...)` 的最小回退保护
4. 对应单元测试与回归验证

## 3. 范围

### 3.1 纳入

1. 保留区路径规则
2. change truth-source YAML 阻断
3. 索引更新单调性检查
4. 测试与索引文档更新

### 3.2 不纳入

1. OS 级真实写拦截
2. 复杂状态机图
3. `maintenance-status` 全量不可逆规则
4. 新的 CLI 命令面

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/run.py`
   - 增加治理保留区写边界检查
2. `src/governance/index.py`
   - 增加 current/index 状态回退保护
3. `tests/test_run.py`
   - 新增保留区写边界失败测试
4. `tests/test_governance_index.py`
   - 新增索引回退保护测试
5. `docs/README.md`
   - 接入索引

## 5. 设计约束

实现时必须遵守：

1. 不改变现有 CLI 入口。
2. 不影响 archive 后清空 active change 的行为。
3. 不为 continuity / sync 对象新增新的 truth-source。
4. 未知状态下宁可保守放宽同 step 细排序，也不要误阻断不同 change 的正常切换。

## 6. 推荐实现步骤

### Step 1. 先写 run.py 的失败测试

新增建议：

1. 阻断 `.governance/index/**`
2. 阻断 `.governance/runtime/**`
3. 阻断 `.governance/archive/**`
4. 阻断 `.governance/changes/<change-id>/*.yaml`

### Step 2. 实现保留区匹配逻辑

建议新增：

1. `_ensure_governance_reserved_boundaries(...)`
2. `_is_reserved_governance_artifact(...)`

### Step 3. 先写 index.py 的失败测试

新增建议：

1. `set_current_change` 拒绝同 change 的 step 回退
2. `upsert_change_entry` 拒绝同 change 的 step 回退
3. 不同 change 切换允许
4. idle 清空允许

### Step 4. 实现最小状态顺序与回退保护

建议新增：

1. `_ensure_non_regressive_change_state(...)`
2. `_compare_change_position(...)`
3. `_status_rank(...)`

### Step 5. 更新文档索引

接入：

1. `20-milestone2-boundary-hardening-design.md`
2. `21-milestone2-boundary-hardening-implementation-plan.md`

## 7. 测试命令

先定向：

```bash
python3 -m unittest tests.test_run tests.test_governance_index -v
```

再全量：

```bash
python3 -m unittest discover -s tests -v
```

## 8. 退出条件

满足以下条件即可视为本轮成立：

1. `executor` 无法通过 artifacts 声明写入治理保留区
2. 同一 change 的 `current-change` / `changes-index` 不能被低阶状态覆盖
3. archive 清空 active change 行为不受影响
4. 全量测试通过

## 9. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. `maintenance-status` 的进一步不可逆约束
2. 更细的 truth-source / artifact boundary
3. 更强的真实写边界探针

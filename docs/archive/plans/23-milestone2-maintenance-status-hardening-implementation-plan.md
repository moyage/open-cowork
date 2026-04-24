# open-cowork Milestone 2 Maintenance Status Hardening 实施计划

## 1. 文档目的

本实施计划用于指导 `maintenance-status` 第二轮硬边界的最小实现。

目标不是重写维护模型，而是先把：

1. 同活动 change 姿态回退
2. 最近归档基线空写回退

收成可测试、可解释、可继续扩展的一层约束。

## 2. 目标

本轮实现完成后，应具备：

1. `set_maintenance_status(...)` 的同 change 不可回退保护
2. `last_archived_change / last_archive_at` 的最小 sticky 保护
3. 对应单元测试
4. 文档索引与 Baseline 同步

## 3. 范围

### 3.1 纳入

1. `status/current_change_active` 单调推进
2. recent archive baseline sticky
3. 测试与文档

### 3.2 不纳入

1. `maintenance-status` 完整状态机
2. `archive-map` 交叉强一致校验
3. `residual_followups` 语义治理
4. 新 CLI 命令

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/index.py`
   - 扩展 `set_maintenance_status(...)`
2. `tests/test_governance_index.py`
   - 新增 maintenance-status 回退保护测试
3. `docs/README.md`
   - 接入索引

## 5. 设计约束

实现时必须遵守：

1. archive 的 `idle/none` 清空行为不受影响；
2. 不同 `change_id` 的切换不应被误阻断；
3. 未知状态下保守跳过细排序，不误伤现有流程；
4. sticky 保护只针对显式空写，不影响正常 merge 保留现值。

## 6. 推荐实现步骤

### Step 1. 先写 maintenance-status 失败测试

新增建议：

1. 同 change 的 `status` 回退失败
2. 同 change 的 `current_change_active` 回退失败
3. `last_archived_change=None` 失败
4. `last_archive_at=None` 失败

### Step 2. 补合法例外测试

新增建议：

1. 不同 `change_id` 切换允许
2. `idle/none` 清空允许
3. 新的非空归档基线覆盖允许

### Step 3. 实现 `set_maintenance_status(...)` 保护逻辑

建议新增：

1. `_ensure_non_regressive_maintenance_status(...)`
2. `_ensure_sticky_archive_baseline(...)`
3. `_status_rank(...)` 对 `idle/draft` 的兼容映射

### Step 4. 回归验证

先定向：

```bash
python3 -m unittest discover -s tests -p 'test_governance_index.py' -v
```

再全量：

```bash
python3 -m unittest discover -s tests -v
```

## 7. 退出条件

满足以下条件即可视为本轮成立：

1. `maintenance-status` 的同 change 活动态不能回退
2. 最近归档基线不能被显式空写抹掉
3. archive / 新 change 激活等正常流转仍通过
4. 全量测试通过

## 8. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. 更细的 `truth-source / artifact boundary`
2. `archive-map` 与 `maintenance-status` 的交叉一致性
3. 更强的 lifecycle 不可逆约束

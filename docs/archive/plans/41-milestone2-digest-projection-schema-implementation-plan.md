# open-cowork Milestone 2 Digest Projection Schema 实施计划

## 1. 文档目的

本实施计划用于指导 `continuity digest` 中显式 projection schema 的最小实现。

## 2. 本轮目标

完成后应具备：

1. `resolve_continuity_digest(...)` 输出 `projection_sources`
2. active / archived 两种摘要路径都支持
3. 不新增新的事实文件

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `tests/test_continuity.py`
3. `docs/README.md`

### 3.2 不纳入

1. digest CLI 新输出格式
2. 全字段 lineage
3. schema validator

## 4. 设计约束

1. `projection_sources` 只能声明来源，不能形成新的权威层。
2. 若某字段是降级推导值，也必须写明真实来源。
3. 仍然保持 digest 为只读派生层。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_resolve_continuity_digest_active_includes_projection_sources`
2. `test_resolve_continuity_digest_archived_includes_projection_sources`

### Step 2. 实现 helper

建议新增：

1. `_active_digest_projection_sources(...)`
2. `_archived_digest_projection_sources(...)`

### Step 3. 接入 digest

1. active payload 挂入 `projection_sources`
2. archived payload 挂入 `projection_sources`

### Step 4. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. digest 关键镜像字段具备明确来源映射
2. active / archived 两条路径都覆盖
3. 全量测试通过

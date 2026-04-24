# open-cowork Milestone 2 Truth-Source / Artifact Boundary Hardening 实施计划

## 1. 文档目的

本实施计划用于指导 `.governance/changes/**` 包体边界的最小实现。

目标不是重做整个执行权限系统，而是先把：

1. `.governance/changes/**` 作为治理包体保留区
2. `executor` 不能直接声明写入 change package

做成可测试、可解释、可继续扩展的一层约束。

## 2. 目标

本轮实现完成后，应具备：

1. `run_change(...)` 阻断 `.governance/changes/**`
2. 新增对应失败测试
3. 文档索引与 Baseline 同步

## 3. 范围

### 3.1 纳入

1. change package subtree reserved rule
2. run.py 保留区逻辑收紧
3. test_run.py 定向测试

### 3.2 不纳入

1. 真实写探针
2. executor 可写例外目录设计
3. contract schema 变更
4. 新 CLI 命令

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/run.py`
   - 收紧保留区判定
2. `tests/test_run.py`
   - 新增 `.governance/changes/**` 阻断测试
3. `docs/README.md`
   - 接入索引

## 5. 设计约束

实现时必须遵守：

1. 规则应简单明确，不再按后缀零散判断；
2. 不影响治理层自己写入 `.governance/changes/**`；
3. 不影响 repo 工作目录正常执行产物；
4. 不引入新配置项。

## 6. 推荐实现步骤

### Step 1. 先写失败测试

新增建议：

1. `.governance/changes/<id>/tasks.md`
2. `.governance/changes/<id>/requirements.md`
3. `.governance/changes/<id>/evidence/manual-note.txt`

### Step 2. 收紧 `run.py`

建议：

1. 在 `_is_reserved_governance_artifact(...)` 中把 `.governance/changes/` 整体视为保留区
2. 删除“仅 YAML”这一狭窄判断

### Step 3. 回归验证

先定向：

```bash
python3 -m unittest discover -s tests -p 'test_run.py' -v
```

再全量：

```bash
python3 -m unittest discover -s tests -v
```

## 7. 退出条件

满足以下条件即可视为本轮成立：

1. `executor` 无法声明写入任何 `.governance/changes/**` 文件
2. 现有 repo 工作目录写入不受影响
3. 全量测试通过

## 8. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. `archive-map` 与 `maintenance-status` 的交叉一致性
2. 更细的 continuity / closeout / sync refs 约束

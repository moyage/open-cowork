# open-cowork Milestone 2 Closeout Packet 实施计划

## 1. 文档目的

本实施计划用于指导 `Milestone 2 / continuity primitives` 中 `closeout-packet` 的最小实现。

目标不是重建旧式 closeout 文档大包，而是先把：

- archive 后的正式收束入口
- continuity primitives 的 round 级 closure 桥接
- 后续 `sync / escalation packet` 的稳定上游输入

做成一个可运行、可测试、可被人和 agent 消费的最小能力包。

## 2. 目标

本轮实现完成后，应具备：

1. `resolve_closeout_packet(...)`
2. `materialize_closeout_packet(...)`
3. `ocw continuity closeout-packet --change-id ...`
4. `.governance/archive/<change-id>/closeout-packet.yaml`
5. 对 archived change 的最小测试覆盖

## 3. 范围

### 3.1 纳入

1. closeout packet schema 落地
2. archive receipt / archived artifacts 读取逻辑
3. continuity refs 拼装逻辑
4. CLI 参数解析与最小校验
5. 单元测试与 CLI 测试

### 3.2 不纳入

1. 外部 closeout directory 自动导出
2. 多文档 closeout package 生成
3. sync / escalation packet
4. closeout packet update / publish / merge
5. timeline 深度汇总分析

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/continuity.py`
   - 新增 closeout packet 解析与落盘逻辑
2. `src/governance/cli.py`
   - 新增 `continuity closeout-packet` 子命令
3. `src/governance/paths.py`
   - 新增 archived closeout packet 路径函数
4. `tests/test_continuity.py`
   - 新增 closeout packet 单元测试
5. `tests/test_cli.py`
   - 新增 closeout packet CLI 测试
6. `docs/README.md`
   - 接入新文档索引

### 4.2 可选修改

1. `docs/reports/01-status-report.md`
   - 在 closeout packet 落地后补一条状态更新

## 5. 设计约束

实现时必须遵守：

1. closeout packet 只服务已 archive 的 change。
2. closeout packet 必须写入 archive 目录，而不是 change draft 目录。
3. 所有 closure 摘要字段都必须能回指到 archived artifacts。
4. `handoff / owner-transfer / increment` 仅作为可选 refs，不得成为强依赖。
5. 不得把 closeout packet 实现成新的 truth-source。
6. 不得把旧式 5 份 closeout 文档包逻辑重新硬编码进本轮实现。

## 6. 推荐实现步骤

### Step 1. 扩展路径层

在 `paths.py` 中新增：

- `closeout_packet_file(change_id: str) -> Path`

建议输出到：

```text
.governance/archive/<change-id>/closeout-packet.yaml
```

### Step 2. 在 continuity.py 中新增 closeout packet 原语

建议新增：

1. `resolve_closeout_packet(...)`
2. `materialize_closeout_packet(...)`

其中：

- `resolve_closeout_packet(...)`
  - 负责校验 archive 状态
  - 读取 archive receipt / archived artifacts
  - 组装 payload
- `materialize_closeout_packet(...)`
  - 调用 resolve
  - 将结果写入 archive 目录

### Step 3. 组装最小 payload

建议 payload 组装顺序：

1. 读取 archive receipt
2. 读取 archived manifest / contract / verify / review
3. 构建 `closure_summary`
4. 写入 CLI 提供的 `result_summary / continuity_bridge / human_reading_entry`
5. 收集 refs
6. 如果存在：
   - `handoff-package.yaml`
   - `owner-transfer-continuity.yaml`
   - `increment-package.yaml`
   则追加到 refs

### Step 4. 新增 CLI 命令

建议新增：

```bash
ocw continuity closeout-packet ...
```

最小支持参数：

1. `--change-id`
2. `--closeout-statement`
3. `--delivered-scope`（多值）
4. `--deferred-scope`（多值）
5. `--key-outcome`（多值）
6. `--unresolved-item`（多值）
7. `--next-direction`
8. `--attention-point`（多值）
9. `--carry-forward-item`（多值）
10. `--operator-summary`
11. `--sponsor-summary`

### Step 5. 单元测试

建议至少新增以下测试：

1. `test_materialize_closeout_packet_for_archived_change`
2. `test_closeout_packet_rejects_non_archived_change`
3. `test_closeout_packet_requires_archive_receipt`
4. `test_closeout_packet_omits_optional_continuity_refs_when_missing`
5. `test_closeout_packet_includes_optional_continuity_refs_when_present`

### Step 6. CLI 测试

建议新增以下测试：

1. `test_continuity_closeout_packet_command_materializes_output`
2. `test_closeout_packet_command_fails_for_non_archived_change`

## 7. 测试命令

本轮最小验证命令：

```bash
python3 -m unittest discover -s tests -v
```

如需聚焦回归，可优先跑：

```bash
python3 -m unittest tests.test_continuity tests.test_cli -v
```

## 8. 退出条件

满足以下条件即可视为本轮 closeout packet 最小能力包成立：

1. 可以为 archived change 成功生成 `closeout-packet.yaml`
2. 未 archive 的 change 无法冒充 closeout packet
3. continuity 可选 refs 的有无不会破坏主流程
4. 全量测试通过
5. 文档索引已更新

## 9. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. `sync / escalation packet` 设计
2. 让 `sync / escalation packet` 优先复用：
   - `closeout-packet`
   - `increment-package`
   - `runtime timeline`
3. 保持项目级 closeout 与更高层消费面之间的语义边界

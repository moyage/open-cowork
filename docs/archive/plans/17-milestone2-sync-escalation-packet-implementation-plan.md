# open-cowork Milestone 2 Sync / Escalation Packet 实施计划

## 1. 文档目的

本实施计划用于指导 `Milestone 2 / continuity primitives` 中 `sync-packet` 的最小实现。

目标不是立刻做上层治理系统，而是先把：

- 项目级 closeout / increment 结果
- 面向更高层的统一同步入口
- routine sync 与 escalation 的最小统一结构

落成一个可运行、可测试、可被外部消费的协议切片。

## 2. 目标

本轮实现完成后，应具备：

1. `resolve_sync_packet(...)`
2. `materialize_sync_packet(...)`
3. `ocw continuity sync-packet --change-id ...`
4. `sync-packet.yaml` 输出到正确目录
5. 对 closeout / increment 两类 source anchor 的最小测试覆盖

## 3. 范围

### 3.1 纳入

1. `sync-packet` schema 落地
2. `source-kind` 分流逻辑
3. `sync-kind` 与 escalation 规则
4. CLI 参数解析与最小校验
5. 单元测试与 CLI 测试

### 3.2 不纳入

1. 上层系统真实投递
2. 多目标同步
3. history 聚合
4. acknowledge / resolve lifecycle
5. UI / dashboard

## 4. 文件范围

### 4.1 预计修改

1. `src/governance/paths.py`
   - 新增 sync packet 路径函数
2. `src/governance/continuity.py`
   - 新增 sync packet 解析与落盘逻辑
3. `src/governance/cli.py`
   - 新增 `continuity sync-packet` 子命令
4. `tests/test_continuity.py`
   - 新增 sync packet 单元测试
5. `tests/test_cli.py`
   - 新增 sync packet CLI 测试
6. `docs/README.md`
   - 接入新文档索引

## 5. 设计约束

实现时必须遵守：

1. `sync-packet` 必须复用 `closeout-packet` 或 `increment-package` 作为 source anchor。
2. 不得直接把 `sync-packet` 实现成对全部 archived artifacts 的重新打包。
3. `sync-kind = escalation` 时必须显式要求 attention / decision 请求。
4. 输出路径必须与 `source-kind` 一致。
5. `sync-packet` 是对上消费摘要层，不是新的项目级 truth-source。

## 6. 推荐实现步骤

### Step 1. 扩展路径层

在 `paths.py` 中新增：

- `sync_packet_file(change_id: str, *, source_kind: str) -> Path`

建议规则：

1. `source_kind = increment` -> `.governance/changes/<change-id>/sync-packet.yaml`
2. `source_kind = closeout` -> `.governance/archive/<change-id>/sync-packet.yaml`

### Step 2. 在 continuity.py 中新增 sync packet 原语

建议新增：

1. `resolve_sync_packet(...)`
2. `materialize_sync_packet(...)`

### Step 3. 组装最小 payload

建议 payload 组装顺序：

1. 识别 `source_kind`
2. 读取 source anchor payload
3. 写入 `target_context`
4. 写入 `sync_summary`
5. 写入 `continuity_bridge`
6. 收集 refs

### Step 4. 新增 CLI 命令

建议新增：

```bash
ocw continuity sync-packet ...
```

最小支持参数：

1. `--change-id`
2. `--source-kind closeout|increment`
3. `--sync-kind routine-sync|escalation`
4. `--target-layer`
5. `--target-scope`
6. `--urgency`
7. `--headline`
8. `--delivered-scope`（多值）
9. `--pending-scope`（多值）
10. `--requested-attention`（多值）
11. `--requested-decision`（多值）
12. `--next-owner-suggestion`
13. `--next-action-suggestion`

### Step 5. 单元测试

建议至少新增以下测试：

1. `test_materialize_sync_packet_from_closeout_anchor`
2. `test_materialize_sync_packet_from_increment_anchor`
3. `test_sync_packet_requires_attention_or_decision_for_escalation`
4. `test_sync_packet_omits_optional_owner_transfer_ref_when_missing`
5. `test_sync_packet_uses_correct_output_path_for_source_kind`

### Step 6. CLI 测试

建议新增以下测试：

1. `test_continuity_sync_packet_command_materializes_output_from_closeout`
2. `test_continuity_sync_packet_command_materializes_output_from_increment`
3. `test_sync_packet_command_fails_for_invalid_escalation_payload`

## 7. 测试命令

本轮最小验证命令：

```bash
python3 -m unittest discover -s tests -v
```

如需聚焦回归，可优先跑：

```bash
python3 -m unittest discover -s tests -p 'test_continuity.py' -v
python3 -m unittest discover -s tests -p 'test_cli.py' -v
```

## 8. 退出条件

满足以下条件即可视为本轮 sync packet 最小能力包成立：

1. 可从 `closeout-packet` 成功生成 `sync-packet`
2. 可从 `increment-package` 成功生成 `sync-packet`
3. escalation 规则被最小校验
4. 输出路径符合 source-kind 语义
5. 全量测试通过

## 9. 下一步衔接

本轮完成后，下一段最自然的方向是：

1. sync history / external export
2. 更高层只读消费接口
3. closeout / sync 的人类默认阅读入口整合

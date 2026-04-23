# open-cowork Milestone 2 Sync History And External Export 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 中 `sync-packet` 的下一段能力收口为：

> `sync history + external export`

它回答的问题不是“如何马上把 sync-packet 接到真实上层系统”，而是：

- 每次生成 `sync-packet` 后，项目内如何保留一条 append-only 的同步轨迹；
- 当操作者需要把某次同步结果带出项目仓库时，如何以低摩擦、显式触发的方式导出；
- 如何让后续更高层消费和外部只读系统，建立在稳定协议层之上，而不是直接扫本地运行目录。

## 2. 设计目标

本轮目标如下：

1. 为 `sync-packet` 建立项目内最小 `sync history`。
2. 为 `sync-packet` 建立显式触发的 `external export` 能力。
3. 保持：
   - history 是 append-only 的内部记录层；
   - export 是显式导出层；
   - 两者都不替代 `sync-packet` 本身。
4. 为后续更高层只读消费接口保留兼容空间。

## 3. 边界

### 3.1 本轮纳入

1. `sync history` schema
2. `sync-packet` 物化时写入 history
3. 显式 `export-sync-packet` CLI
4. 最小外部导出目录结构
5. 最小测试建议

### 3.2 本轮明确不做

1. 自动投递到远端系统
2. message / email / issue / webhook 分发
3. sync history 可视化面板
4. 外部目录自动 watch 或自动刷新
5. 上层系统真实 ack / resolve lifecycle

### 3.3 但必须兼容

1. 更高层只读系统直接消费导出目录
2. 后续 `sync history list` / query 命令
3. 多次 export 到同一外部目录
4. sponsor / ecosystem operator 的默认阅读入口

## 4. 推荐方案

推荐采用：

> `append-only sync history + explicit export packet`

也就是：

1. 每次 `materialize_sync_packet(...)` 后，向项目内 history 追加一条记录；
2. 需要导出时，由显式 CLI 命令触发 export；
3. export 只复制：
   - `sync-packet.yaml`
   - 一个简短 `README.md`
   - 一个 `export-manifest.yaml`
4. export 不改变项目内 authoritative state。

不推荐：

1. 物化 sync-packet 时自动导出到外部目录  
   - 容易把本地试验和正式对外同步混在一起。
2. 只做 external export，不做 history  
   - 会丢失项目内的同步轨迹。
3. 直接把整个 `.governance/archive/` 或 `.governance/changes/` 复制到外部目录  
   - 会让外部消费面过重，也会模糊 truth-source 边界。

## 5. 建议结构

### 5.1 项目内 sync history

建议新增：

```text
.governance/runtime/sync-history/events-YYYYMM.yaml
```

它属于：

- 项目内 append-only 同步历史层
- 记录每次 `sync-packet` 生成的最小摘要

### 5.2 外部导出目录

建议导出后生成：

```text
<output-dir>/<change-id>/
  README.md
  export-manifest.yaml
  sync-packet.yaml
```

说明：

1. `<output-dir>` 由操作者显式指定；
2. 本轮不强加固定外部目录命名；
3. 外部目录不是 open-cowork 内置 truth-source。

## 6. authoritative source 与生成规则

### 6.1 sync history 核心来源

1. `sync-packet.yaml`
2. `runtime timeline`（仅引用）

### 6.2 external export 核心来源

1. 已存在的 `sync-packet.yaml`
2. 可选读取 `closeout-packet` 或 `increment-package`，仅用于写 README 摘要

### 6.3 生成原则

1. `sync history` 是 append-only 记录层，不允许覆盖旧事件。
2. 每条 history entry 都必须回指到一个明确的 `sync-packet` 路径。
3. external export 只在显式命令触发时进行。
4. external export 只导出上层消费所需的最小集，不复制完整项目事实层。
5. external export 的 README 只能是说明层，不能替代 packet 本身。

## 7. 最小 schema

### 7.1 sync history

```yaml
schema: sync-history/v1
month: 202604
events:
  - event_id: CHG-20260424-001-sync-20260424T120000Z
    change_id: CHG-20260424-001
    recorded_at: 2026-04-24T12:00:00Z
    sync_kind: escalation
    source_kind: closeout
    target_layer: sponsor
    target_scope: project-level
    packet_ref: .governance/archive/CHG-20260424-001/sync-packet.yaml
    headline: 项目级 continuity primitives 已闭环，建议进入更高层同步阶段
```

### 7.2 export manifest

```yaml
schema: sync-export-manifest/v1
change_id: CHG-20260424-001
exported_at: 2026-04-24T12:05:00Z
source_sync_packet: .governance/archive/CHG-20260424-001/sync-packet.yaml
export_dir: /abs/path/to/output/CHG-20260424-001
files:
  - README.md
  - export-manifest.yaml
  - sync-packet.yaml
```

## 8. 最小 CLI 设计

建议新增两条命令：

```bash
ocw continuity sync-history --change-id CHG-20260424-001 --source-kind closeout
ocw continuity export-sync-packet --change-id CHG-20260424-001 --source-kind closeout --output-dir /abs/path/to/export-root
```

### 8.1 `sync-history`

职责：

1. 基于已存在的 `sync-packet` 追加一条 history event；
2. 如果同一 packet 已记录，则避免重复追加；
3. 输出 history 文件路径。

### 8.2 `export-sync-packet`

职责：

1. 读取已存在的 `sync-packet`；
2. 在目标目录下创建 `<change-id>/`；
3. 写入：
   - `sync-packet.yaml`
   - `README.md`
   - `export-manifest.yaml`
4. 输出导出目录路径。

## 9. 最小生命周期

### 9.1 sync history

1. `append`
   - 读取 sync-packet
   - 追加 history entry

### 9.2 external export

1. `materialize-export`
   - 读取 sync-packet
   - 生成导出目录结构

本轮明确不做：

1. `list`
2. `acknowledge`
3. `diff-export`
4. `auto-refresh`

## 10. 最小测试建议

建议至少覆盖：

1. 生成 sync-packet 后可写入 history
2. 重复写同一 packet 时不会重复追加
3. 可从 closeout-anchor packet 导出到外部目录
4. 可从 increment-anchor packet 导出到外部目录
5. export 不存在 source packet 时失败
6. export 只导出最小文件集

## 11. 价值

这份设计的价值在于：

1. 让 sync-packet 不只是一次性产物，而有项目内历史轨迹；
2. 让外部消费从“直接读仓库内部路径”升级为“显式导出包”；
3. 为后续更高层只读消费接口与 sync history 查询能力打基础；
4. 继续保持项目级协议层与外部分发层的边界清晰。

# open-cowork Change Package 规范

## 1. 目标
定义 change package 作为 open-cowork 的最小治理工作单元，确保其可独立评审、执行、验证、归档。

## 2. 标识规则
建议格式：`CHG-YYYYMMDD-序号`，例如 `CHG-20260420-001`。

## 3. 最小目录结构
```text
changes/<change-id>/
  intent.md
  requirements.md
  design.md
  tasks.md
  contract.yaml
  evidence/
  verify.yaml
  review.yaml
  bindings.yaml
  manifest.yaml
```

## 4. 文件职责
### 必填
- `intent.md`：问题背景、目标、边界、非目标。
- `requirements.md`：功能/治理/审计要求与约束。
- `design.md`：本 change 的方案塑形，不得重定义顶层目标。
- `tasks.md`：可执行任务拆解与阶段顺序。
- `contract.yaml`：执行契约。
- `manifest.yaml`：文件清单、状态、版本、档位。

### 阶段性必填
- `bindings.yaml`：进入 Step 5 时必须存在。
- `verify.yaml`：进入 Step 7 时必须存在。
- `review.yaml`：进入 Step 8 时必须存在。
- `evidence/`：进入 Step 6 后必须持续写入。

## 5. 核心关系
- intent 回答“为什么做”。
- requirements 回答“必须满足什么”。
- design 回答“准备怎么做”。
- tasks 回答“按什么顺序执行”。
- contract 回答“执行者被允许做什么、必须产出什么”。
- evidence 回答“执行期间客观发生了什么”。
- verify 回答“结果是否达标”。
- review 回答“是否批准进入下一状态”。

## 6. Lite / Standard / Strict 裁剪
| 项目 | Lite | Standard | Strict |
|---|---|---|---|
| requirements 明细度 | 精简 | 标准 | 完整且含风险项 |
| design 深度 | 可简述 | 标准设计说明 | 必须含替代方案与边界分析 |
| tasks 粒度 | 粗粒度 | 中粒度 | 细粒度 + gate 点 |
| verify 字段 | 最小 | 标准 | 完整含 blocker taxonomy |
| review 决策 | reviewer 通过 | reviewer + sponsor | reviewer + sponsor + 明确审批痕迹 |
| evidence 附件 | 最少必需 | 常规完整 | 完整可审计 |

## 7. manifest.yaml 建议结构
```yaml
change_id: CHG-20260420-001
title: 规格化阶段主干文档建立
policy_level: standard
status: drafting
current_step: 1
owner: orchestrator
files:
  required:
    - intent.md
    - requirements.md
    - design.md
    - tasks.md
    - contract.yaml
    - manifest.yaml
  optional:
    - bindings.yaml
    - verify.yaml
    - review.yaml
```

说明：v0.3.1 起，新 change package 默认从 `current_step: 1` 开始，表示输入接入与问题定界尚需对人可见确认。`change prepare` 可以生成 Step 3-5 所需材料，但不能把 Step 1-5 伪装成已完成。

## 8. 独立 review 条件
一个 change package 只有在以下条件满足时才可进入独立 review：
- 顶层边界明确。
- contract 可执行。
- evidence 目录已存在并可持续写入。
- verify 与 review 的结构预留完成。

## 9. 禁止事项
- 把 change package 简化成单一 TODO 列表。
- 没有 contract 就进入执行。
- 没有 evidence 目录就声称已完成执行。
- 将个人域某个具体工具或实例写死为通用结构。

# open-cowork Executor Adapter Interface 规格

## 1. 目标
定义 open-cowork 在 MVP 中接入执行器的最小适配接口。该接口服务于治理框架，不把任何具体 agent 名硬编码为内核。

## 2. 设计原则
- adapter 是执行适配层，不是治理核心层。
- MVP 只要求一个真实 adapter，但接口必须可扩展。
- adapter 必须接受 execution contract，而不是接受模糊自然语言直接开跑。
- adapter 必须返回 evidence 所需的结构化结果。

## 3. 输入接口
```yaml
adapter_request:
  adapter_type: generic
  change_id: CHG-20260420-001
  contract_path: .governance/changes/CHG-20260420-001/contract.yaml
  working_directory: /path/to/sandbox
  policy_level: standard
  allowed_write_scope:
    - docs/**
  timeout_seconds: 1800
```

## 4. 输出接口
```yaml
adapter_response:
  status: success
  run_id: run-001
  started_at: 2026-04-20T15:00:00Z
  ended_at: 2026-04-20T15:20:00Z
  artifacts:
    created:
      - docs/specs/01-prd.md
    modified: []
  evidence_refs:
    - evidence/summary.yaml
  next_action_hint: verify
```

## 5. 最小能力要求
- 读取 contract。
- 在限定 working directory 和 allowed_write_scope 内执行。
- 产出 artifacts created/modified 列表。
- 记录 run_id、起止时间、状态。
- 在失败时返回错误摘要，而不是仅返回空结果。

## 6. 错误模型
- invalid_contract
- scope_violation
- timeout
- execution_failed
- evidence_missing

## 7. 治理边界
adapter 不负责：
- 重写顶层目标
- 最终 review decision
- stable facts 最终写入
- archive 与 index refresh 决策

## 8. MVP 建议
MVP 的首个 adapter 可优先选择文件/命令型适配方式，以验证治理链路本身，而不是追求多平台覆盖。

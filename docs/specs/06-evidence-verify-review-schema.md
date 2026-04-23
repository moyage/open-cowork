# open-cowork Evidence / Verify / Review Schema 规范

## 1. 目标
建立执行证据、验证结果、审查决策的最小结构化 schema，确保“evidence over claims”。

## 2. execution evidence
### 2.1 最小字段
```yaml
schema: execution-evidence/v1
change_id: CHG-20260420-001
step: 6
actor:
  role: executor
  id: adapter-1
activity:
  summary: 生成规格文档
  started_at: 2026-04-20T15:00:00Z
  ended_at: 2026-04-20T15:20:00Z
artifacts:
  created:
    - docs/specs/01-prd.md
  modified: []
attachments:
  - type: file-diff
    path: evidence/diff.txt
  - type: command-output
    path: evidence/output.log
result:
  status: success
  notes: 未进入工程执行
```

### 2.2 证据类型
- file_write_record
- file_diff
- command_output
- test_output
- screenshot_or_capture
- review_note_reference
- archive_receipt

## 3. verify result
### 3.1 最小字段
```yaml
schema: verify-result/v1
change_id: CHG-20260420-001
verifier:
  role: verifier
  id: verifier-1
checks:
  - id: boundary
    description: 未扩大MVP且未进入实现
    status: pass
  - id: completeness
    description: P0主干文档已落盘
    status: pass
summary:
  status: pass
  blocker_count: 0
  major_count: 0
  minor_count: 1
issues:
  - severity: minor
    title: 部分扩展schema待后续工程化补全
```

### 3.2 缺陷等级
- blocker：阻止进入下一 gate。
- major：不建议进入下一 gate，需明确豁免或整改。
- minor：可带入下一轮。
- note：仅记录。

## 4. review decision
### 4.1 最小字段
```yaml
schema: review-decision/v1
change_id: CHG-20260420-001
reviewers:
  - role: reviewer
    id: reviewer-1
decision:
  status: approve
  rationale: 主干规格齐备，边界未漂移
conditions:
  must_before_next_step:
    - 进入工程执行前补齐 adapter interface 细化稿
  followups:
    - 建立首个执行 change package
trace:
  evidence_refs:
    - evidence/summary.yaml
  verify_refs:
    - verify.yaml
```

### 4.2 decision 状态
- approve
- approve_with_conditions
- revise
- reject

其中以下属于阻断性 decision：
- reject
- revise
- approve_with_conditions 且条件未满足

## 5. 保存规则
- execution evidence 存于 `changes/<id>/evidence/`
- verify result 存于 `changes/<id>/verify.yaml`
- review decision 存于 `changes/<id>/review.yaml`
- archive 后需在归档目录保留完整副本

## 6. 结构化保存要求
以下结果必须结构化保存，不能仅存在对话中：
- 执行动作摘要
- 产物清单
- 验证结论
- 缺陷分级
- 审查决策
- 归档回执

## 7. 审计规则
- 没有 evidence 不能 claim 完成执行。
- verify pass 不等于 review approve。
- review approve 不等于 stable 已更新，仍需 Step 9。

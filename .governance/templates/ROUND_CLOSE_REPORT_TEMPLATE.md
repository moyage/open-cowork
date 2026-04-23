# Round Close Report Template

## 用途
本模板用于每一轮 change / round 完成 Step 9 archive 后，输出一份固定结构的闭环报告。

它的作用不是替代 `.governance/**` authoritative artifacts，而是把本轮：
- 轮次信息
- 变更汇总
- 阶段 / 步骤执行链
- 复盘
- close 结论
- 下一轮迭代参考建议

整理成对人类、后续轮次、以及 external / local closeout directory 都可直接复用的标准化闭环说明。

---

## 输出时机
- 仅在当前 round 已完成 Step 9 archive 后输出
- 如果发生 rollback / rerun，应以最终 authoritative closure 为准
- 如果 round 尚未 archive，只能输出 progress / interim report，不能冒充 round close report

---

## 必填结构

### 1. 轮次信息
至少包含：
- round 编号
- change id
- round 主题
- 开始时间
- 完成时间
- 总时长
- 参与者 / owner / participant
- 最终 authoritative 执行链

### 2. 本轮变更汇总
至少包含：
- 新增需求
- 优化功能
- 修复的 bug / 缺陷
- 本轮落地的关键文件 / 模块 / artifact

### 3. 步骤和阶段信息
按阶段 / step 说明：
- 输入了什么
- 产出了什么
- 做了哪些动作
- 达成了什么目标
- 如果发生 rollback / rerun / invalidation，必须显式写出

### 4. 本轮复盘
必须区分：
- 执行域 / orchestration 问题
- open-cowork 框架本身的待优化 / 待修复问题

每个问题至少说明：
- 现象
- 根因
- 影响
- 处理方式
- 是否 carry-forward

### 5. 本轮 close 结论
至少回答：
- 本轮是否真正完成
- 当前 authoritative 状态是什么
- 本轮证明了什么
- 本轮没有证明什么
- 还剩哪些 residual

### 6. 下一轮迭代参考建议
必须明确：
- 这里只能写参考建议
- 不能把它写成下一轮已确定执行方案
- 下一轮确定性执行方案，必须在下一轮自己的 Step 1 / Step 2 中敲定

建议至少按优先级给出：
- P0: 必须优先修正 / 强化
- P1: 应尽快增强
- P2: 可延后但有价值

---

## 推荐输出顺序
1. 先读 `.governance/archive/<change-id>/archive-receipt.yaml`
2. 再读 archive 下的 `manifest.yaml / verify.yaml / review.yaml / contract.yaml`
3. 再读 `.governance/index/maintenance-status.yaml / changes-index.yaml`
4. 然后生成 round close report
5. 若操作者在个人域保留外层 closeout directory，再把该报告提炼并写入对应目录

---

## 禁止项
- 不得把未 archive 的 round 写成 close report
- 不得把 personal-domain 调度协议写成 open-cowork 项目事实
- 不得把本地个人目录名当成 open-cowork 框架内置术语
- 不得用旧会话残留替代 authoritative artifacts
- 不得省略 rollback / invalidation / rerun 等关键过程
- 不得把外层 closeout package 写成 authoritative project artifact 的替代品

---

## 最小标题骨架
```md
# Round <N> Close Report

## 1. 轮次信息
## 2. 本轮变更汇总
## 3. 步骤和阶段信息
## 4. 本轮复盘
## 5. 本轮 close 结论
## 6. 下一轮迭代参考建议
```

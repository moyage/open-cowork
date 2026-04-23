# Round Close Report And Closeout Package Spec

## 1. 目的
为 open-cowork 定义一个标准化的 round closeout 输出规范。

这份规范解决的不是“每轮多写几份文档”，而是把每轮 Step 9 archive 后最有价值的 closure 信息，压缩成一个固定、低摩擦、可复用的输出面，降低：
- 下一轮重新拼装上下文的成本
- 人类操作者回顾与审计的成本
- authoritative artifacts 与外层复盘资料之间的语义漂移

## 2. 适用条件
本规范只适用于：
- 当前 round 已完成 Step 9 archive
- active change 已结束
- machine-readable maintenance state 已同步完成

未 archive 的轮次，只能输出 progress / interim report，不能冒充 closeout package。

## 3. 术语边界
### 3.1 open-cowork 内置术语
open-cowork 内置的标准术语是：
- round close report
- round closeout package
- external / local closeout directory

### 3.2 非内置术语
操作者可以在本地个人域用任何目录名保存 closeout package。
例如某个本地目录名可以叫 `my-closeouts`，但：
- 这不是 open-cowork 框架内置术语
- 这不是 open-cowork authoritative model 的一部分
- 这不应写入 open-cowork 的框架性规则中作为固有名词

## 4. authoritative truth-source 规则
生成 round close report 与 closeout package 时，事实优先级必须是：
1. `.governance/archive/<change-id>/archive-receipt.yaml`
2. archive 下的 `manifest.yaml / verify.yaml / review.yaml / contract.yaml`
3. `.governance/index/maintenance-status.yaml / changes-index.yaml`
4. Step 6 execution summaries / evidence artifacts
5. 聊天内容仅作为解释层补充，不得覆盖 authoritative artifacts

## 5. 标准 closeout package 结构
每轮 closeout package 固定输出 5 份文档：

### 5.1 README.md
#### 定位
整个 closeout package 的入口索引文件。

#### 必含内容
- 本目录用途
- 覆盖范围
- 阅读顺序
- 权威性说明

#### 消费对象
- Sponsor
- Maintainer
- 下一轮参与者
- 事后回顾者

#### 作为哪个环节输入
- 下一轮启动前的外层导航输入
- 外层检索与回顾入口

---

### 5.2 01-round<N>-close-loop-report.md
#### 定位
本轮唯一的主闭环报告。

#### 必含内容
1. 轮次信息
2. 本轮变更汇总
3. 步骤和阶段信息
4. 本轮复盘
5. 本轮 close 结论
6. 下一轮迭代参考建议

#### 消费对象
- Sponsor
- Maintainer
- 下一轮 Architect / Analyzer / Reviewer

#### 作为哪个环节输入
- 下一轮 Step 1 / Step 2 的高优先级参考输入
- 人类审批前的事实性摘要输入

---

### 5.3 02-round<N>-change-summary-and-evidence-map.md
#### 定位
把本轮关键变更、关键文件、关键 evidence 和 truth-source 优先级收拢成一份索引。

#### 必含内容
- 关键代码与测试对象
- Step 6 / 7 / 8 / 9 关键产物
- evidence chain mapping
- authoritative truth-source priority
- 本轮最重要事实

#### 消费对象
- 验证者
- 维护者
- 后续轮次需要快速追溯事实的人

#### 作为哪个环节输入
- 下一轮 Step 1 / Step 2 的事实层参考输入
- 后续问题定位时的 evidence 索引输入

---

### 5.4 03-round<N>-execution-domain-vs-framework-retrospective.md
#### 定位
把本轮问题拆成两类：执行域问题、框架问题。

#### 必含内容
- 执行域问题
- 框架问题
- 每个问题的现象 / 根因 / 影响 / 处理
- 哪些问题已经闭合，哪些 carry-forward

#### 消费对象
- Sponsor
- Architect
- Maintainer
- 下一轮做 Step 1 / Step 2 定义的人

#### 作为哪个环节输入
- 下一轮 Step 1 / Step 2 的问题输入
- 后续框架增强时的问题边界输入

---

### 5.5 04-round<N+1>-reference-suggestions.md
#### 定位
面向下一轮的参考建议文件。

#### 关键语义
这份文件不是下一轮的确定性执行方案。
它只是：
- 下一轮变更项筛选时的候选建议集合
- 下一轮 Step 1 / Step 2 用于锁定真实范围与真实 change object 的参考输入之一

下一轮的确定性执行方案，必须在下一轮自己的 Step 1 / Step 2 中再正式敲定。

#### 必含内容
- 优先级建议（P0 / P1 / P2）
- 推荐默认方向
- 候选方案骨架
- 明确不做
- 建议的成功标准
- 建议的启动条件

#### 消费对象
- 下一轮 Sponsor
- 下一轮 Architect / Analyzer

#### 作为哪个环节输入
- 下一轮 Step 1 / Step 2 的参考输入
- 不是 Step 5 之后的执行合同替代物

## 6. 项目内置层与外层目录层的关系
### 6.1 项目内置层
open-cowork 项目内应固定存在：
- `.governance/templates/ROUND_CLOSE_REPORT_TEMPLATE.md`
- `docs/specs/13-round-close-report-and-closeout-package-spec.md`

它们负责定义规范与模板。

其中：
- `ROUND_CLOSE_REPORT_TEMPLATE.md` 是项目级固定模板资产
- 它应长期保留在项目内
- 它不要求被复制进每一轮的 closeout package

### 6.2 外层目录层
每轮 closeout 后，可以在操作者自己的 external / local closeout directory 中保存这一轮的 closeout package。

这个外层目录：
- 便于个人域管理与检索
- 不替代 open-cowork 项目内 authoritative artifacts
- 可以按操作者自己的目录习惯命名
- 不要求重复存放项目内置模板副本

## 7. 输出时机与流程
### 7.1 输出时机
- 完成 Step 9 archive 后
- archive receipt 已落盘后
- maintenance state 已同步到 close 后

### 7.2 推荐流程
1. 读取 archive receipt
2. 读取 archive 下的 manifest / verify / review / contract
3. 读取 maintenance-status / changes-index
4. 输出 round close report
5. 输出 change summary and evidence map
6. 输出 execution-domain vs framework retrospective
7. 输出 next-round reference suggestions
8. 在 external / local closeout directory 中写入 README 作为入口

## 8. 禁止项
- 不得把未 archive 的 round 写成 close package
- 不得把 personal-domain 调度协议写成 open-cowork 项目事实
- 不得把 local directory 名称当成 open-cowork 框架内置术语
- 不得把下一轮参考建议写成下一轮已确定执行方案
- 不得省略 rollback / invalidation / rerun 等关键过程
- 不得把外层 closeout package 写成 authoritative project artifact 的替代物

## 9. 价值
这套规范的价值在于：
- 让每轮 close 有固定出口
- 让每轮复盘文档数量被收敛，而不是继续膨胀
- 让“下一轮输入”与“下一轮已定方案”语义分开
- 让项目内置规范与个人域存档目录严格分离

# open-cowork 状态报告（公开仓库基线）

## 1. 当前状态
open-cowork 已完成多轮治理机制验证并沉淀为可复用的治理运行时核心模块。  
当前仓库已整理为“可公开协作”的干净基线：
- 移除历史运行残留（active/archive/index runtime data）
- 保留治理模板、核心代码、测试与规格文档
- 提供可安装 CLI 入口和快速上手文档

## 2. 已完成能力
1. 变更包、合同、证据、验证、审查、归档等核心治理模块实现
2. 关键治理硬化：
   - Step 6 准入控制
   - 执行/审查角色分离校验
   - stable write boundary 防护
   - 状态一致性检查
3. 会话压缩/断连诊断与恢复包机制
4. 基础 CLI 命令：
   - `init`
   - `status`
   - `diagnose-session`
   - `session-recovery-packet`

## 3. 当前限制
1. CLI 主链命令尚未全部产品化（`propose/change/contract/run/verify/review/archive` 仍为占位）
2. 默认 adapter 仍为最小可用实现，尚未扩展到更丰富执行后端
3. 协同状态可视化输出（runtime status/timeline）仍在规格阶段

## 4. 下一步方向
1. 完成 CLI 主链命令的端到端可执行化
2. 强化 adapter 执行能力与审计证据保真度
3. 落地 runtime 状态输出层，提升团队协作可观测性

## 5. 文档边界说明
本报告用于公开仓库状态摘要，不替代 `.governance/` 运行时事实层产物。

# open-cowork 执行计划（公开仓库版本）

## 1. 目标
在保持治理边界稳定的前提下，把当前原型推进为团队可广泛试用的低门槛协作运行时。

## 2. 当前基础
已具备：
1. 治理核心模块（change/contract/evidence/verify/review/archive）
2. 关键治理硬化能力（执行前 gate、角色分离、state consistency、truth-source boundary）
3. 可安装 CLI 与基础命令

## 3. 下一阶段计划

### Phase A：CLI 主链完整化
目标：
- 完成 `propose/change/contract/run/verify/review/archive` 的可执行实现
- 让用户可从 CLI 一条链路走完治理闭环

验收：
- 不再出现 “not fully implemented in MVP” 提示
- 一条命令序列可落盘完整治理产物

### Phase B：Adapter 执行能力增强
目标：
- 提升默认 adapter 的真实执行与审计能力
- 完善错误处理、超时、写入边界和证据保真

验收：
- 可重放关键执行证据
- 边界违规可被稳定阻断

### Phase C：协同可观测输出落地
目标：
- 落地 runtime 状态快照与事件时间线
- 支持团队看板/插件只读消费

验收：
- 输出结构稳定、可解析、可追溯

## 4. 发布节奏建议
1. `v0.2`: CLI 主链完整化
2. `v0.3`: Adapter 强化与证据增强
3. `v0.4`: runtime 状态输出与可观测性增强

## 5. 执行约束
1. 不改变治理骨架（固定 9 步）
2. 不把治理层扩展为重型执行平台
3. 不引入工具链强绑定
4. 文档与实现必须持续对齐

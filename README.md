# open-cowork

`open-cowork` 是一个面向个人域与团队协作的复杂协作底层框架与协议体系。

它不要求你统一 Agent、模型、IDE 或工作流工具，而是用统一的任务入口、角色边界、证据、审查门和接续机制，把多个强个人域或多个 Agent 的工作组织成可分工、可验证、可协同、可持续维护的过程。

## 适合谁

- 个人域中的强执行者，希望把自己的多 Agent / 多 AI Coding 实践接入更稳定的协作结构。
- 多个个人域中的多个“超级个体”，需要围绕复杂项目进行分工、接力和审查。
- sponsor / owner / reviewer / maintainer，需要清楚看到项目状态、风险、判断点和下一步。
- 团队或组织，希望低侵入地统一协作协议，而不是统一每个人的工具链。

## 它提供什么

- change package：把意图、范围、设计、任务和 contract 组织成一个工作单元。
- contract / run / verify / review / archive：形成执行证据与审查门闭环。
- runtime status / timeline：输出机器可读的状态和事件流。
- continuity primitives：handoff、owner transfer、increment、closeout、sync、history、export、digest。
- session recovery：在上下文压缩、会话断裂或 provider drop 时生成诊断和恢复输入。

## 5 分钟开始

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
./scripts/bootstrap.sh
source .venv/bin/activate
ocw --help
./scripts/smoke-test.sh
```

在你的目标项目中初始化：

```bash
cd /path/to/your-project
ocw --root . init
ocw --root . status
ocw --root . diagnose-session
```

更完整的个人域和团队试用说明见：`docs/getting-started.md`。

## 当前状态

当前 `v0.2.1` 文档整理基线建立在 `v0.2.0` 能力之上：

- 主链闭环：`change -> contract -> run -> verify -> review -> archive`。
- runtime status 与 timeline 机器可读输出。
- handoff、owner transfer、increment、closeout、sync、history、export、digest 等 continuity 原语。
- 治理保留区、状态回退、archive anchor、continuity refs 的最小硬化。
- 面向个人域首次试用和团队试用的统一上手入口。

## 文档入口

- `docs/getting-started.md`：唯一上手入口。
- `docs/README.md`：完整文档地图。
- `docs/specs/00-top-level-whitepaper.md`：顶层白皮书。
- `docs/specs/01-prd.md`：产品定义和能力模型。
- `docs/archive/`：历史迭代计划、设计记录、closeout 和复盘材料。

## 贡献与安全

- `CONTRIBUTING.md`：贡献指南。
- `CODE_OF_CONDUCT.md`：行为准则。
- `SECURITY.md`：安全反馈和隐私注意事项。

## 一句话总结

`open-cowork` 不是要替代每个人的个人域，而是让多个强个人域和多个 Agent 在复杂项目中通过统一协议形成高质量协作。

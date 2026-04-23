# Open-Cowork 团队内测启动说明（1页）

本说明面向团队同事在个人域快速试用 `open-cowork`，目标是低门槛进入“多人 / 多 Agent / 多 AI Coding”协同治理流程。

## 1. 这个项目是什么

`open-cowork` 是一个协同治理框架：
- 以分层事实治理为基础（策略、变更、证据、索引）
- 以变更包（change package）为工作单元
- 以执行证据与审查门控制交付质量
- 以低侵入方式接入现有 AI Coding Agent 与工具链

一句话：把“意图 -> 落地产物 -> 可持续维护”做成可审计、可协作、可复用的闭环。

## 2. 你需要准备什么

- Python 3.10+
- Git
- 一个可写的项目目录（个人域）

## 3. 5分钟快速开始

```bash
git clone https://github.com/moyage/open-cowork.git
cd open-cowork
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

验证 CLI：

```bash
ocw --help
```

## 4. 在你的个人域接入（推荐最小路径）

在目标项目根目录执行（或由 Agent 调用）：

```bash
ocw init
ocw create-change --id demo-change --title "First governed change"
ocw run --change demo-change
```

说明：
- `init`：初始化治理目录与索引
- `create-change`：建立变更包
- `run`：按契约执行并产出证据

## 5. 团队协作最小约定

- 每次协作都绑定一个 `change-id`
- 每次执行必须落证据（evidence）
- 未通过审查门（review gate）不得进入 closeout
- closeout 后再进入下一轮迭代

## 6. 推荐阅读顺序

1. `README.md`
2. `docs/QUICKSTART.md`
3. `docs/specs/04-change-package-spec.md`
4. `docs/specs/06-evidence-verify-review-schema.md`
5. `docs/specs/13-round-close-report-and-closeout-package-spec.md`

## 7. 常见问题

- Q: 我只想先试，不想改现有流程？  
  A: 先用 `open-cowork` 做旁路治理，不替换你现有 CI/CD。

- Q: Agent 上下文爆炸怎么办？  
  A: 优先做 round closeout，沉淀结构化证据，再开启下一轮。

- Q: 团队怎么统一口径？  
  A: 用同一套 change package + evidence schema + review gate。

## 8. 内测反馈建议

反馈最有价值的三类问题：
- 执行阻塞点（命令、目录、依赖）
- 证据与审查门不清晰处
- 多人并行协作时的冲突与恢复问题

建议以 Issue 模板提交：场景、复现步骤、预期、实际、日志摘要。

# open-cowork MVP CLI / 入口规格

## 1. 目标
定义 MVP 对外最低可见入口与最小 CLI 命令集，体现“默认简单、内部复杂性内收、低侵入接入”。

本规格的重点不是把完整生命周期一次性暴露给用户，而是让普通用户可以先走默认路径，需要时再逐步进入显式治理命令。

## 2. 用户入口原则
- 默认入口面向“我要创建一个受治理的任务/change”。
- 不要求普通用户先理解状态机、schema、索引层。
- 高级能力后置，通过显式参数或显式命令启用。
- 默认输出应告诉用户“当前在哪一步、下一步做什么”，而不是先展示全部内部结构。
- CLI 可以驱动完整 9 步，但普通用户不应被迫一开始就学习 9 步全部命令。

## 3. 推荐入口
```text
ocw init
ocw propose
ocw change create
ocw contract generate
ocw run
ocw verify
ocw review
ocw archive
ocw status
```

## 4. 命令职责
### ocw init
初始化最低治理目录，不深改现有项目结构。

### ocw propose
把输入转成 intent 草稿与边界说明。

### ocw change create
创建最小 change package 骨架。

### ocw contract generate
根据 intent/requirements/tasks 生成 execution contract 草稿。

### ocw run
调用一个 executor adapter 执行当前 change。
限制：MVP 仅要求支持一个 adapter。

### ocw verify
运行验证并生成 verify result。

### ocw review
进入 review decision 组装与审批流程。

### ocw archive
归档并刷新 stable/index/maintenance context。

### ocw status
显示当前 change、当前步骤、gate 状态、待处理阻断项。

## 5. 默认路径
### 5.1 默认路径的设计目标
默认路径用于降低外显复杂度。用户只要想“开始一个受治理的任务”，就应能先启动最小链路，而不是先学习全部治理文件。

### 5.2 默认路径命令顺序
```text
ocw init
ocw change create
ocw run
ocw status
```

说明：
- `init` 建立最低治理目录。
- `change create` 创建最小 change package，并指向当前 change。
- `run` 在内部发现缺失项时，应优先提示并引导补齐 contract / bindings / verify / review 预留，而不是直接静默失败。
- `status` 用于告诉用户当前所处步骤、当前 gate 与待补阻断项。

默认路径的要求不是“跳过治理”，而是“由 CLI 代为承接必要复杂度”。

### 5.3 默认路径的产品约束
- 默认路径必须可从项目根目录直接使用。
- 默认路径必须优先使用项目默认治理目录与当前 change 指针。
- 默认路径下，用户不应被要求先手动编辑 index 文件。
- 默认路径下，CLI 应优先输出下一步建议，而不是完整内部 schema。

## 6. 新手路径
### 6.1 适用对象
适用于第一次接触 open-cowork、希望逐步理解 change package 与 contract 的用户。

### 6.2 新手路径命令顺序
```text
ocw init
ocw propose
ocw change create
ocw contract generate
ocw status
```

说明：
- `propose` 先把自然语言输入整理成 intent 草稿，降低直接面对多文件 change package 的门槛。
- `change create` 基于 intent 创建结构化骨架。
- `contract generate` 生成 contract 草稿，让用户先看到执行边界，再决定是否进入 `run`。
- `status` 应明确告诉用户“当前仍在 Step 5 还是已具备进入 Step 6 的条件”。

### 6.3 新手路径的交互要求
- 优先展示“为什么还不能 run”。
- 对缺失项应使用用户层术语解释，例如“还缺执行约束文件”，而不是只吐 schema 名称。
- 当存在多个缺失项时，应给出有顺序的补齐建议。
- 不要求新手先理解 archive、stable-map、changes-index 等内部治理细节。

## 7. 专家路径
### 7.1 适用对象
适用于已经理解 9 步生命周期、希望显式控制每个治理动作的用户或自动化脚本。

### 7.2 专家路径命令顺序
```text
ocw init
ocw propose
ocw change create
ocw contract generate
ocw run
ocw verify
ocw review
ocw archive
ocw status
```

### 7.3 专家路径要求
- 每个命令都应可单独调用。
- 专家路径允许显式指定 change id、adapter、工作目录、验证命令与输出位置。
- 专家路径允许直接查看结构化产物，但仍不能绕过 contract、verify、review、archive。
- 专家路径是“显式控制”，不是“跳过 gate”。

## 8. 默认路径
- 默认治理目录：`.governance/`
- 默认当前 change 指针：`.governance/index/current-change.yaml`
- 默认输出人类入口：`README.md` 仅做人类导航，不做机器事实层。
- 默认 change package 路径：`.governance/changes/<change-id>/`
- 默认执行隔离策略：由 Step 5/6 绑定结果决定，CLI 不应假定主工作区可直接执行。

## 9. 低侵入要求
允许：
- 独立治理目录
- 文件契约
- 命令接口
- 桥接接口
- 隔离执行目录 / worktree / sandbox

避免：
- 深改用户业务项目结构
- 强迫替换现有 agent/harness
- 强制统一底层工具链
- 默认接管外部 agent 配置

## 10. MVP 不向普通用户暴露的能力
- 复杂 gate policy matrix
- 多 adapter 编排细节
- 细粒度 runtime 状态机
- 内部索引重建机制
- 深度 registry 管理

## 11. CLI 输出要求
- 对外显示用户层术语。
- 对内保留结构化文件产物。
- `status` 命令必须能看见 blockers、当前 step、下一 gate。
- 默认路径下优先显示下一步动作建议。
- 新手路径下优先显示缺失项与补齐顺序。
- 专家路径下允许显示完整结构化上下文，但不应替代落盘文件。

## 12. 阻断条件
- 用户要理解一堆内部 schema 才能开始。
- init/run 默认高侵入。
- run 不经过 contract 就直接执行。
- 默认路径把 verify/review/archive 彻底隐藏，导致闭环不可达。
- 新手路径不能判断当前仍处于 Step 5 还是已可进入 Step 6。

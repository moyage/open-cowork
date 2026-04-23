# open-cowork 最小索引与产物文档治理方案

## 1. 目标
定义最小 index 层与产物文档治理规则，确保执行结果能被导航、检索、归档、维护，而不依赖 README 充当机器事实层。

## 2. index 层职责
- 给出当前 change 指针。
- 给出 stable 文档映射。
- 给出 archive 导航。
- 给出状态摘要与待办阻断项入口。

## 3. 最小索引文件
```text
index/
  current-change.yaml
  changes-index.yaml
  stable-map.yaml
  archive-map.yaml
  maintenance-status.yaml
```

## 4. 文件职责
### current-change.yaml
指向当前正在推进的 change 与当前步骤。

### changes-index.yaml
记录 change 列表、状态、policy level、最近更新时间。

### stable-map.yaml
记录 stable 层关键文档及其主题映射。

### archive-map.yaml
记录历史归档位置、摘要、时间线。

### maintenance-status.yaml
记录当前维护上下文、下一轮关注点、待处理 followups。

## 5. 产物文档治理原则
- 文档分层必须与 stable/changes/archive/index 对齐。
- README 只做人类入口、项目介绍、快速开始。
- 机器应优先读取 stable 与 index，不以 README 为事实源。
- 已批准变更的结论必须同步进入 stable 或 maintenance context，而非只留在 archive。

## 6. 生命周期
1. 变更进行中：更新 current-change 与 changes-index。
2. 审查通过后：更新 stable-map 与 maintenance-status。
3. 归档完成后：更新 archive-map，并移除 current-change 指针或切换到下一 change。

## 7. 阻断条件
- 没有 current-change 指针，导致运行态混乱。
- archive 完成但 stable-map / maintenance-status 未刷新。
- README 被当成事实源替代 stable/index。

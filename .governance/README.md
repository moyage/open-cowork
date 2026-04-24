# .governance 目录

`.governance/` 是 `open-cowork` 的运行时治理产物目录，不是普通文档目录。

它用于保存项目在执行过程中的结构化事实、当前变更、证据、状态快照、归档和接续材料。

## 仓库中默认提交的内容

- `templates/`：可复用模板。
- `README.md`：本说明文件。

## 运行时生成且默认不提交的内容

- `index/`：当前 change 指针、维护状态和索引。
- `changes/`：正在推进的 change package。
- `archive/`：已归档的 change package。
- `runtime/`：状态、timeline 和面向外部工具的投影输出。

## 初始化方式

在目标项目根目录执行：

```bash
ocw --root . init
```

如果你只是阅读 `open-cowork` 框架本身，通常不需要手动编辑 `.governance/`。

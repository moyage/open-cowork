# 贡献指南

感谢你参与 `open-cowork`。

## 本地开发

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
./scripts/smoke-test.sh
python3 -m unittest discover -s tests -v
```

## 贡献原则

1. 保持治理边界清晰。
2. 不削弱 executor / reviewer 分离。
3. 行为变化必须补充或更新测试。
4. 用户可见能力变化必须同步更新文档。
5. 不提交个人本地路径、私有配置、密钥或团队成员个人信息。
6. 不把某个个人域工具写死为通用机制。

## PR 检查清单

- [ ] 本地测试通过。
- [ ] 文档与实际 CLI 行为一致。
- [ ] 没有泄露个人域信息、绝对路径、密钥或内部身份信息。
- [ ] 变更范围清楚，没有混入无关重构。
- [ ] 如果涉及治理状态流转，已确认不会破坏 archive / review / evidence 约束。

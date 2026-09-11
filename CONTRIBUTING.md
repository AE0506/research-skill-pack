# 贡献指南

欢迎提交文档、Profile、Skill 和验证改进。请保持本项目的核心边界：不伪造研究证据、不读取原始敏感数据、不把模型判断写成外部事实，也不自动向外部系统提交材料。

## 提交前检查

```bash
cd plugins/research-skill-pack
python3 -m pytest -q
python3 scripts/validate_plugin.py
python3 scripts/validate_plugin.py --catalog-report --verification-report
```

新增或修改 Skill 时，Catalog、验证矩阵和 Skill 目录必须同步；每个 `acceptance_id` 只能映射一次，并诚实标记为结构检查、确定性契约测试或人工试跑。新增 Profile 时，先登记到 Profile Registry，再更新 schema 与迁移/测试证据。

请勿提交真实题目、个人信息、原始数据、全文、凭据或未获授权的文献内容。真实试跑一律在仓库外进行，公开时仅提交经人工审阅的脱敏报告。

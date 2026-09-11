# 验证模型与证据边界

`verification-matrix-v0.2.yaml` 为每个 Catalog `acceptance_id` 提供唯一验证记录。它解决“没有映射”的问题，但不把静态检查伪装为模型能力测试。

| 层级 | 当前数量 | 实际证明什么 | 不证明什么 |
| --- | ---: | --- | --- |
| `structural` | 160 | Skill 可发现、Catalog 元数据与安全/门槛声明完整 | 模型是否正确执行工作流、来源是否真实 |
| `deterministic_contract` | 8 | 本地 artifact、状态闸门、时间线或原始数据隔离规则 | LLM 判断质量、研究结论 |
| `manual_pilot` | 7 | 真实匿名项目中经人工确认的核心流程步骤 | 外部来源真实性、投稿成功或普遍适用性 |

运行：

```bash
cd plugins/research-skill-pack
python3 scripts/validate_plugin.py --verification-report
```

报告中的 `coverage_complete: true` 仅表示 175 条验收 ID 都有一条明确的验证路径。它不表示完成了 175 项独立模型功能测试。

引用、证据与期刊相关 Skill 都是本地辅助判断：本项目不联网核验、不调用外部数据库、不代替人工查证，也不会把模型输出升级为可发表事实。

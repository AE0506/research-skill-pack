# Changelog

本项目遵循“已验证事实与计划分开记录”的原则。

## v0.2.0 Beta — 未发布

### Added

- MIT 授权、Profile Registry、175 条验收 ID 的验证矩阵和本地私有试跑审计器。
- GitHub Actions：Python 3.11/3.12 上运行 pytest、插件校验、Catalog 与验证映射报告。
- 贡献指南、验证层级说明、匿名试跑证明协议及 Release Notes 模板。
- 175 张逐项 Skill 操作深度卡：每张都包含自身的前置核对、五步执行协议、产物记录模板、失败/确认分支、证据边界与交接条件。
- Skill 深度校验与报告：CI 拒绝缺段、过短、未声明工作流深度或未覆盖自身 Catalog 契约的 Skill。

### Changed

- Catalog 以已安装 Skill 目录名为准，并保留 172 条旧设计 ID 的兼容映射。
- 验证结果明确分为结构检查、确定性项目契约测试和人工试跑；没有任何条目被宣称为通用 LLM 行为验证。

### Not released yet

- 真实匿名试跑尚未完成，因此 `v0.2.0` GitHub pre-release 尚未创建。

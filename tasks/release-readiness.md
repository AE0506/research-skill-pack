# v0.2 发布就绪度

更新：2026-09-11。此记录区分已由本机命令验证的事实与尚未验证的产品主张，避免把设计目标写成已交付能力。

## 已有证据

- `codex plugin list` 显示 `research-skill-pack@research-local` 为 `installed, enabled`；安装与发现已在本机 Codex CLI 上核对。
- `python3 scripts/validate_plugin.py` 校验插件清单、175 个 Skill 的 YAML 元数据、两个合成项目 fixture 与 Catalog 的设计字段。
- `python3 -m pytest -q` 覆盖项目 schema、状态闸门、迁移、时间线、数据安全和插件结构校验。

以上均不调用模型、不联网、不读取原始研究数据。

## 发布前阻塞项

1. **Catalog 与实现收敛**：Catalog 有 172 个设计 ID，实际有 175 个 Skill 目录，且存在名称漂移。`python3 scripts/validate_plugin.py --catalog-report` 是当前唯一可信的差异报告；在逐项确认、改名或建立显式映射前，Catalog 不得被称为实现真源。
2. **真实研究试跑**：用已获得授权且不含敏感原始数据的最小项目，人工走完“约束采集 → Context Brief 确认 → Timeline → Gap Card → Review Board”的受限路径，记录每一步输入、产物和人工复核结论。不要把合成 fixture 或模型推演写成真实研究验证。
3. **测试追踪**：Catalog 的 `acceptance_ids` 是需求标签，不是测试文件名。为高风险闸门建立显式的“需求 ID → 自动化测试 / 人工试跑记录”映射后，才可声明逐项覆盖。
4. **许可证**：著作权人需选择并加入明确许可证；这会决定使用者和贡献者的复制、修改与分发权利。

## 后续优先级

- P0：完成 Catalog 映射和最小真实试跑。
- P1：补充高风险阶段的行为测试（证据升级、引用审计、原始数据隔离、投稿确认）。
- P2：审阅短 Skill 的实际可操作性，将仅有接口规格的条目改为最小工作流或明确标为设计占位。

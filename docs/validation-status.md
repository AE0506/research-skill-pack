# v0.2 Beta 验证状态

更新：2026-09-11。

本页只陈述可复核的验证层级，避免将结构检查、合成 fixture 或模型推演表述为真实研究能力验证。

## 已验证

- 插件的 Catalog 与已安装 Skill 目录严格一致：175 个 Catalog 条目对应 175 个 `SKILL.md` 目录；172 个旧设计 ID 保留为一对一兼容映射。
- 本地校验器检查插件清单、Skill 元数据、Catalog/目录/映射一致性、两套合成项目 fixture 和项目契约。
- 自动化测试覆盖项目 schema、状态闸门、迁移、时间线、原始数据隔离、Catalog 映射、Profile Registry、验证矩阵，以及 175 张 Skill 操作深度卡的段落、长度、Catalog 契约镜像与失败回归。
- 175 个 `acceptance_id` 均映射到一条验证记录：160 条结构检查、8 条确定性契约测试、7 条人工真实试跑步骤。映射完整性不等于 175 项独立的模型功能测试。
- 所有 175 个 Skill 都有操作深度卡：各自的前置核对、至少五步执行协议、版本化记录模板、`requires_confirmation`/`blocked` 分支、证据边界和最小情境演练。该结构化完整性不等同于它们各自完成行为级测试。
- 本地 `research-state` MCP 服务以 175/175 写入策略表、12 条正常状态路由、29 种 canonical artifact 写入者和 revision/收据链约束正常插件路径；测试覆盖合法提交、闸门拒绝、策略越权、过期 revision、重复请求、敏感原始数据字段、日志恢复与 MCP 工具发现。它不是文件系统级阻断。

可复核命令：

```bash
cd plugins/research-skill-pack
python3 -m pytest -q
python3 scripts/validate_plugin.py
python3 scripts/validate_plugin.py --catalog-report
python3 scripts/validate_plugin.py --verification-report
python3 scripts/validate_plugin.py --skill-depth-report
python3 scripts/validate_plugin.py --mutation-policy-report
```

以上命令不调用模型、不联网、不读取真实项目原始数据。

## 尚未验证

- 一次已获授权的匿名真实选题试跑尚未随仓库发布；提供的是协议和报告模板，而不是虚构的试跑结果。
- 插件安装后的真实对话行为、模型输出质量、外部文献或期刊信息的真实性，以及投稿流程均没有由这些本机检查验证。MCP 收据证明本地正常写入路径经过了确定性校验，不证明模型一定调用该路径。
- `validation.level: structural` 代表结构、元数据或合成 fixture 检查；`deterministic_contract` 代表本地项目契约规则；`manual_pilot` 代表需要按试跑协议人工核验的路径。它们不应被解读为逐项模型功能测试完成。详见 [验证模型](verification-model.md)。

## 不做事项

- 不联网核验来源、期刊或实时研究事实。
- 不默认读取、上传或处理原始敏感数据；原始数据只允许登记路径、哈希和访问条件。
- 不登录、提交、上传或发送任何外部系统中的研究材料。
- 不伪造证据、研究结果、作者声明，或提供规避学术检测的能力。

## Beta 范围

v0.2 Beta 仅激活 `zh-undergrad-information-management-empirical`。支持列表由 Profile Registry 与项目 schema 的同步校验共同控制；收集到第二类真实需求前，不会以放宽现有 schema 的方式假装支持更多学科或学位类型。

许可证为 [MIT](../LICENSE)。MIT 授予代码使用、复制、修改和分发权利，但不保证研究结论、数据合规、期刊要求或投稿结果。

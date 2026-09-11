# Research Skill Pack v0.2 Beta

个人本地 ChatGPT 桌面 Codex 插件，服务中文本科信息管理与社会科学实证论文。它使用 `<project>/.research/` 保存版本化、可审计的科研状态，并将 12 步科研流程拆为一个路由入口和可显式调用的专业 Skill。

首版仅支持 YAML 与 Markdown；文献以用户导入资料为主，在线来源仅有未配置的适配接口。v0.2 Beta 仅支持 `zh-undergrad-information-management-empirical`。插件不会自动读取原始敏感数据、伪造证据、规避 AI 检测或向外部投稿系统发送任何内容。

## 本地校验边界

从仓库根目录运行：

```bash
cd plugins/research-skill-pack
python3 -m pytest -q
python3 scripts/validate_plugin.py
```

这会验证插件清单、Skill 元数据、合成项目 fixture、项目契约，以及 Catalog、旧设计 ID 映射和 Skill 目录的严格一致性；不调用模型、不联网、不读取原始数据，也不代表真实研究项目已端到端验证。`python3 scripts/validate_plugin.py --catalog-report` 输出当前严格一致性报告。

## 授权与 Beta 边界

本项目采用 [MIT License](../../LICENSE)。已验证、尚未验证与明确不做事项见 [Beta 验证状态](../../docs/validation-status.md)。真实试跑必须在仓库外的独立本地目录进行，并遵循 [匿名真实试跑协议](../../docs/beta-pilot-protocol.md)；仓库当前仅提供协议与脱敏报告模板，不声称已经完成真实试跑。

# 科研论文 Skill Pack

这是一个个人本地 ChatGPT 桌面 Codex 插件，插件目录为
`plugins/research-skill-pack/`。它提供一个自动路由入口
`$research-orchestrator`，以及 13 个只可显式调用的研究阶段 Skill：12
个科研步骤与 8.5 写作原创性与可追溯性闸门。

首版面向 `zh-undergrad-information-management-empirical`：中文本科信息管理
与社会科学实证论文。每个论文项目把结构化状态保存在
`<project>/.research/project.yaml`，并以版本化 artifact 保存证据、决策与
报告。它不会自动读取原始敏感数据、杜撰证据、规避 AI 检测，或实际投递稿件。

## 本地安装

```bash
codex plugin marketplace add /Users/zhangzheng/Documents/项目/科研skill包
codex plugin add research-skill-pack@research-local
```

重新打开一个 Codex 会话后，可用 `$research-orchestrator` 发现或初始化本地
科研项目；其他阶段 Skill 必须显式调用。

## 验证

```bash
cd /Users/zhangzheng/Documents/项目/科研skill包/plugins/research-skill-pack
python3 -m pytest -q
python3 scripts/research_contract.py validate fixtures/valid-project
```

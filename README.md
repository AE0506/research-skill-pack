# Research Skill Pack

> 给第一次真正独立做科研的人，一套从“我该做什么”走到“我凭什么这样写”的本地工作流。

一篇本科论文最难的部分，往往不是把八千字写出来。

真正困难的是：在导师要求、学校规范、个人能力、可获得数据和最终截止日期之间，找到一个**做得完、站得住、能留下真实成果**的研究问题；然后在漫长的几个月里，不让选题、文献、数据、论证和写作彼此脱节。

普通论文工具通常从“请帮我写”开始。Research Skill Pack 从更早的地方开始：**先理解研究者，再建立证据，再组织论证，最后才允许写作。**

<table>
  <tr>
    <td align="center"><b>理解研究者</b><br><sub>学校 · 导师 · 能力 · 资源 · 时间</sub></td>
    <td align="center">→</td>
    <td align="center"><b>判断是否值得做</b><br><sub>领域机会 · Gap · Sweet Spot · Review Board</sub></td>
    <td align="center">→</td>
    <td align="center"><b>获得真实证据</b><br><sub>文献 · 设计 · 数据 · 分析 · Lineage</sub></td>
    <td align="center">→</td>
    <td align="center"><b>形成可审计论文</b><br><sub>论证树 · 写作 · 引用 · 审稿 · 归档</sub></td>
  </tr>
</table>

## 它解决什么问题

科研中的失败很少发生在最后一天。更常见的是：

- 选题看起来新，却不符合导师、学校、能力或截止时间。
- 已经提出假设，才发现没有可测变量或拿不到真实数据。
- 文献读了很多，写作时仍不知道“哪篇论文真正支持这句话”。
- 数据结果尚未核验，正文已经写出了漂亮结论。
- 离提交只剩两周，才发现导师反馈、格式审查和返修没有留出缓冲。

Research Skill Pack 把这些问题变成可见、可追溯、可阻断的项目状态。它不替用户伪造研究，也不把“生成了一段文字”误认为“完成了一项科研工作”。

```text
No Evidence, No Claim
No Claim, No Paragraph
No Verified Manuscript, No Submission
```

## 我们怎样设计它

### 一个项目，只有一个结构化真源

每篇论文在自己的项目目录中保存 `.research/project.yaml`。Markdown 是供人阅读的报告；版本化 YAML artifact 才是证据、决策、计划和稿件依赖的真源。

```text
my-thesis/
└── .research/
    ├── project.yaml          # 当前状态、artifact 索引、确认记录
    ├── artifacts/            # 不静默覆盖的版本化成果
    └── reports/              # 面向人阅读的 Markdown
```

每个 artifact 都记录来源、核验状态、是否可用于论文 Claim、依赖关系、替代版本和修改原因。原始数据只登记路径、哈希和访问限制，默认不会被读入模型。

### 不是一个大 Skill，而是一套科研工作单元

插件保留 `$research-orchestrator` 作为唯一的自动路由入口，并提供 **170 多个显式调用的细 Skill**。它们不是为了堆数量，而是让每个重要科研动作都有明确边界：输入是什么、前置条件是什么、生成什么 artifact、何时必须停下等待人工确认。

<table>
  <tr><th align="left">Skill Pack</th><th align="left">它负责回答的问题</th></tr>
  <tr><td>Project Governance</td><td>我是谁、要交什么、导师和学校允许什么？</td></tr>
  <tr><td>Timeline & Milestone OS</td><td>现在到哪一步、这周做什么、延期后还能怎么恢复？</td></tr>
  <tr><td>Topic Intelligence</td><td>这个方向有机会吗？它是否落在我的 Project Sweet Spot？</td></tr>
  <tr><td>Literature & Gap</td><td>已有研究知道什么、不知道什么、哪条证据支持哪项主张？</td></tr>
  <tr><td>Design & Evidence</td><td>问题能否被真实测量、分析和验证？</td></tr>
  <tr><td>Manuscript & Audit</td><td>论证是否闭合？每一句话是否有足够证据与引用？</td></tr>
  <tr><td>Review & Submission</td><td>最严厉的审稿人会攻击哪里？哪些材料还不能提交？</td></tr>
</table>

完整目录见 [Skill Catalog](plugins/research-skill-pack/shared/skill-catalog-v0.2.yaml)。

### 时间不是“最终截止日期”一个字段

Timeline OS 与论文状态机并行运行。它从最终提交、开题/中期/答辩节点、每周可投入时间、导师反馈窗口和不可用日期开始，反向建立计划；之后持续回答“当前阶段、本周优先事项、关键路径和延期风险”。

```text
Timeline Intake → Deadline Ladder → Capacity Assessment → Timeline Baseline
                                                          ↓
GO 决策 → Execution Timeline → Weekly Actions → Drift Monitor → Rebaseline Draft
```

AI 只能提出重排方案，不能悄悄改计划；任何新的时间基线都必须由用户确认。全局 Portfolio 只汇总用户主动登记项目的路径、状态、风险和下一节点，不复制论文、证据或原始数据。

### Sweet Spot 不是“选题总分”

Project Sweet Spot 依次检查五道闸门：硬约束匹配、执行可行性、证据可获得性、研究贡献匹配、韧性与战略匹配。结论只会是“适合”“有条件适合”或“不在甜蜜区”，并附带依据、风险和 Plan B；它不会用一个看似精确却不可审计的分数替你做决定。

## 安全与学术诚信边界

- 不补造问卷、实验、样本、统计结果、图表或引用。
- 不把 AI 提取、网页摘要或未核验 PDF 当作论文证据。
- 不读取原始敏感数据；只有用户明确批准的最小脱敏摘要才可被使用。
- 不提供“去 AIGC”、绕过检测或规避学校规则的承诺。
- 不登录期刊系统、不发送邮件、不上传或提交稿件。
- 在线来源当前仅保留 `not_configured` 的适配接口；首版以用户导入的本地资料为基础。

## 安装与开始使用

### 前提

- ChatGPT 桌面 Codex 环境。
- Python 3.11+，以及项目声明的 `PyYAML`、`jsonschema`、`pytest`。

### 从 GitHub 安装

```bash
git clone https://github.com/AE0506/research-skill-pack.git
cd research-skill-pack
codex plugin marketplace add "$PWD"
codex plugin add research-skill-pack@research-local
```

重新打开一个 Codex 会话后，从下面这句话开始：

```text
使用 $research-orchestrator 开始或继续我的科研项目。
```

日常用户不需要记住全部 Skill；路由器会根据项目状态、时间线和缺失 artifact 建议下一步。想精细控制时，再显式调用具体 Skill，例如 `$timeline-intake`、`$project-sweet-spot-assessor` 或 `$citation-entailment-auditor`。

## 本地验证

```bash
cd plugins/research-skill-pack
python3 -m pytest -q
python3 scripts/research_contract.py validate fixtures/valid-project
python3 scripts/research_contract.py validate fixtures/v0.2-project
python3 scripts/research_contract.py validate-portfolio fixtures/portfolio.yaml
```

## 当前版本与边界

当前为 `v0.2.0`，首版 profile 是 `zh-undergrad-information-management-empirical`，面向中文本科信息管理与相邻社会科学实证论文。输出仅限 YAML 与 Markdown；不生成 DOCX、LaTeX，也不承诺普通网页版 ChatGPT 具备同等本地项目与数据能力。

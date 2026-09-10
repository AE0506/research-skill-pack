# 实施计划：科研论文 Skill Pack

## 目标

构建一套安装后可在 Codex / ChatGPT 协作环境中调用的科研论文 Skill Pack。它服务于用户的真实科研项目，不生成或托管独立 Web 产品；每个 Skill 读取同一个项目状态、产生可追溯产物，并遵守“无证据不主张、无核验不投稿”的边界。

产品保留 12 个主流程。`Research Context Intake` 是第 1 步 `Research Radar` 的强制入口；`AI Writing Originality & Traceability Pack` 是第 8 步之后、第 9 步之前的 8.5 质量闸门，不额外增加主流程编号。

## 架构决定

### 1. 交付形态

- 本仓库是 Skill Pack 的开发源；不实现网页、登录、数据库或独立后端。
- 每项用户可调用能力是独立的 Codex Skill 文件夹，具有一个简洁的 `SKILL.md` 和仅在需要时读取的 `references/`。
- 安装阶段将各 Skill 安装/复制到 Codex 的可发现 Skill 目录；安装方式须在真实目标环境中验证，不能凭假设编写。
- 可增加一个不属于科研阶段的 `research-orchestrator` 路由 Skill，用于根据项目状态选择下一个主 Skill；它不替代任何专业 Skill。

### 2. 共享科研项目契约

每个研究项目在用户指定目录中维护可读、可审计的文件，而不是隐藏在模型记忆中。首版使用 Markdown/YAML/CSV/JSON 等人可审阅的格式，后续再评估是否需要数据库。

建议的项目根目录：

```text
research-project/
├── project.yaml                    # 项目、profile、状态与当前阶段
├── context/                        # 背景、导师约束、确认后的 Brief
├── topic/                          # 机会画像、候选方向、立项决定
├── literature/                     # 检索记录、文献实体、Claim 与证据图谱
├── design/                         # 协议、变量、样本与分析计划
├── evidence/                       # 原始数据登记、清洗、代码、结果与图表
├── manuscript/                     # 论证蓝图、草稿、段落/Claim 链接
├── review/                         # 模拟与真实审稿意见、返修任务
└── submission/                     # 投稿包、期刊梯队、版本与回复矩阵
```

共享契约必须首先定义：对象 ID、版本、来源、时间、AI/人工核验状态、上游依赖、证据位置和变更原因。原始数据只登记和只读引用，清洗结果不得覆盖它。

### 3. 证据与诚信边界

- 任何从外部来源得出的研究事实都要保存来源、定位信息和核验状态。
- Skill 必须区分 `AI-extracted`、`human-verified`、`project-generated`、`unverified`，不将前者伪装为后者。
- AIGC 质量包用于提升实质性、可追溯性和原创表达；不得承诺或指导绕过检测，也不得制造未使用 AI 的虚假声明。
- 数据、实验、统计和投稿均需用户的真实输入与授权；Skill 只做准备、检查和建议。

### 4. 分阶段策略

第一版不是同时实现 12 个复杂自动化系统。先完成可以被真实使用的“前半程立项闭环”：

```text
Research Context Intake
→ Topic opportunity record
→ evidence-backed gap candidate
→ Research Review Board decision
→ project-level proposal brief
```

第二阶段建立 Literature OS 和 Research Design，第三阶段接通数据、写作、审计与审稿，最后才做投稿返修。每一步先实现本地、可核验的闭环；外部文献数据库或模型供应商通过可替换适配器接入，不能把“网页搜索结果”当作学术证据。

## 依赖图

```text
Skill package conventions + shared project schema
             │
             ├── Research Context Intake ──┐
             ├── Source / evidence contract │
             │                              ▼
             │                     Topic Radar → Gap Finder → Review Board
             │                                                │
             ▼                                                ▼
       Literature OS ───────────────────────────────→ Research Design
                                                               │
                                                               ▼
                                                     Data & Evidence Lab
                                                               │
                                                               ▼
                                                     Paper Architect
                                                               │
                                                               ▼
                                                Writing → Originality Gate → Citation Guard
                                                               │
                                                               ▼
                                                    Reviewer Simulator → Journal Matcher
                                                               │
                                                               ▼
                                                    Submission & Revision OS
```

## 版本路线

### V0.1：可用的科研立项闭环

目标：用户能在一个本地研究项目中完成背景约束确认、候选方向整理、带来源的空白卡、严格立项决策和开题简报。

包含：第 1、2、3 步的最小可用版本，以及共享状态、证据契约和安装验证。

不包含：自动声称“搜全”、未经核验的实时趋势分数、真实数据库大规模抓取、自动写整篇论文。

### V0.2：证据库与研究设计

目标：将已获得文献变为可核验的 Claim Library、关系图和研究方案；用户可从项目证据库生成论文论证蓝图。

包含：第 4、5、7 步的首版，以及第 6 步的计划/登记能力。

### V0.3：真实证据到可审稿稿件

目标：从真实数据和实验结果生成受约束稿件，完成 AI 写作实质检查、引用审计和模拟审稿。

包含：第 6、8、8.5、9、10 步。

### V0.4：投稿与科研档案

目标：依据已核验期刊要求形成投稿策略、返修链路和完整项目归档。

包含：第 11、12 步。

## 模块映射

| 主步骤 | 开发 Skill/能力 | 首个可用产物 | 关键依赖 |
|---|---|---|---|
| 1 | `research-radar`（含 context intake） | Research Context Brief、Topic Opportunity Profile | 项目 schema、来源契约 |
| 2 | `research-gap-finder` | Evidence-backed Gap Cards、候选问题 | 轻量文献记录 |
| 3 | `research-review-board` | GO/CONDITIONAL GO/PIVOT/KILL 决策 | 用户约束、Gap、Radar |
| 4 | `research-literature-os` | Literature Records、Claim Library、Evidence Graph | 版本/来源 schema |
| 5 | `research-design` | Research Protocol、变量与分析计划 | 已通过立项的问题、证据库 |
| 6 | `research-evidence-lab` | Data/Experiment registry、lineage、Verified Evidence Package | Protocol |
| 7 | `paper-architect` | Manuscript Blueprint、Argument Tree | 文献与真实结果 |
| 8 | `academic-writing` | 带句子角色和证据链接的章节草稿 | Blueprint |
| 8.5 | `academic-originality` | 实质性/可追溯性修改报告 | 草稿、项目证据 |
| 9 | `citation-evidence-guard` | Citation-audited manuscript、风险热图 | Claim/证据链接 |
| 10 | `reviewer-simulator` | 分级审稿报告、返修任务 | 审计后的稿件 |
| 11 | `journal-venue-matcher` | Reach/Match/Safe 投稿梯队、合规清单 | 稿件与经核验的期刊资料 |
| 12 | `submission-revision-os` | 投稿包、回复矩阵、Research Archive | 期刊 profile、版本控制 |

## 验收总则

- 每个 Skill 通过 Codex Skill 校验，描述可被准确发现，且只加载当前任务需要的资料。
- 每个 Skill 都用同一份合成研究项目 fixture 演示一次端到端输入与输出。
- 所有“事实”“文献”“数据结果”均显示来源或明确标为未核验；没有来源就不能升级为论文 Claim。
- 每个阶段产生的文件均可由用户直接打开检查，并被下游 Skill 正确读取。
- 不以文案相似度测试代替行为验证；测试应检查 schema、状态流转、引用定位、版本依赖和禁止行为。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 12 个模块同时开工 | 高 | 先交付 V0.1 立项闭环，后续按依赖推进 |
| 论文数据库/API 权限与条款不同 | 高 | 先定义可替换来源适配器和人工导入闭环；接入前逐源核验 |
| LLM 生成幻觉引用或过强结论 | 高 | Claim、来源定位与人工核验状态是基础 schema，不是后补功能 |
| Skill 指令臃肿、相互冲突 | 中 | 每 Skill 只保留其独有决策；共用 schema 与规则移入引用资料 |
| "AI 去重"被误解为规避检测 | 高 | 以原创性、实质性、溯源和人工修改为目标，禁止规避承诺 |
| 用户项目格式千差万别 | 中 | profile 可扩展，首版只支持明确的最小字段和人工确认 |

## 需要在实施前核验的外部事实

- 目标 ChatGPT/Codex 环境中 Skill 的实际安装与发现路径、是否支持本地 Skill 目录。
- 可合法稳定调用的文献元数据、全文、引用与撤稿数据源；其 API、授权、限额和使用条款。
- 第一版优先支持的论文类型和学科 profile；默认可先用“中文本科毕业论文 / 信息管理与社科实证”作为演示 fixture，但不应写死为通用规则。


# [归档] 科研论文 Skill Pack 开发任务清单

> 这是早期开发任务记录，不代表当前已交付能力或 v0.2 Beta 发布承诺。请以 [Beta 验证状态](../docs/validation-status.md) 为准。

本清单以 [tasks/plan.md](plan.md) 为架构依据。当前仓库为空；本阶段仅计划，不把未确认的外部 API 或模型能力写成已实现功能。

## Phase 0：包约定与共享项目状态

## Task 1：建立 Skill Pack 源目录和命名约定

**Description：** 建立 12 个主 Skill、8.5 质量闸门以及可选路由 Skill 的源目录，并为每项写出可准确触发的简短描述；不填充尚未验证的工作流细节。

**Acceptance criteria：**
- [ ] 每个目录名符合 Codex Skill 命名规范。
- [ ] 每个 Skill 具有可发现且不互相抢占的职责描述。
- [ ] 第 1 步包含 Context Intake，第 8.5 步不改变 12 步编号。

**Verification：**
- [ ] 使用 Skill 校验器检查所有已创建的 Skill 目录。
- [ ] 人工检查“雷达、空白发现、立项评审”职责没有重叠。

**Dependencies：** None

**Estimated scope：** Medium

## Task 2：定义 Research Project Schema v0.1

**Description：** 定义 `project.yaml` 与 context/topic/evidence 记录的必填字段、ID、版本、来源和核验状态；同时定义 Raw Data 不可覆盖的约束。

**Acceptance criteria：**
- [ ] 一份合成项目可表示背景、导师约束、方向、来源、Gap 和立项决定。
- [ ] Claim、文献与数据记录均能保存来源、定位和人工核验状态。
- [ ] schema 明确禁止以清洗结果覆盖原始数据。

**Verification：**
- [ ] 用 JSON/YAML schema 或等价检查验证 fixture。
- [ ] 人工追踪一条 Claim 至其来源记录。

**Dependencies：** Task 1

**Estimated scope：** Medium

## Task 3：创建合成研究项目 fixture 与测试契约

**Description：** 使用明确标记为合成的数据和文献记录创建端到端 fixture；它用于验证 Skill 之间传递，不冒充真实文献或真实实验。

**Acceptance criteria：**
- [ ] fixture 覆盖一条可 GO 的候选题与一条因数据不可得而 PIVOT 的候选题。
- [ ] fixture 含已核验、未核验和矛盾证据状态。
- [ ] fixture 可被 V0.1 的每个 Skill 读取。

**Verification：**
- [ ] schema 校验通过。
- [ ] 手动检查所有合成内容均有清晰标识。

**Dependencies：** Task 2

**Estimated scope：** Small

## Checkpoint：Phase 0

- [ ] 目录、命名与共享 schema 已评审。
- [ ] 合成 fixture 可被读取并不含伪造的真实学术信息。

## Phase 1：V0.1 科研立项闭环

## Task 4：实现 Research Context Intake

**Description：** 创建第 1 步中的背景与约束采集模式：根据已有上下文仅询问会实质改变建议的缺失信息，并输出需用户确认的 Research Context Brief。

**Acceptance criteria：**
- [ ] 能记录任务类型、论文规范、时间、导师约束、能力、资源、偏好和自由备注。
- [ ] 不重复询问项目文件中已经确认的信息。
- [ ] 输出可写入 `context/` 的结构化 Brief，并保留未确认字段。

**Verification：**
- [ ] 用 fixture 运行一次，Brief 与预设字段一致。
- [ ] 人工检查导师约束会出现在后续输入中。

**Dependencies：** Tasks 2-3

**Estimated scope：** Medium

## Task 5：实现 Topic Opportunity Profile

**Description：** 创建 Topic Radar 的离线可验证版本：输入方向、来源记录和用户 Context，输出生命周期、EMS、ADI、SRR、拥挤度、增长与来源覆盖说明；分数必须附证据范围和不确定性，不能假装实时全网结论。

**Acceptance criteria：**
- [ ] 明确区分方向层的 Field Sweet Spot 与用户层的 Project Sweet Spot。
- [ ] 支持萌芽、早期增长、黄金窗口、拥挤、折旧五阶段判断。
- [ ] 输出来源覆盖、数据不足与不可下结论的提示。

**Verification：**
- [ ] fixture 中的高重复候选题触发 SRR/折旧警示。
- [ ] 人工检查没有把能力展示度混入领域机会分。

**Dependencies：** Task 4

**Estimated scope：** Medium

## Task 6：实现 Gap Cards 与候选 Research Questions

**Description：** 创建 Gap Finder：从可定位的文献记录和 Claim 中识别机制、方法、数据、对象、情境、矛盾、复现与测量空白，并生成附证据的候选问题。

**Acceptance criteria：**
- [ ] 每张 Gap Card 至少含类型、支持/反例来源、证据强度、可验证性与风险。
- [ ] 不把“没人做过”单独作为推荐理由。
- [ ] 区分真实贡献与仅换地区/词汇的表面创新。

**Verification：**
- [ ] fixture 的矛盾结果形成 Contradiction Gap。
- [ ] 无来源候选题被标为不可立项证据。

**Dependencies：** Task 5

**Estimated scope：** Medium

## Task 7：实现 Research Review Board 决策

**Description：** 创建多角色立项评审，消费 Context、Radar 和 Gap，输出 GO/CONDITIONAL GO/PIVOT/KILL 及可执行修改建议。

**Acceptance criteria：**
- [ ] 分别检查理论、构念、方法问题匹配、数据可行性、执行风险、能力展示与容错韧性。
- [ ] Fatal Flaw 可以否决平均分较高的候选题。
- [ ] 决策明确列出成立条件、风险、备选路径和下一步。

**Verification：**
- [ ] fixture 的不可得核心数据项目输出 PIVOT 或 KILL。
- [ ] 可行项目输出带前提的 GO 且可生成 Proposal Brief。

**Dependencies：** Task 6

**Estimated scope：** Medium

## Task 8：V0.1 端到端路由与人工验收

**Description：** 实现路由说明和端到端演示，使用户从项目目录启动后能依次完成 Intake、Radar、Gap 和 Review Board；生成开题简报而不是自动进入写作。

**Acceptance criteria：**
- [ ] 下一步由项目状态而不是固定聊天脚本确定。
- [ ] 拒绝/转向项目不能越过 Review Board 自动进入 Research Design。
- [ ] 为用户提供可打开审阅的 Proposal Brief。

**Verification：**
- [ ] 使用 fixture 跑通 GO 与 PIVOT 两条路径。
- [ ] 复核所有产物均指向可见项目文件。

**Dependencies：** Task 7

**Estimated scope：** Medium

## Checkpoint：V0.1

- [ ] Skill 校验通过。
- [ ] 两条端到端路径可复现。
- [ ] 没有未经来源核验的事实被写成项目结论。
- [ ] 用户审阅并批准 V0.1 工作流，再进入文献与设计开发。

## Phase 2：V0.2 证据库、研究设计与论证蓝图

## Task 9：实现 Literature OS 的文献实体与生命周期

**Description：** 实现 Literature Record、身份/版本解析、筛选状态、人工阅读状态、引用使用追踪和撤稿/更正影响字段。

**Acceptance criteria：**
- [ ] 同一研究的多个版本不会在项目中被误计为独立论文。
- [ ] 文献可标记为核心、方法、理论、矛盾、排除或已被替代。
- [ ] 人工核验状态和使用位置可被查询。

**Verification：**
- [ ] fixture 中的两个版本被关联到同一逻辑实体。
- [ ] 已撤回文献能定位其影响的 Claim。

**Dependencies：** Tasks 2-3

**Estimated scope：** Medium

## Task 10：实现 Claim Library、Evidence Graph 与文献地图

**Description：** 以 Claim 为最小可复用证据单元，建立 supports/contradicts/extends 等关系，并提供主题、理论、方法、冲突和时间图谱的文本化输出。

**Acceptance criteria：**
- [ ] Claim 保存原文定位、证据范围、方法、强度和核验状态。
- [ ] 可以显示一条论文主张的支持与反例。
- [ ] 输出文献饱和度的依据，而非仅按篇数判断。

**Verification：**
- [ ] fixture 中矛盾 Claim 能被正确关联。
- [ ] 未核验 Claim 不会被导出为可直接引用的结论。

**Dependencies：** Task 9

**Estimated scope：** Medium

## Task 11：实现 Research Design

**Description：** 从已通过的 Research Question 和 Evidence Base 生成可审阅 Research Protocol，分别覆盖社科实证与计算机实验两种基础模式。

**Acceptance criteria：**
- [ ] 每条假设可映射到构念、变量、可观测证据和数据字段。
- [ ] 明确研究设计能够支持的结论边界。
- [ ] 输出样本、控制变量、测量、方法和风险，不编造数据或样本量。

**Verification：**
- [ ] 任何无对应字段的假设会触发警示。
- [ ] 横截面示例不会被表述为因果设计。

**Dependencies：** Tasks 7 and 10

**Estimated scope：** Medium

## Task 12：实现 Paper Architect

**Description：** 用已核验文献与真实结果的占位接口生成 Argument Tree、章节蓝图与段落蓝图；在没有证据时只报告缺口。

**Acceptance criteria：**
- [ ] 每个核心 Claim 链接至少一条证据或被标为未支持。
- [ ] 输出 Central Thesis、Claim Graph、章节/段落蓝图与逻辑缺口。
- [ ] 章节不能先于论证结构成为主要输入。

**Verification：**
- [ ] fixture 中的超范围因果 Claim 被标记为不支持。
- [ ] 下游草稿可读取 Blueprint。

**Dependencies：** Tasks 10-11

**Estimated scope：** Medium

## Checkpoint：V0.2

- [ ] 用户可从已立项项目获得可核验文献证据库与研究方案。
- [ ] Argument Tree 中每一条 Claim 可回溯或被明确标红。

## Phase 3：V0.3 真实证据、写作与审稿闭环

## Task 13：实现 Data & Evidence Lab 的登记与 lineage

**Description：** 实现数据/实验登记、原始数据引用、清洗产物、分析运行和 Verified Evidence Package 的状态链；首版不自行执行未经用户授权的外部操作。

**Acceptance criteria：**
- [ ] Raw/Processed/Analysis 三层不互相覆盖。
- [ ] 每份结果可追溯数据版本、处理步骤和代码/方法。
- [ ] 无真实结果时不可生成 Results Claim。

**Verification：**
- [ ] fixture 可追溯一张图表到分析数据与来源。
- [ ] 模拟数据不能被误标为真实数据。

**Dependencies：** Task 11

**Estimated scope：** Medium

## Task 14：实现 Academic Writing 与句子角色

**Description：** 基于 Blueprint 与 Verified Evidence Package 生成分章节草稿，写入句子角色、Claim 链接和可追溯来源。

**Acceptance criteria：**
- [ ] Method 和 Results 不得添加协议或结果中不存在的事实。
- [ ] Results 根据设计边界使用关联/因果等正确措辞。
- [ ] 每个可外部验证的 Claim 可交给 Citation Guard 审核。

**Verification：**
- [ ] 对 fixture 生成一节 Method 与一节 Results。
- [ ] 静态检查不存在无来源的新增数值。

**Dependencies：** Tasks 12-13

**Estimated scope：** Medium

## Task 15：实现 AI Writing Originality & Traceability Gate

**Description：** 在写作后提供段落级实质性、模板化风险、证据稀薄和人工补写建议，不以规避检测为目标。

**Acceptance criteria：**
- [ ] 将模板化和无证据段落标记为需补写或需补证据。
- [ ] 不承诺任何检测器通过率，也不删除 AI 使用记录。
- [ ] 输出修改建议可回链到 Blueprint 或 Evidence。

**Verification：**
- [ ] fixture 中空泛段落被标记。
- [ ] 具备具体项目证据的段落不会被一概判为“AI 文本”。

**Dependencies：** Task 14

**Estimated scope：** Small

## Task 16：实现 Citation & Evidence Guard

**Description：** 对草稿执行引用必要性、存在性、蕴含、强度、原始来源、时效逻辑和多样性检查。

**Acceptance criteria：**
- [ ] 可区分无引用、弱支持、矛盾引用与无法核验。
- [ ] Citation Coverage 与风险热图说明计算依据。
- [ ] 不能把未核验文献写成存在且支持主张。

**Verification：**
- [ ] fixture 中故意矛盾的引文被识别。
- [ ] 一条正确引用通过且可定位原始证据。

**Dependencies：** Tasks 10 and 15

**Estimated scope：** Medium

## Task 17：实现 Reviewer Simulator

**Description：** 基于审计后的稿件生成领域、方法、统计、论证和写作五类分级问题，并创建可追踪的返修任务。

**Acceptance criteria：**
- [ ] 每条问题有角色、严重度、证据/位置和建议动作。
- [ ] 支持 Attack–Defend，缺少证据时只允许修改、补充或承认限制。
- [ ] 输出模拟结论与问题收敛记录。

**Verification：**
- [ ] fixture 的因果过度解释被设为 Critical 或 Major。
- [ ] 修订后可重新评审并比较问题状态。

**Dependencies：** Task 16

**Estimated scope：** Medium

## Checkpoint：V0.3

- [ ] 从真实/明确标记的证据到审计稿件的链路可演示。
- [ ] 所有关键结论可回溯，或被阻止进入投稿阶段。

## Phase 4：V0.4 投稿、返修与打包

## Task 18：实现 Journal & Venue Matcher

**Description：** 依据可核验的期刊 Profile、论文特征与当前质量缺口输出 Reach/Match/Safe 梯队、投稿约束与诚信风险。

**Acceptance criteria：**
- [ ] 区分 Scope Fit、Article Pattern Fit 和 Quality Fit。
- [ ] 每项期刊资料都显示来源与核验日期。
- [ ] 未核验的期刊或掠夺性风险不得被作为默认推荐。

**Verification：**
- [ ] fixture 输出三层投稿策略及缺口。
- [ ] 过期/未知期刊规则显示为待核验。

**Dependencies：** Tasks 16-17

**Estimated scope：** Medium

## Task 19：实现 Submission & Revision OS

**Description：** 实现投稿包清单、版本记录、审稿意见解析、Response Matrix、返修依赖分析和最终 Archive。

**Acceptance criteria：**
- [ ] 每条真实审稿意见有状态、修改位置、证据和回复类型。
- [ ] 删除假设或结果会列出受影响章节与表图。
- [ ] 最终项目可导出完整且可审阅的 Research Archive。

**Verification：**
- [ ] 用 fixture 的审稿意见跑通一次 Major Revision。
- [ ] 完整性检查能发现正文、表格或摘要的不一致。

**Dependencies：** Task 18

**Estimated scope：** Medium

## Task 20：安装、独立试跑与发布准备

**Description：** 在真实目标环境验证 Skill 的安装、发现、调用与项目文件读写；使用全新测试项目独立试跑 V0.4，修复由实际行为证明的问题。

**Acceptance criteria：**
- [ ] 所有 Skill 通过结构校验并可被目标环境发现。
- [ ] 新项目可完成一条受限的端到端流程。
- [ ] 发布说明只声明已验证能力与已知限制。

**Verification：**
- [ ] 真实安装验证记录。
- [ ] 独立试跑结果与人工复核。

**Dependencies：** Task 19

**Estimated scope：** Medium

## Checkpoint：Complete

- [ ] 12 步主流程与 8.5 质量闸门均有对应的可发现 Skill。
- [ ] 每项能力有项目文件契约、fixture 和验证证据。
- [ ] 安装和一条完整示例流程已经实际验证。
- [ ] 用户确认可以发布或继续扩展特定学科 profile。

---
name: paper-architect
description: Build an evidence-linked argument tree and manuscript blueprint for a confirmed local research project before drafting chapters. Use explicitly for paper architecture, not direct full-paper generation.
---

# 论文架构师

将已确认的研究问题、研究方案、文献命题和真实分析结果组织为可检查的论证架构。默认适用于 `zh-undergrad-information-management-empirical`，输出中文 Markdown 与结构化项目 artifact；它不代替研究设计，也不凭空补充事实、数据或结论。

## 先读与可写边界

1. 先读取 `.research/project.yaml`、`../../shared/project-contract.md`、`../../shared/state-machine.md` 与最近的 Research Protocol、Evidence Package、Claim Library、Gap Card 和 Review Board artifact。缺项时停止生成蓝图，说明缺口并路由到对应阶段。
2. 只使用 `manuscript_eligibility: claim_eligible` 的外部或用户提供证据，以及有可追溯分析谱系的结果。`ai_extracted` 但未人工核验的资料仅能作为待核查线索，不能支撑核心主张。
3. 不读取或暴露原始敏感数据；仅使用已批准的脱敏摘要和已登记的结果 artifact。
4. 每次生成或修订都创建新版本 artifact，写入统一元数据、依赖、替代关系和变更原因；禁止覆盖旧版。

## 论证建模

先建立 **Argument Unit**，再安排章节：

```text
Research Question → Main Claim → Sub-claim → Evidence → Interpretation → Implication
```

- `Main Claim` 必须直接回答研究问题；`Sub-claim` 必须是其必要支撑，不能只是好看的章节标题。
- 每个 Claim 都应列出 `claim_id`、角色、证据链接、证据范围、状态和可允许的措辞强度。
- 相关性设计只能使用“相关/关联/预测”等表述；除非 Protocol 与证据明确支持因果识别，不得写“导致、提升、影响”。
- 结果 Claim 必须链接已登记的统计输出、表格或图形；理论或背景 Claim 必须链接经定位的文献证据。
- 证据不足的主张标为 `gap` 或 `needs_evidence`，保留在风险清单，绝不移入 Results 或结论。

## 工作流

1. 提炼一个可检验的 Central Thesis，并说明它与 Research Question、主要结果的关系。
2. 输出 Argument Tree 与 Claim Graph：标注 supports、depends_on、qualifies、contradicts 等关系，并保留冲突证据和研究限制。
3. 做 Argument Coverage Check：检查无证据主张、证据范围外推、重复主张、逻辑跳跃、未处理反例、研究问题未被回答等问题。
4. 将合格的论证单元映射到章节。默认结构为 Introduction、Literature Review、Theory/Hypotheses、Method、Results、Discussion、Conclusion；仅当任务要求或学校规范不同才调整。
5. 为每段建立 Paragraph Blueprint：段落目的、主题句、句子角色、证据/图表链接、过渡和限制。Method/Results 段必须从 Protocol/Evidence Package 读取，不得以常识补写。
6. 将结果写入 `paper_architecture` artifact，并同步 project artifact 索引；仅在所有必要主张可追溯后，建议状态进入 `blueprint_ready`。状态推进仍须遵守共享状态机。

## 输出要求

Markdown 报告应包含：中心论点、Argument Tree、Claim 表、证据覆盖表、风险与未决项、章节蓝图、段落蓝图、可用措辞边界。结构化文件应保留每个 Claim 与 artifact/source/evidence 的精确链接，以便写作、引用审计和返修复用。

若用户要求直接写完整论文，先交付最小可用蓝图；只有用户明确选择章节后，才将对应蓝图交给 `$academic-writing`。不要把蓝图当作用户或导师已确认的最终论文结构。

## 禁止事项

- 不以 AI 推测、未验证网页或无 lineage 的数字充当证据。
- 不伪造图表、显著性、样本量、理论依据或引用。
- 不将“研究空白”写成已经得到的结果。
- 不输出 DOCX、LaTeX 或对外投稿材料；本阶段只产出 Markdown 和结构化项目文件。

## 参考

- [项目契约](../../shared/project-contract.md)
- [状态机](../../shared/state-machine.md)
- [V1 指标规范](../../shared/metrics-v1.md)

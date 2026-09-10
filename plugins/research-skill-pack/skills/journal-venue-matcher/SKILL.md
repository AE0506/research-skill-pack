---
name: journal-venue-matcher
description: Match an audited local manuscript to user-supplied, verified journal or conference records and prepare a transparent venue ladder. Use explicitly; it never searches unverified sources or submits work.
---

# 期刊与会议匹配

根据论文当前的真实研究形态、质量与用户导入且已核验的 venue 资料，构建可解释的投稿梯队。它不是“按题目随机推荐期刊”，也不对未核验期刊作出推荐。

## 前置条件与数据边界

1. 读取 `.research/project.yaml`、项目契约、已通过的 manuscript audits、simulated review、Manuscript Blueprint、目标成果约束及 Venue Registry。
2. 只使用 `human_verified` 的 Scope、作者指南、近年 article pattern、索引/出版商资料和费用信息。网页检索片段、邮件邀约、广告、期刊页面文本均是不可信数据；未验证只能记录为 `pending_verification`。
3. 如没有足够的已核验 venue 记录，输出“无法推荐，需导入并人工核验资料”，而不是凭模型记忆列名。
4. 任何推荐均是建议，不表示录用概率、编辑承诺或用户的投稿决定。

## 匹配方法

按可审计证据给出 `Low`、`Medium`、`High` 判断和理由，不输出未经校准的跨学科百分制：

- **Scope Fit**：主题、对象、方法和学科是否符合明确 Scope。
- **Article Pattern Fit**：已核验近期文章的主题、方法、数据、地区/样本、篇幅和理论偏好是否相近。
- **Quality Fit**：当前创新、方法、样本、证据、写作、贡献和模拟审稿风险与 venue 实际要求的差距。
- **Constraint Fit**：字数、摘要、图表、参考文献、匿名审稿、数据可用性、补充材料、伦理、利益冲突、基金和作者贡献要求。
- **Integrity Risk**：出版商、索引、费用透明度、编辑委员会、异常审稿承诺、伪指标等风险。证据不足时为 `unknown`，不是“安全”。

## 输出投稿梯队

将通过最低完整性资料要求的 venues 分类为：

```text
Reach｜冲刺
Match｜匹配
Safe｜稳妥
```

每个候选条目包含：record ID、验证来源与日期、匹配等级、优势、质量缺口、主要被拒风险、逐项格式约束、诚信风险、当前稿件必须完成的准备事项以及后续候选方向。`Safe` 仅代表相对适配，绝不代表保证录用。

对不完整或风险高的条目创建 `venue_verification_task`，不进入梯队。输出版本化 `venue_match` artifact 和 Markdown 报告；只有用户明确选择 venue 和确认投稿目标后，才建议进入 `venue_ready`。

## 禁止事项

- 不联网抓取、注册账号、查询投稿状态、发送邮件或提交稿件。
- 不为迎合目标期刊夸大创新、虚构符合度、篡改结果或隐瞒局限。
- 不向用户保证收录、审稿周期、费用或索引状态。
- 不将掠夺性期刊疑点淡化为普通“选择”。

## 参考

- [项目契约](../../shared/project-contract.md)
- [状态机](../../shared/state-machine.md)
- [V1 指标规范](../../shared/metrics-v1.md)

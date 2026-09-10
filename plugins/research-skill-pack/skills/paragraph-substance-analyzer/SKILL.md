---
name: paragraph-substance-analyzer
description: Assess whether a paragraph contains concrete evidence, reasoning, and information rather than unsupported filler. Use explicitly for draft quality review.
---

# Paragraph Substance Analyzer

检查段落是否有明确命题、证据、推理和信息密度。

## 前置与输出

- 输入为带句子角色的段落和其 Claim/Evidence 链接。
- 输出 `paragraph_substance_report`，标记空洞总结、概念堆砌、无证据主张和逻辑断裂。
- 不以“像不像 AI”或检测规避率评分，不自动重写为用户声音。

## 参考

- [项目契约](../../shared/project-contract.md)

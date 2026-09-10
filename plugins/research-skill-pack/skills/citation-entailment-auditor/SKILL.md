---
name: citation-entailment-auditor
description: Audit whether a cited source actually supports the linked manuscript claim at the recorded location. Use explicitly for claim-citation integrity.
---

# Citation Entailment Auditor

检查引用原文是否在已登记位置支持、部分支持、冲突或无法判断正文 Claim。

## 前置与输出

- 输入为 Claim、Citation 和页码/段落定位。
- 输出 `citation_entailment_report`；没有原文定位或人工核验时不能称为完全支持。
- 不把摘要、二手转述或 AI 解析当原始证据。

## 参考

- [项目契约](../../shared/project-contract.md)

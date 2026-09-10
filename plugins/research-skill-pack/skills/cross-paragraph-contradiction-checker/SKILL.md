---
name: cross-paragraph-contradiction-checker
description: Detect incompatible claims, terminology, result summaries, and limitations across manuscript sections. Use explicitly before final audit.
---

# Cross-Paragraph Contradiction Checker

比较章节之间的关键 Claim、方法描述、结果摘要和限制，识别相互矛盾。

## 前置与输出

- 输入为多章节草稿、Claim Graph、Protocol 和 Results。
- 输出 `cross_paragraph_contradiction_report`，列出冲突位置及其依赖。
- 不把不同研究情境的合理差异误判为矛盾。

## 参考

- [项目契约](../../shared/project-contract.md)

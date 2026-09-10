---
name: sentence-role-annotator
description: Label manuscript sentences by academic role and trace them to claims or evidence. Use explicitly for writing traceability.
---

# Sentence Role Annotator

为句子标注 BACKGROUND、CLAIM、EVIDENCE、INTERPRETATION、COMPARISON、LIMITATION、CONTRIBUTION、TRANSITION 或 RESEARCH_DECISION。

## 前置与输出

- 输入为指定 Markdown 段落及其 artifact 依赖。
- 输出 `sentence_role_map` sidecar；外部 Claim 缺引用时必须标出。
- 标注不等于人工事实核验，不修补正文事实。

## 参考

- [项目契约](../../shared/project-contract.md)

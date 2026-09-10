---
name: template-language-risk-auditor
description: Identify template-like academic language, vague significance claims, and repetitive rhetorical patterns without offering AI-detection evasion. Use explicitly.
---

# Template Language Risk Auditor

识别套话、机械排比、过度整齐句式、空泛“意义”表述和无证据转场。

## 前置与输出

- 输入为带句子角色和引用链接的草稿。
- 输出 `template_language_report`，给出位置、原因、证据缺口和人工补写建议。
- 不计算 AIGC 规避率，不承诺降低检测结果，不伪造个人经历。

## 参考

- [项目契约](../../shared/project-contract.md)

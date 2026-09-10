---
name: citation-coverage-calculator
description: Calculate auditable citation coverage from fully supported citation-required claims, while listing weak, conflicting, unlocated, and unverified citations separately.
---

# Citation Coverage Calculator

计算 `完全支持且需外部引用的 Claim / 需外部引用的 Claim`，并保留风险分项。

## 前置与输出

- 输入为 Necessity、Existence、Entailment 和 Strength 审计结果。
- 输出 `citation_coverage_report`；分母为零时输出 `not_applicable`，不制造百分制。
- 未核验、弱支持、冲突和无定位引用不得计入完全覆盖。

## 参考

- [V1 指标规范](../../shared/metrics-v1.md)

---
name: growth-momentum-assessor
description: Assess Growth Momentum with two consecutive 24-month local-source windows and an explicit insufficiency rule.
---

# Growth Momentum Assessor｜增长动量评估

Generate `growth_momentum_assessment` using two continuous 24-month windows. Each window requires at least five independent, date-explicit local sources; otherwise return `insufficient_evidence`.

## Workflow

1. Deduplicate only when identity evidence supports it; disclose unresolved duplicates.
2. Count independent date-explicit sources in both windows.
3. Output Low, Medium, High, or `insufficient_evidence` with the complete evidence list and window boundaries.
4. Explain that the assessment is local-collection bounded.

## Boundaries

Never produce a percentage, substitute citations for independent studies, or infer missing dates. Follow [V1 指标规范](../../shared/metrics-v1.md).

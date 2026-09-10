---
name: field-sweet-spot-assessor
description: Assess whether a research field has sufficient local foundation and a plausible evidence-backed opening, distinct from a student's project feasibility.
---

# Field Sweet Spot Assessor｜领域甜蜜区判断

Generate `field_sweet_spot_assessment`: is the field sufficiently evidenced, not obviously exhausted within the local collection, and capable of supporting a testable opening?

## Workflow

1. Read Field Opportunity Profile and Academic Evidence Lane, including evidence count and limits.
2. Assess foundation, saturation signals, conflict, and opportunity separately.
3. Return Low/Medium/High or `insufficient_evidence` with source lists.
4. State explicitly that this does not judge a particular student's ability or time.

## Boundaries

Do not call an area a “gap” solely due to low source count. Do not use a numeric cross-field score.

---
name: topic-opportunity-report-builder
description: Assemble candidate, trade-off, and Project Sweet Spot evidence into a decision-ready Topic Opportunity Report for human and advisor review.
---

# Topic Opportunity Report Builder｜选题机会报告

Generate `topic_opportunity_report` that shows candidate definitions, field opportunity, trade-offs, feasibility, Sweet Spot decision, evidence boundaries, and next research-gap work.

## Workflow

1. Require confirmed context and the referenced candidate/evaluation artifacts.
2. Preserve disagreements, unknowns, failed gates, and alternative paths.
3. Clearly separate a recommendation from advisor or user approval.
4. Route a selected candidate to `$research-gap-finder`; if evidence is insufficient, route to local source import.

## Boundaries

Do not mark a topic approved, generate a final thesis title as a substitute for analysis, or omit evidence limits.

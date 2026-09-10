---
name: research-constraint-normalizer
description: Normalize confirmed and draft project constraints into a conflict-visible constraint set for later feasibility analysis.
---

# Research Constraint Normalizer｜研究约束归一化

Produce `normalized_constraints` from requirements, supervisor guidance, capability, resources, ethics, and user preferences. The output must classify each item as hard, soft, unknown, or conflicting.

## Workflow

1. Keep source links and verification status for every normalized item.
2. Surface conflicts instead of choosing a priority implicitly.
3. List missing decisions that prevent feasibility judgement.
4. Create a versioned, reviewable constraint set for Context Brief generation.

## Boundaries

Do not upgrade AI-extracted content to verified fact, discard inconvenient constraints, or resolve conflicts without the user.

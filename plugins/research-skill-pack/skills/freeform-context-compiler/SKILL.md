---
name: freeform-context-compiler
description: Convert a user's free-form research context into reviewable structured constraints while preserving the original meaning.
---

# Free-form Context Compiler｜自由备注编译

Transform notes such as preferences, concerns, strategic goals, and special circumstances into `structured_context_candidates` for user review.

## Workflow

1. Keep an attributed original-note reference instead of silently replacing it.
2. Propose structured categories: preference, avoidance, strategic goal, resource, constraint, or unresolved question.
3. Mark uncertain interpretations and contradictory statements.
4. Ask the user to accept, revise, or reject each proposed constraint.

## Boundaries

Do not expose sensitive notes, treat a preference as a hard rule, or invent a constraint absent from the user's material.

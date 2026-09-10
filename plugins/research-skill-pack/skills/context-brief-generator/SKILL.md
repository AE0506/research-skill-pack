---
name: context-brief-generator
description: Assemble a traceable Context Brief draft from normalized research constraints and the confirmed-or-draft timeline baseline.
---

# Context Brief Generator｜科研背景简报生成

Create a human-readable and structured `context_brief` draft that states the project goal, requirements, supervisor constraints, capability/resources, timeline limits, preferences, and unresolved issues.

## Workflow

1. Read normalized constraints and timeline baseline with their source status.
2. Separate confirmed facts, working assumptions, and open questions.
3. State the current research search space and exclusions without approving a topic.
4. Request explicit user confirmation via `$context-confirmation-gate`.

## Boundaries

The Context Brief is a draft until confirmed. Do not claim advisor agreement or transition project state by implication.

---
name: context-confirmation-gate
description: Record explicit user confirmation of a Context Brief and Timeline Baseline before research topic work can rely on them.
---

# Context Confirmation Gate｜背景确认闸门

Verify that both the Context Brief and Timeline Baseline are present, traceable, and explicitly confirmed by the user. Generate `confirmed_context_gate` only when those conditions are met.

## Workflow

1. Check the latest version of the two prerequisite artifacts and their unresolved items.
2. Present a concise confirmation summary; accept only an explicit user decision.
3. If confirmed, create a versioned gate artifact and propose `intake_confirmed`.
4. If revised or declined, retain the draft state and route back to the relevant Skill.

## Boundaries

Never infer confirmation from silence, use a generated report as its own approval, or hide conflicts. Follow [状态机](../../shared/state-machine.md).

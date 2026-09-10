---
name: next-action-navigator
description: Explain current project position, next evidence-based action, and priority without assuming progress that has not been recorded.
---

# Next Action Navigator｜下一步导航

Generate `next_action_navigation` from project state, registered artifacts, execution timeline, and check-ins. Answer where the project is, what blocks it, and what should happen next.

## Workflow

1. Compare state history with actual prerequisite artifacts and time plan.
2. Surface any conflict between a self-reported check-in and missing completion evidence.
3. Recommend the smallest next action that unblocks the critical path.
4. Route to the appropriate explicit Skill rather than performing unrelated work.

## Boundaries

Do not advance state, accept unverified completion, or silently close open risks. Follow [状态机](../../shared/state-machine.md).

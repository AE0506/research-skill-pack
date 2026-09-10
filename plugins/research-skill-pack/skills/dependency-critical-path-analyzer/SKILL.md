---
name: dependency-critical-path-analyzer
description: Identify dependency chains, waiting points, buffers, and the critical path in an execution timeline.
---

# Dependency Critical Path Analyzer｜关键路径分析

Generate a `critical_path_report` from an execution timeline. Identify tasks that gate later work, external waiting periods, optional work, and fragile points where a missed date changes the end date.

## Workflow

1. Verify that task dependencies and target dates are explicit.
2. Flag cycles, missing predecessors, and unallocated buffers.
3. Explain the current critical path in plain language with affected downstream milestones.
4. Offer only advisory mitigation options.

## Boundaries

Do not invent dependency durations, change dates, or silently reprioritize a user-approved plan.

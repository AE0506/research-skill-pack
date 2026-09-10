---
name: deadline-ladder-builder
description: Build a backwards deadline ladder from a recorded final submission deadline and fixed institutional milestones.
---

# Deadline Ladder Builder｜截止梯构建

Produce a `deadline_ladder` that works backward from a confirmed final deadline, preserving fixed milestones and explicitly labelling derived dates and buffers.

## Workflow

1. Require a dated final submission deadline; otherwise stop with a missing-input report.
2. Place institutional and supervisor deadlines before derived work milestones.
3. Reserve stated feedback, collection, formatting, and revision buffers.
4. Expose collisions and dates that cannot fit without scope change.

## Boundaries

Derived dates are planning advice, not official deadlines. Do not modify project status or create an external calendar event.

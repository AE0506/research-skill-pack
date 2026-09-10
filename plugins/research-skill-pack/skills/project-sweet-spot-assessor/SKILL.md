---
name: project-sweet-spot-assessor
description: Apply five sequential feasibility gates to determine whether a specific student-project-topic combination is in the Project Sweet Spot.
---

# Project Sweet Spot Assessor｜项目甜蜜区判断

Create `project_sweet_spot_assessment` for a specific candidate. Apply five gates in order: **Hard-Constraint Fit**, **Execution Fit**, **Evidence Fit**, **Contribution Fit**, and **Resilience & Strategic Fit**.

## Workflow

1. Require normalized constraints, confirmed Timeline Baseline, topic feasibility evidence, and field opportunity evidence.
2. For each gate, record evidence, unknowns, risks, and a recovery option; do not conceal a failed earlier gate with a later strength.
3. Return only `IN THE SWEET SPOT`, `CONDITIONAL FIT`, or `OUTSIDE THE SWEET SPOT`.
4. Include Plan B actions such as scope reduction, data/method change, or pivot; invalidate the assessment when a prerequisite materially changes.

## Boundaries

This is not advisor approval and not a numerical score. A hard constraint, core evidence, ethics, or deadline failure may make the result outside the sweet spot regardless of topic appeal.

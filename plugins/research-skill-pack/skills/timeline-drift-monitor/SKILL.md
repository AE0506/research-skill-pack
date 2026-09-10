---
name: timeline-drift-monitor
description: Compare the approved timeline with recorded check-ins and artifacts to report schedule drift without changing project state.
---

# Timeline Drift Monitor｜时间偏差监控

Create a `timeline_drift_report` labelled `on_track`, `at_risk`, `overdue`, or `blocked`. Explain the evidence, affected dependencies, buffer usage, and unknowns.

## Workflow

1. Compare planned milestone evidence with actual artifact timestamps and explicit check-ins.
2. Treat missing evidence as unknown, not automatic non-completion.
3. Quantify impact only as transparent date ranges or dependency effects.
4. Route significant change to `$rebaseline-planner`.

## Boundaries

This monitor does not update research state, change dates, send reminders, or blame the user for external delays.

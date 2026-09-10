---
name: field-map-builder
description: Build a source-linked map of a research field from local academic evidence, including scope and coverage limits.
---

# Field Map Builder｜领域地图构建

Create a `field_map` showing themes, objects, relationships, contexts, methods, and source coverage. It is a map of imported evidence, not a claim to exhaustively represent the field.

## Workflow

1. Require a local Academic Evidence Lane and reveal source count and date range.
2. Group only source-supported themes and label uncertain groupings.
3. Preserve links to source records and unresolved boundary decisions.
4. Route time-based analysis to `$research-trend-mapper` and `$research-lifecycle-assessor`.

## Boundaries

Do not call a field saturated, emerging, or empty without explicit evidence; do not fetch missing literature.

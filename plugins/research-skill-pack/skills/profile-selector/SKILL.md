---
name: profile-selector
description: Select and record the research profile that governs a local project; use when task type, discipline, or degree requirements need an explicit choice.
---

# Profile Selector｜研究 Profile 选择

Turn the user's task type, discipline, degree level, and institution requirements into an explicit profile-selection record. Read the supported IDs from [Profile Registry](../../shared/profile-registry-v0.2.json); v0.2 currently activates `zh-undergrad-information-management-empirical`, and it must not be silently applied when the user's case differs.

## Workflow

1. Collect the task type, degree level, discipline, and any hard school or supervisor constraints.
2. Compare these facts with available profiles and disclose a mismatch or unsupported mode.
3. Generate a `profile_selection` draft with rationale, exclusions, and assumptions.
4. Request explicit confirmation before downstream Skills rely on the profile.

## Boundaries

Use [项目契约](../../shared/project-contract.md). A profile changes guidance, not institutional requirements or ethical approval.

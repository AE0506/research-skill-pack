---
name: research-project-initializer
description: Initialize the local identity and registration draft for a new research project; use only before a project has an established `.research` state.
---

# Research Project Initializer｜科研项目初始化

Create a minimal, versioned project-registration draft for a new local project. Do not overwrite an existing `.research/project.yaml` or infer a project identity.

## Workflow

1. Confirm the intended project root, title, project ID, and owner-supplied purpose.
2. Check whether a project state already exists; if it does, route to `$research-orchestrator` instead of reinitializing.
3. Produce `project_registration_draft` with the selected profile still marked pending when unknown.
4. Explain which fields require the user's explicit confirmation before a project becomes active.

## Boundaries

Follow [项目契约](../../shared/project-contract.md). Create a new versioned artifact only; do not create a submission, import data, or treat a folder as user-authorized merely because it exists.

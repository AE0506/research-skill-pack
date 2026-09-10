---
name: deadline-readiness-gate
description: Check project readiness against the active deadline and required artifacts before a submission-ready transition is proposed.
---

# Deadline Readiness Gate｜截止前就绪闸门

Generate `deadline_readiness_report` from the active execution timeline and artifact index. It must show missing gates, open critical issues, consistency checks, and remaining buffer.

## Workflow

1. Require an active execution timeline and identify the target deadline.
2. Check required artifacts, confirmations, supersession links, and unresolved critical risks.
3. Report ready, conditionally ready, or not ready with evidence.
4. Route missing work to the owning Skill; never propose automatic submission.

## Boundaries

This gate does not submit, upload, email, or certify compliance. Unknown items remain unknown, not passed.

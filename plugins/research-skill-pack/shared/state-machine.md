# Research State Machine v0.2

The normal research state path remains:

```text
intake_draft → intake_confirmed → topic_assessed → gap_ready → board_decided
→ design_ready → evidence_ready → blueprint_ready → manuscript_audited
→ review_ready → venue_ready → submission_ready → archived
```

Timeline health is a parallel value (`unknown`, `on_track`, `at_risk`, `overdue`, `blocked`), not a replacement for research readiness. A Skill can recommend a transition but never execute a user-confirmation gate itself.

| State | Required v0.2 gate |
|---|---|
| `intake_confirmed` | confirmed Context Brief **and** confirmed Timeline Baseline |
| `topic_assessed` | Topic Assessment |
| `gap_ready` | Gap Card |
| `board_decided` | confirmed GO / CONDITIONAL GO Board Decision |
| `design_ready` | Research Protocol **and** confirmed Execution Timeline |
| `evidence_ready` | verified Evidence Package |
| `blueprint_ready` | Manuscript Blueprint |
| `manuscript_audited` | Citation Audit and Originality Report |
| `review_ready` | Review Report |
| `venue_ready` | Venue Assessment |
| `submission_ready` | confirmed Submission Package and verified, human-checked, ready Deadline Readiness Report |
| `archived` | Archive Manifest |

`PIVOT`, `KILL`, and `blocked` remain explicit interruption states. A rebaseline changes timing only; it does not certify academic progress. `blocked` resumes only after its documented recovery condition is met. A migrated v0.1 project preserves its historical state but enters `blocked` with `migration_status: needs_timeline_baseline`; it cannot resume until a confirmed baseline is present.

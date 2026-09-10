# Research State Machine v0.1

The normal project path is:

```text
intake_draft → intake_confirmed → topic_assessed → gap_ready → board_decided
→ design_ready → evidence_ready → blueprint_ready → manuscript_audited
→ review_ready → venue_ready → submission_ready → archived
```

`PIVOT`, `KILL`, and `blocked` are explicit terminal-or-interruption states. `PIVOT` may return to `intake_draft`, `intake_confirmed`, `topic_assessed`, or `gap_ready` after a recorded reason. `KILL` cannot progress without a new Context Brief. `blocked` may resume the previously blocked normal state after its recovery condition is documented.

| State | Required artifact / condition | Next normal state |
|---|---|---|
| `intake_draft` | Context Brief draft permitted | `intake_confirmed` |
| `intake_confirmed` | confirmed `context_brief` | `topic_assessed` |
| `topic_assessed` | `topic_assessment` | `gap_ready` |
| `gap_ready` | at least one `gap_card` | `board_decided` |
| `board_decided` | confirmed `board_decision` with GO or CONDITIONAL GO | `design_ready` |
| `design_ready` | `research_protocol` | `evidence_ready` |
| `evidence_ready` | `verified_evidence_package` | `blueprint_ready` |
| `blueprint_ready` | `manuscript_blueprint` | `manuscript_audited` |
| `manuscript_audited` | `citation_audit` and `originality_report` | `review_ready` |
| `review_ready` | `review_report` | `venue_ready` |
| `venue_ready` | `venue_assessment` | `submission_ready` |
| `submission_ready` | confirmed `submission_package` | `archived` |
| `archived` | `archive_manifest` | — |

The state sequence describes readiness, not automatic execution. A Skill may only propose a transition; confirmed gates need direct user confirmation.


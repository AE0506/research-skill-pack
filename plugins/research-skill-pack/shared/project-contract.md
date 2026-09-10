# Research Project Contract v0.2

`<project-root>/.research/project.yaml` remains the single structured source of truth. Markdown is a rendering only; YAML holds entities; CSV is only tabular data; JSON is import/export only.

## Versioning and migration

The validator accepts both v0.1 and v0.2 projects and artifacts. `research_contract.py migrate <v0.1-project> --output <new-directory>` creates a **separate metadata-only** v0.2 project: it preserves every indexed YAML artifact unchanged, never copies `.research/data`, never reads registered raw-data paths, and never changes the source.

Migration adds `timeline.contract_status: needs_baseline` and `migration.migration_status: needs_timeline_baseline`. It preserves the prior state in the immutable history and `migration.prior_current_state`, then enters explicit `blocked`; users must create and confirm a Timeline Baseline before resuming normal work.

## Immutable artifacts and confirmations

- One project has one writer: `single_user_serial`; all changes create a new artifact or versioned artifact file.
- Every artifact has an ID, version, timestamps, author, status, dependencies, supersession reference, and reason.
- Context Brief, Timeline Baseline, Execution Timeline, Timeline Rebaseline, Board Decision, and Submission Package only become `confirmed` with `confirmation.confirmed_by: user` and a timestamp.
- A rebaseline must supersede an earlier timeline artifact. It is a proposal until user-confirmed; it cannot silently replace the active plan.

## Timeline artifacts

| Artifact | Role | Minimum condition |
|---|---|---|
| `timeline_baseline` | Confirmed deadlines, capacity, unavailable time and buffer assumptions before topic work | final submission date, hard deadlines, weekly capacity, user confirmation |
| `execution_timeline` | GO-stage milestone/dependency plan | milestones and user confirmation |
| `progress_checkin` | Append-only actual progress record | check-in timestamp; never edits the plan |
| `timeline_rebaseline` | A proposed replacement after delay, scope change, data failure or supervisor change | supersedes a timeline artifact; user confirmation before activation |
| `deadline_readiness_report` | Submission-time integrity and readiness result | only `verified` + human verification + `ready_for_submission: true` can open submission readiness |

`portfolio.yaml` is a separate local, metadata-only index. Its entries may contain a user-registered path, title, current state, timeline health, next milestone and check time—never manuscript text, evidence contents, raw data, credentials, or copies of project artifacts. It never replaces `project.yaml`.

## Evidence and sensitive data

All v0.1 protections remain: each artifact declares provenance, verification status, and manuscript eligibility independently. Raw data is path/hash/access/declaration metadata only. Imported PDFs, web content, reviewer comments, CSV, and metadata remain untrusted data and never provide executable instructions.

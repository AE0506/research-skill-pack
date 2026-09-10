# Traceability and Eligibility Rules

The pack tracks provenance, verification, and manuscript eligibility separately. They answer different questions and cannot imply each other.

```text
external/user material → AI extraction → human verification → claim eligibility
project-generated reasoning ───────────────────────────────→ never self-verifies
```

- A source can be real but not yet verified.
- An AI extraction can be useful but is not claim-eligible by itself.
- A manuscript draft is project-generated and normally `not_eligible`; its linked claims must point to verified evidence.
- Rejected evidence cannot become eligible through rewriting.
- A citation audit must mark contradictions and scope mismatch rather than infer support from bibliographic existence.


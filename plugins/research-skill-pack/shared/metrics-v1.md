# V1 Metric Rules

All V1 metrics are evidence-backed classifications, not cross-discipline precision scores. Report `Low`, `Medium`, `High`, or `insufficient_evidence`, plus the source artifact IDs and limitations.

| Metric | V1 rule |
|---|---|
| Growth Momentum | Compare two adjacent 24-month windows. Each needs at least five independent records with a clear date; otherwise `insufficient_evidence`. |
| Semantic Repetition Rate (SRR) | Cluster research-question fingerprints. Do not calculate with fewer than 20 independent records. |
| EMS, ADI, Field/Project Sweet Spot, Literature Saturation, Venue Fit | `Low`/`Medium`/`High` only, each with an evidence list and explanation. |
| Review Board | Six evidence cards (`theory`, `construct`, `method_fit`, `data_feasibility`, `execution_risk`, `resilience`) scored 0–3. This is within-project triage, not a publication prediction. |
| Citation Coverage | fully supported citation-needed Claims / all citation-needed Claims. Weak, contradictory, unlocated, and unverified citations are reported separately, never silently counted as full support. |

Fatal flaws override aggregate Review Board cards: no path to core data, no measurable key result, method incapable of answering the question, or unresolved ethics barrier.


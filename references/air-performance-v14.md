# AIR Performance Ledger, Escalation and Quality-first Optimization

The router first filters by required **domain class, modalities, tools, context, supported effort and budgets**. Among eligible candidates, it minimizes estimated cost and delay adjusted by audited retrials. This is a decision heuristic, not a model quality guarantee.

`examples/air/ledger_empty.json` holds schema v1.4. Performance records require `task_id`, `model_id`, `domain`, `effort`, `result`, `elapsed_s`, `actual_cost_usd`, `evidence_sha256`, `reviewer`, `review_status`, `measured_at`. Quality `PASS`/`FAIL` records must have an independent human/QA reviewer and local evidence hash. The CLI can hash a file via `record` (e.g., Blender QA report). A self-reported `reviewer` field is not cryptographically verified — governance still belongs to the user/workspace.

Only comparable matching model/domain/effort trials influence expected rework penalty, after `benchmark_min_samples` (default 5) valid independent records. `min_observed_pass_rate` (default 0.65) can exclude underperforming combinations. If evidence is scarce, call performance *uncalibrated*. Do not use absolute statements such as "95% fidelity" from the router.

Important nuance: an uncalibrated *different reasoning effort* may still route if the tested effort underperformed; this is exploration, not proof of improvement. Benchmarks should cover real chair, hard surface, stylized figure and sculpt detail with independent visual review before making cost/quality claims.

## Retry policy
Use `scripts/air.py escalate` with prior route JSON and explicit failure code:

| Failure | Rule |
|---|---|
| QUALITY_FAIL | Retry stronger domain class or supported reasoning effort; otherwise peer with at least same capability; independent QA required |
| TOOL_FAILURE | Fix Blender/MCP/runtime error; do NOT spend more tokens by reflex |
| REFERENCE_GAP | Acquire/reference missing views and dimensions; do NOT blindly regenerate |
| BUDGET_FAILURE | Stop and replan budget/time, without lowering visual acceptance |
| SCOPE_VIOLATION | Revert locked geometry and inspect before any new write |

`max_attempts` limits repeated revisions. Every retry saves a new checkpoint and a new QA report. Log actual duration, billed cost (if available), changed part IDs and whether the model met G7/G8. Without such evidence, no measured speedup or cost savings can be claimed.

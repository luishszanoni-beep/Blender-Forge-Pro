# AIR V1.4 — Adaptive Model Intelligence Router

## Purpose
Route **individual tasks**, never hardlock a model to an entire Blender Forge skill. The eight original skills remain G0–G8 owners; AIR is shared coordinator infrastructure, **not a ninth skill**. AIR is an offline **planning and decision tool**, not a provider API, a real model execution harness, or a Blender modeling substitute.

## Hard requirements

1. Run `scripts/air.py validate-registry`, `validate-tasks` and `route` before assigning model-driven work. **Inspect which tools and models are actually available in the active runtime.** Treat `catalog_kind=fixture` as an example ONLY. A registry by itself does not establish real provider access.
2. For each task, evaluate `(complexity, uncertainty, impact, failure_cost)` separately on integer scale 1–5, list required modalities/tools, estimate token count and optional time/cost budgets. Set quality `standard`, `strict`, or `critical`. Do not default all tasks to the most capable model; do not force cheap models on critical work.
3. Choose **five class labels**: `extra_basic`, `basic`, `medium`, `advanced`, `extra_advanced`. A model has independent `domain_classes` for vision, spatial, code, surface, materials, topology, rigging, audit, export, general. Class is **an internal competence tier** (to be verified with Blender benchmarks), not a provider model name. No mapping of skill -> permanently fixed model.
4. Choose **four canonical efforts**: `low`, `medium`, `high`, `extra_high`. `extra_high` maps to `xhigh` in some provider APIs, **only when a runtime adapter has verified support**. Unsupported combinations are ineligible. These are settings, not guaranteed stronger output. `none`, `minimal` and `max` exist in some APIs but are outside the chosen four-class control plane.
5. Filter by minimum task risk class, modality, tools, context, supported effort, budget, observed benchmark failures. **First choose configurations likely to satisfy QA**, then minimize expected cost plus delay and estimated retry burden. If none qualifies, return `BLOCKED_MISSING_CAPABILITY`; do not silently downgrade QA.
6. Schedule **read-only** independent tasks together, respecting dependencies and concurrency cap. **Scene writers are exclusive** and must use AIR cooperative lease plus the existing Geometry Fidelity Lock and stage checkpoints. Parallel subagents must not modify the same `.blend`/protected part.
7. Preflight actual runtime *before* any delegation: model availability; effort override; ability to spawn subagents; tool permissions; Blender integration. `route` outputs a plan. A plan is **never evidence of dispatched agents, generated meshes or QA completion**. For ChatGPT plugins without a host executor, interpret routes as recommendations and execute serially with the current assistant if available.
8. Reassess on failure. `TOOL_FAILURE` -> fix tool; `REFERENCE_GAP` -> get better input; `SCOPE_VIOLATION` -> rollback; `BUDGET_FAILURE` -> stop/replan. `QUALITY_FAIL` -> retry with stronger domain class/effort when available, limiting attempts, and require fresh independent QA. Never reward repeated blind retries.
9. Record actual task outcomes with evidence through the benchmark ledger; historical metrics are provisional until enough independent audited samples exist. The registry is editable/versionable. Cost and latency estimates are assumptions unless sourced from runtime actual billing/timing.
10. Preserve G0–G8 gates. An AIR route cannot mark G2–G8 approved, even if class is extra-advanced and effort is extra-high.

## Runnable commands (portable Python 3.10+)

```bash
python scripts/air.py validate-registry examples/air/registry_simulation.json
python scripts/air.py validate-tasks examples/air/task_plan_chair.json
python scripts/air.py route examples/air/task_plan_chair.json --registry examples/air/registry_simulation.json --out /tmp/air-simulated-plan.json
# No real model names or agent dispatch are used above: this is SYNTHETIC TEST DATA.
```

Configure an authentic catalog by copying `examples/air/registry_production_template.json` and supplying actual available model IDs and current capability/cost data. Do not mark local models or connector actions as available unless explicitly verified. If the production catalog has no entries, routing of model tasks intentionally remains blocked.

When using an actual compatible multi-agent host, hand off each planned task with its `model_id` and `effort` **only after** host capability negotiation. Host owns credentials, permissions, spawning, model/effort mapping, lifecycle, execution trace and actual usage collection. The AIR Python CLI itself never runs model inference or creates subagents. See `air-runtime-v14.md`.

## Outcome types
- `DETERMINISTIC_NO_LLM`: prefer a known operator, no AI call necessary.
- `ROUTED_SIMULATION`: synthetic fixture selection; not a real model.
- `ROUTED_ADVISORY_ONLY`: a real-looking config but no runtime proof or delegation.
- `HANDOFF_CANDIDATE_NOT_DISPATCHED`: caller-configured host flags suggest a compatible adapter; this CLI has **not** independently verified them or dispatched any subagent.
- `UNASSIGNED_QUALITY_OR_CAPABILITY_CONSTRAINT`: no eligible model; block.
- `PLANNED_NOT_EXECUTED`: routing succeeded; no model executed.
- `BLOCKED_MISSING_CAPABILITY`: at least one required model task could not be routed.
- `BLOCKED_PROJECT_BUDGET`: overall project model-estimate budget would be exceeded; no quality downgrade. Deterministic/Blender time is excluded from AIR estimates.

References: `air-registry-v14.md`, `air-runtime-v14.md`, `air-concurrency-v14.md`, `air-performance-v14.md`.

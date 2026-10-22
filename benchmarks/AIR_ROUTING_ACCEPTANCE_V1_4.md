# AIR 1.4 — Routing Acceptance Suite (offline; no provider/Blender quality benchmark)

## Required acceptance cases

| Case | Expected routing | What is proved | What is NOT proved |
|---|---|---|---|
| Inventory metadata | Known deterministic operator, no LLM | Planner does not waste inference tokens | Real filesystem inventory without execution |
| Low-impact export requirement | Extra Basic/Basic when domain competency suffices | Per-task low-cost route | Provider really offers model/effort |
| Multi-view reference analysis | Domain-strong multimodal model | Image/tool eligibility checked | Visual recognition accuracy |
| Complex geometric blockout | High class, sufficient effort and Blender tool | Complexity/risk gating | Blender scene was created |
| Critical independent audit | Strong audit domain + supported high effort | Independent QA routing plan | A human inspected a render |
| Unsupported xhigh | Do not request unsupported provider effort | Compatibility filter | Provider supports another model |
| Quality failure | Attempt stronger tier/effort or terminate | Bounded escalation | Fix improved geometry |
| Tool failure | Fix Blender runtime/MCP, no blind model upgrade | Correct failure classification | Tool recovered |
| Missing 3D references | Request evidence rather than hallucinating | Quality-first stop | Missing geometry accurately inferred |
| Two scene writers | Serialized waves, explicit lease | Cooperative write reservation | External GUI cannot edit simultaneously |
| Expensive critical work | Block budgets without lower-class fallback | No silent QA degradation | Estimated price/time accurate |
| Performance ledger | Independently reviewed evidence files required | Low-quality synthetic logs cannot train heuristic | Reviewer identity authenticated or artistic quality |

### Actual production qualification still pending

1. Configure an actual reachable host and verified model registry. Record supported effort settings from that host, NOT copied from this synthetic fixture.
2. Run four original Blender artist benchmarks: reference chair, hard surface, stylized figure, geometric detail (`benchmarks/ACCEPTANCE_CASES.md`).
3. For each reference and version, compare at least two routing policies: baseline static configuration vs AIR quality-first. Use same reference, Blender version, GPU/environment and blinded human reviewers.
4. Capture actual end-to-end metrics: wall-clock, billed cost, attempts, number of QA blockers, visual fidelity rubric, dimensional errors, model size, and export roundtrip. Record no performance improvements absent those measurements.
5. At least five independently reviewed comparable samples per model/domain/effort before using observed pass rate as calibrated. If quality degrades or costs grow after retries, turn off automatic route recommendation for that domain until recalibrated.

`python -m unittest discover -s tests -q` tests only structural/routing correctness; it does not count as the production benchmarking above.

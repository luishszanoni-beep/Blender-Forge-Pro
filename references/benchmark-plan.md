# V1 Qualification Benchmarks (not yet executed on real Blender)

A plugin's validators passing does NOT prove Blender modeling quality. Run paired before/after trials using same references and blinded reviewers with consent, logging actual tool calls, time, model size and corrections. Minimum 4 fixture classes:

1. Industrial product / chair: 3+ views and dimensions, upholstered seam, under-seat structure. Measured dimensions and number of missing parts. Export to GLB then reimport.
2. Hard surface prop: silhouette, small engraved marks, bevel radii, 3/4 reference with scale.
3. Stylized character: anatomical proportions, symmetry exceptions, 5 views; optional rig deformation.
4. Geometric relief: actual mesh sculpted groove/quilting confirmed in neutral/wireframe and export, not normal texture.

For every trial evaluate: silhouette shape agreement, dimensional deviation (if calibrated), per-part completeness, required geometric relief evidence, material fidelity, topology and export fitness, performance, iteration count, artifact integrity. Have 2+ independent evaluators for subjective categories; capture disagreements. Use `FATAL` blockers regardless of weighted aesthetic score. Failure gates must be actionable and traceable by part ID. Log `NOT_TESTED` for no Blender, no reference, missing view, missing real engine, or missing visual review. Avoid declaring 95% reference fidelity unless quantitative reference alignment and ground truth support it.


## V1.3 harness

Use `scripts/benchmark_runner.py` (or `scripts/forge_upgrade.py benchmark`) with actual Blender operation logs, file hashes, dimensions and at least two independent reviewers for subjective reference likeness. Four cases remain unexecuted until locally produced and inspected; see `references/benchmarks-v13.md`.

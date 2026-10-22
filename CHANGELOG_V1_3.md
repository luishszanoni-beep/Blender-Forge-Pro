# Blender Forge Pro 1.3.0 — Modeling Execution & Fidelity Upgrade

Integrates proposed V1.1/V1.2/V1.3 capabilities in a single, backward-compatible release.

## Features added
1. **Procedural Modeling Engine:** audited, fixed `bpy` operators for boxes, cylinders, ellipsoid primitives, tube mesh, loft, quilt panel and Boolean grooves.
2. **Reference Alignment:** calibrated-landmark 2D similarity with uncertainty and residual reporting; does not infer 3D camera pose.
3. **Intelligent Geometry Repair:** changes to declared part IDs only, scene snapshot preconditions, locked component guard, unchanged-part fingerprints and separate candidates.
4. **Advanced Surface Geometry:** real vertex-deformed quilting, modeled seam meshes and carved grooves, with G3 mesh proof required after creation/export.
5. **Mechanical & Assembly Intelligence:** proximity, center alignment and conservative clearance proxies from real scene bounds; no false engineering certification.
6. **Adaptive Detail & LOD:** budget-aware geometry allocation and bounded derivative LOD collections with approved relief automatically protected.
7. **360° Visual Regression:** controlled view-to-view pixel comparison with protected masks, fail-closed missing camera/view.
8. **Parametric Variants:** explicit structural/material choices, conditional compatibility rules and single-combination `.blend` output.
9. **Real-World Benchmark Harness:** four scenario contracts, evidence SHA verification, artist reviewer states and baseline-vs-candidate deltas.

## Compatibility and safety
- Eight existing skills preserved; `project.json` and G0–G8 evidence contracts remain at schema 1.0; new optional operational specs use schema 1.3.
- Blender subprocess bridge only runs bundled trusted worker tasks and explicitly provided finite/bounded JSON. No arbitrary Python scripts from reference material.
- `bpy` worker operations must be tested in real Blender. The authoring environment for this release did not have Blender; Python preflight/unit tests do NOT prove bpy runtime or artistic reference fidelity.
- Existing `.blend` input is never overwritten; outputs are new artifacts with `PENDING_VISUAL_QA` statuses.
- Benchmark cases remain **NOT EXECUTED** until a real Blender operator and independent reviewers complete the test plan.

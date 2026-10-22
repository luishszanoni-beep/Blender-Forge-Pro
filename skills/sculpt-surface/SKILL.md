---
name: sculpt-surface
description: "Create physical mesh relief in Blender including quilted vertex deformation, mesh seams, carved grooves, sculpted folds and armor details; prove geometric texture survives GLB export. Use when the request requires real modeled texture rather than image maps."
---

# Sculpt & Surface Specialist

## Ownership and trigger
G3: physical detail on actual evaluated mesh. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Approved G2 geometry, geometric feature ledger, detail scale, target triangle budgets.

## Required outputs
High-detail mesh/sculpt checkpoint, `qa/geo_proofs/` neutral/wireframe images, per-feature evidence.

## Production procedure

1. Identify feature scale: structural detail, medium relief, micrograin. Mark required actual geometry separately from material-only detail. Never equate bump/normal/PNG with edited mesh.
2. Choose technique per feature: Boolean/edge loops for grooves; extruded meshes/curves-to-mesh for seams/stitches; sculpt + multires/voxel remesh for wrinkles; applied displacement on sufficiently subdivided geometry; Geometry Nodes evaluated/applied for reusable relief.
3. Model from medium to small scales while preserving G2 silhouette, approved part dimensions and contact points. Avoid uniform noise or procedural "AI grain" instead of recognizable physical features.
4. Retain editable master and avoid baking unnecessarily early. Where export target cannot preserve a procedural stack, make a real evaluated mesh derivative and confirm its geometry after export.
5. Record what was changed: affected object, feature ID, method, measured relief mm if measurable, geometric evidence filenames. Prefer an explicit cross-section or depth/vertex change, not a high-poly count alone.
6. Inspect with neutral clay material and wireframe closeups at realistic viewing distances. Switch off normal/bump nodes to check genuine form; if it vanishes, treat as appearance-only.
7. Collaborate with Topology Engineer for game-ready derivative: preserve geometry where user explicitly requires it, bake microdetail only if permitted.
8. Pass G3 only after Fidelity Auditor verifies actual mesh and matches the reference. Do not mark `evaluated_mesh_verified` based on operator success without inspection.


### V1.3 — Real Surface Geometry
- Read `../../references/surface-geometry-v13.md` for `quilt_panel` actual vertex displacement, `tube` mesh seams and Boolean groove primitives. Preserve `forge_feature_ids` and evaluate mesh under neutral material.
- The detail/LOD planning contract `../../references/detail-lod-v13.md` must protect geometric requirements, never replace them silently by normal/bump textures. A successful operator is not G3 approval: demand wireframe/cross-section closeups and export persistence.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
"Modeled texture" represented only by roughness PNG; boolean artifact creates nonmanifold tears; excessive micro-poly mesh with no on-screen value; baked relief invisible in actual exported target.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

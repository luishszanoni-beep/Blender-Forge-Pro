---
name: topology-engineer
description: "Optimize Blender meshes and UV topology for games/web/Roblox, allocate geometry detail budgets and produce LOD variants while protecting physical relief and respecting triangle budgets."
---

# Topology Engineer

## Ownership and trigger
G5: topology/runtime/performance and profile derivative management. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Approved high-poly source, target platform, required features, known resource budgets.

## Required outputs
Optimized variants, scene/mesh statistics, UV/normal/LOD report, preserved feature evidence.

## Production procedure

1. Agree target profile and budget; never assume universal ideal triangle count. Use projected viewing distance, material count, user hardware, renderer and scene complexity.
2. Inspect evaluated meshes for triangles, degenerate faces, non-manifold edges, loose verts, flipped normals, intersections and duplicate geometry. Note: open surfaces are not automatically invalid; interpret topology relative to asset requirements.
3. Keep highpoly master unchanged; derive a lowpoly variant using targeted retopology, decimation or remesh only where details survive. Preserve silhouette-critical loops and required geometric relief.
4. Verify UV unwrap non-overlap where baked maps demand it, normal transfer, smoothing boundaries, sharp bevels and material splits. Avoid UV overlaps unless intentionally mirrored/atlas-shared.
5. Optimize modifiers and node stacks for export; evaluate final triangle count after modifiers (not base object count). Use object merges and texture atlases only if editing/rigging/material requirements permit.
6. If LODs matter, test screen-space silhouette and texture fidelity at intended distances. Validate approximate LOD transitions.
7. Check pivot/transforms/scaling, mesh names, collider strategy and optional rig deformation for target engine.
8. Compare optimized model against highpoly from multiple angles; log exactly which details are baked vs still geometric, with user requirement taking precedence.


### V1.3 — Adaptive Detail and LOD
- Read `../../references/detail-lod-v13.md` and use `scripts/detail_budget.py` to allocate triangles by measured screen presence, destination and mandatory representation. Required geometry that exceeds the budget must block rather than automatically bake away.
- Validate and run `create-lods` through trusted Blender bridge. LOD objects are separate hidden collections; verify each derivative visually and after export before deployment.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
Aggressive decimation destroys sculpt/character anatomy; normal maps replace forbidden geometry; open mesh described as broken without context; counting raw polygon faces instead of evaluated triangles.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

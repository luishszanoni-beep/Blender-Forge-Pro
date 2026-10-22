---
name: export-engineer
description: "Export and validate actual BLEND/GLB/FBX assets and variants, preserving source geometry, correct materials, chosen LOD collections, integrity hashes, scene hierarchy and target reimport."
---

# Export Engineer

## Ownership and trigger
G8 artifact production, structural verification and controlled handoff. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Audited `.blend`, requested formats, origin/units/material profile, destination constraints.

## Required outputs
Actual `deliverables/` plus `manifest.json`, reimport report and preview evidence.

## Production procedure

1. Confirm source `.blend` was saved to new destination with edits and dependency images packed or included. Do not overwrite user originals. Verify artifact bytes exist, meaningful size and expected Blender signature.
2. Normalize transforms, scene units in meters, scale, rotation/origin and object hierarchy for target. Verify export collection visibility and active selections.
3. For `.glb`, check `bpy.ops.export_scene.gltf` availability, use binary GLB with compatible glTF PBR materials and evaluated meshes. For FBX, inspect armature axes, unit mapping, bone leaves and engine-specific requirements.
4. Enumerate feature restrictions: true mesh detail vs shader displacement; bake geometry when required and verify result after export. Ensure image resources present and physically consistent.
5. Run `scripts/check_glb.py`; review structural parsing, metadata, mesh/material counts and binary chunk integrity. Structural PASS alone does not verify shading, geometry orientation or target app behavior.
6. Re-import export into a fresh empty Blender scene or supported target viewer and check object count, world bounds, pivots, materials, alpha, visibility, rig/poses if any. Capture representative screenshots and discrepancies.
7. Produce `qa/evidence.json` with actual audits and results, run `forge.py check-evidence`; create `manifest.json` hashes of real files only. Fail closed for missing required outputs.
8. Package only requested deliverables, source/preview/evidence as agreed, with safe relative paths and no absolute references; run a ZIP integrity check, mention external target restrictions honestly.


### V1.3 — Parametric Variants & LOD Delivery
- Read `../../references/variants-v13.md`; build one valid selected variant with existing components/materials and inspect it before separate GLB export. The number of combinations is not a promise to build them all.
- Read `../../references/detail-lod-v13.md`; candidate LOD collections are hidden until explicitly selected. Verify the intended derivative in Blender and target renderer; GLB alone does not implement runtime automatic LOD selection.
- Do not mark G8 complete because a recipe validates or a candidate .blend exists. Maintain actual export, roundtrip and geometry proof requirements.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
GLB with missing procedural shader textures; `.blend` only when GLB requested; broken scale/pivots; untested export called ready for Roblox; zip contains placeholders.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

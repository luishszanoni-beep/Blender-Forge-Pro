---
name: rigging-specialist
description: "Prepare and audit Blender armatures, pivots, weights and deforming components for game-ready models, preserving protected geometry and posing only when an actual rig is required."
---

# Rigging Specialist

## Ownership and trigger
G6 optional: deformation, skeleton/constraints and test poses. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Approved geometries, rig request and destination engine, approved rest pose/pivots.

## Required outputs
Rigged editable `.blend`, skeleton hierarchy, pose-test images, deformation/weight audit.

## Production procedure

1. Confirm rig actually needed; static product visuals do not need a skeletal rig. Distinguish mechanical hinges, object parenting, shape keys and deforming armatures.
2. Define target skeleton standard and export limitations early: engine requirements, bone names/orientation, rest pose, limits, skin influence budget, root motion.
3. For mechanical assets, place pivot at actual joints; constraint rotation axes and ranges. Do not deform rigid plates where transform/parenting is intended.
4. For characters, build hierarchy and skinning with even deformation at elbows/knees/shoulders, corrected weights near twist areas, optional corrective shape keys when supported by target.
5. Maintain `forge_part_id` and locked reference geometry; rigging must not permanently alter base dimensions. Handle mirrored limbs and asymmetric references intentionally.
6. Render or capture a systematic pose grid: neutral, minimum, maximum, cross-body and stress-test poses; check clipping, unintended distortion, inverted normals and topology tearing.
7. Confirm actual exported rig in the target format, hierarchy, bone orientation and animation clips if provided. A rig that only poses in Blender may not work in Roblox/GLB.
8. Auditor independently reviews all material deform issues. If no rig requested, mark G6 `SKIPPED_NOT_APPLICABLE`, not PASS.


### V1.3 — Rig-Compatible Updates
- When repairs or LODs affect articulated meshes, inspect original rest pose and deformation after changes; see `../../references/geometry-repair-v13.md` and `../../references/detail-lod-v13.md`.
- New fixed geometric operators do not retarget bones or certify weight painting; G6 pivot/pose QA remains mandatory, as does any relevant `../../references/assembly-v13.md` relationship test.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
Default rig applied to static furniture; armature skinning on rigid parts; missing joint pivot; deformations only tested in neutral pose; pose works only in Blender and breaks export.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

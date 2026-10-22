---
name: material-specialist
description: "Build realistic Blender PBR materials and finish, roughness, metalness and approved covering variants, verifying shader response and GLB compatibility without hiding wrong geometry."
---

# Material Specialist

## Ownership and trigger
G4: visual material response; cannot fix or certify geometry. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Approved geometry and material references with style, lighting and export destination.

## Required outputs
Material ledger, named shader slots, neutral/studio light comparisons, exported material plan.

## Production procedure

1. For each part specify real material family and observable properties (base color, roughness, metallic, specular, clearcoat, transmission, translucency, opacity, anisotropy) with confidence and approximate scale.
2. Keep physically plausible roughness/reflections; use varied but restrained procedural imperfections. Avoid fake glossy plastic on matte wood, overbright metals, or a uniform texture on all different material families.
3. Separate color texture, normal/bump and actual geometry. If a detail was specified as geometry, do not replace it with a shader node, including displacement that only affects Cycles render but not exported mesh.
4. Check UV scale, texture orientation/seams, tiling and directional grain. Use consistent texel density where applicable; test under neutral light and intended stage lighting.
5. For `.glb`, restrict production material to glTF-compatible PBR or bake unsupported nodes; verify output in reimport. Maintain editable source material in `.blend` if target shader is richer.
6. Check repeatability across product configurations: standardized finish IDs and naming for swappable furniture materials. Preserve cross-product palette constraints.
7. Produce diffuse/roughness/normal/emissive export inventory with actual paths/hashes where applicable; no missing linked images.
8. Have Auditor review material match separately from geometry match. An attractive render with wrong dimensions is still a reject.


### V1.3 — Material Variants
- Read `../../references/variants-v13.md` for material overrides in compatible product families. Choices must reference real material and part IDs; validate the selected combination before applying to a copy of the scene.
- Material/roughness work never substitutes required modeled relief. Verify appearance under neutral/studio light and actual target export.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
Color-correct screenshot claimed as physically correct material; shader effect absent in GLB; tiled texture scale wildly inconsistent; global roughness producing artificial gloss.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

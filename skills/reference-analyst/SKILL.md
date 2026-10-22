---
name: reference-analyst
description: "Analyze multi-angle references and orthographic landmarks for Blender modeling, dimension calibration, silhouette and confidence-aware reference fidelity. When explicitly requested, plan generation and visual QA of anatomically coherent reference image sets for Codex 3D modeling."
---

# Reference Analyst

## Ownership and trigger
G0-G1: source analysis and constraint ledger, never mesh authoring. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Photos/drawings, manual specifications, style references, known physical measurements, target destination. Before analyzing, inspect accessible assets and complete the adaptive source-file request at G0-F per `../../references/gcb-file-intake-v16.md`; never ask the user to resend an already accessible file.

## Required outputs
`planning/reference_ledger.json`, part inventory, visibility matrix, measurement and camera assumptions, blockout constraints.

## Production procedure

1. Inventory every actual source file with stable ID, provenance/license if available, view angle, and quality. Distinguish product documentation from concept art and 3D renders; note likely lens distortion.
2. Classify each view as orthographic/perspective/unknown. Do not call a frontal photograph orthographic automatically. Identify scale from dimensions or a known reference object; pixel ratios from perspective images are not calibrated world measurements.
3. List all visible components and subfeatures: silhouette-forming structure first, functional interfaces and construction seams second, microdetail last. Cross-reference every required part with source IDs.
4. Record `observed`, `inferred`, `unknown` for each part surface. Contradictory images require explicit conflicts list and resolution rule; newer or more authoritative source does not automatically trump user instruction.
5. Build front/side/top dimension hypothesis only if geometry can be inferred; record tolerances (specified vs estimated). Do not infer millimeters from a single non-calibrated photo.
6. Create a feature-ledger per component: geometry/material/either, priority, reference IDs, expected appearance, expected 3D construction, source uncertainty.
7. Estimate which extra orthos/closeups would most reduce modeling uncertainty, but proceed with labeled assumptions when not critical to the task.
8. Handoff *measurable constraints* to Geometry Architect. Lock only approved dimensions/parts, not speculative topology. Ask Fidelity Auditor to review mismatched sources.


### V1.3 — Reference Alignment System
- Read `../../references/reference-alignment-v13.md` when corresponding landmarks and reliable orthographic evidence exist. Validate 2D alignment with `scripts/forge_upgrade.py align-reference` and log RMS, max residual and verification provenance.
- Return `INDETERMINATE` on perspective/unknown cameras or inconsistent landmarks; never claim recovered 3D camera orientation without evidence. Pass G1 measured constraints and uncertain surfaces to Geometry Architect.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
Invented unseen surfaces as "confirmed"; geometry dimensions from uncalibrated reference; missing large structural piece; duplicate naming with conflicting IDs.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

### V1.5 — GCB reference intake at G1 (do not author meshes)
- Before G1.5 Geometry Architect planning, read `../../references/construction-blueprint-v15.md`; deliver `planning/reference_ledger.json` with stable source IDs, all visible/occluded pieces, projection/calibration per image, measured vs inferred dimensions, unknown opposite views and per-component geometric feature requirements.
- **Observed** requires a supporting source; **inferred** explicitly records approximations; **unknown** never becomes confirmed due to plausible generated plates. An orthographic image without a scale does not establish real-world mm. Avoid uncalibrated pixel-to-mm calculations.
- Ask the Architect to preserve separate moving pieces and symmetry requirements. Pass projected image landmarks only where camera/view is credible; send uncertain surfaces to auditor for signoff rather than inventing exact unseen topology.
- The single GCB spec created downstream drives ALL technical plates. New art imagery must not be used as sole dimensional authority, and generated exploded offsets are not assembly coordinates.

### V1.6 — G0-F adaptive file request (mandatory for new GCB workflows)
- Inspect actual conversation attachments and project sources **before** asking for uploads. Record what has already been received. Classify each file as `art_reference`, `orthographic_reference`, `detail_reference`, `technical_document`, `source_mesh`, `rig_reference`, `material_map` or `animation_reference` as appropriate. Do not invent access to Codex local files.
- Request all **missing essential** files in one natural PT-BR message, then recommend useful optional views/closeups/material maps only when relevant. Absolute physical scale, editing an existing model, and retargeting have conditional mandatory sources; multi-angle images themselves are not always mandatory. Ask non-file requirements (target, clips, tolerances) in text.
- Save G0-F intake information and an explicit user `nao tenho` for unavailable optional files; avoid repeat requests. When a local filesystem is authorized, use `scripts/gcb_intake.py` to generate `intake_report.json` and `file_request.md`. Block G1.5 if an essential is missing, but continue with documented inferred surfaces when recommended photos are unavailable.
- Read `../../references/gcb-file-intake-v16.md`. The CLI's `READY_FOR_REFERENCE_ANALYSIS` means only file presence, **not** visual approval or a valid dimension calibration.


### V1.7 — Conditional generation of production-ready image references (G1-R)
- Trigger **only if the user requests new images** to build the asset. Review `../../references/reference-image-generation-v17.md`; preserve any supplied art immutable. If no image-generation capability is actually available, record `NOT_GENERATED` and make a plan, never fabricated files.
- Decompose the subject anatomically/structurally before image generation: maintain unique semantic part IDs, logical number of limbs/horns/eyes/wing struts/jaws, center of mass/support points, joint positions, separation of moving segments, silhouette-critical plates and designed asymmetry. Apply topology/rig logic to fantasy or Bloxy assets without forcing lifelike realism.
- Generate only views needed to resolve geometry (known side/front/top/back, 3/4, articulation closeups). User original view is authoritative; additional generations show `inferred` or `generated_design` provenance until reviewed. Ensure corresponding silhouettes and distinctive marks remain stable across angles; do not call a perspective generation true orthographic camera calibration.
- **Inspect image pixels** for duplicated/absent parts, legs or wings attached implausibly, intersecting/floating joints, fused mandibles, unsupported volume, impossible folding/rotation, confusing shading disguising shape, decorative noise concealing geometry and inconsistent views. Reject critical defects and regenerate or revise only affected part sets. This requires actual visual inspection, not prompt compliance.
- Deliver each generated image ID/path/view/confidence plus component observations, constraints, unresolved unknowns and construction handoff to Geometry Architect. Independent Fidelity Auditor must review before G1-R is considered passed. Structural QA metadata alone cannot certify visible anatomy.

### V1.9 — 3DERL visual exemplars for source analysis
- When the user requests quality inspirations, the reference is ambiguous or creature/vegetation anatomy is complex, optionally use `../../references/3d-excellence-library-v19.md` and the CC0 catalog. Select at most 3 task-relevant examples; prefer same style and purpose. User source imagery remains G1 PRIMARY. A library thumbnail is never a new observed view of the USER asset; never transfer its hidden geometry or exact sizes into `reference_ledger.json`.
- State which principles are transferable (silhouette, modular construction, plausible volumes, joints, surface finish) and which facts need an actual model file (rig/mesh/UV). Do not ask for optional library images during G0-F intake. Maintain G1-R anatomy/image QA and explicitly mark confidence observed/inferred/unknown.

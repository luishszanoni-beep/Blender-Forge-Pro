---
name: fidelity-auditor
description: "Independently audit Blender models and generated 3D-modeling reference images for multi-view fidelity, anatomy, geometry, structural and articulation plausibility, regression, and export proof."
---

# Fidelity Auditor

## Ownership and trigger
G1-G8 independent quality assessment, acceptance/critical defect register. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
Reference ledger, actual Blender scene or renders, geometry proof, stats, export files, checkpoint baseline.

## Required outputs
`qa/evidence.json`, `qa/fidelity_review.md`, blocker list with severity, part ID and targeted repairs.

## Production procedure

1. Confirm actual visual/geometry evidence available. If only a model filename or textual description exists, flag `PENDING_VISUAL_QA`, not APPROVED.
2. Build a coverage matrix by part, required view and feature; distinguish direct calibrated comparison from subjective style judgment. Do not infer invisible surfaces as visually verified.
3. Align source and rendered projection/crop/scale before attempting image metrics. Compute optional foreground IoU/centroid only for calibrated comparable masks; never call it a semantic fidelity score.
4. Inspect neutral/clay renders first for silhouette, component presence, proportions and assembly. Inspect shaded renders second for finish, material response and aesthetic style.
5. For every required geometric feature, demand evaluated mesh evidence and wireframe/closeup plus actual export persistence. High detail normal maps do NOT count; an overall poly count does NOT prove a groove exists.
6. Review topology stats, nonmanifold only where relevant, UV/export warnings, triangle/material budgets and rig deformation when applicable.
7. Score according to shared 100-point rubric but allow `null` unobservable checks. Any missing mandatory part, broken export or unverified real-geometry feature is a *blocking defect* independent of aggregate score.
8. Write exact correction instructions with affected part/face/feature, reference source, desired result and explicitly protected baseline. Do not edit the model while certifying the model.
9. Re-inspect changed areas plus dependencies after specialist corrections. Only mark `APPROVED` if all required evidence is actually inspected and no blockers remain.


### V1.3 — Independent Reference & Regression QA
- Use `../../references/reference-alignment-v13.md` only when reliable orthographic evidence makes 2D metrics meaningful; do not confuse inferred landmarks with 3D likeness.
- Use `../../references/regression-v13.md` for same-camera protected before/after views and baseline geometry checks. A regression pass checks change preservation; it does NOT prove resemblance to the original reference.
- See `../../references/benchmarks-v13.md` for actual Blender trials. Never approve a model on the basis of structural/unit tests without inspecting renders and critical details.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
Fictional "100% match" from one image; all green from successful Python tests without looking at output; wrong-camera silhouette metric; artistic score masking a missing structural component.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

### V1.5 — Independent G1.5 Construction Blueprint audit
- Before approving any G2 reference-based reconstruction, read `../../references/construction-blueprint-v15.md`, inspect original reference ledger, `gcb_spec.json`, produced SVG/PNG plates, `gcb_preflight.json` and, when actual Blender is available, `gcb_blender_evidence.json` and orthographic/3-4 blockout renders.
- Numeric validator only verifies specification structure: do NOT equate `SPEC_VALIDATED_PENDING_VISUAL_QA` with faithful silhouette, correct unseen surfaces or G1.5 approved. Treat no-Blender as planning only; record `PENDING_VISUAL_QA` until trustworthy image/scene comparison is performed.
- Detect component omissions, duplicate head/jaw/limb meshes, incorrect parent relationships, anchor misfits, wrong scale, primitive substitutions destroying style, wrong projections, undocumented inferred geometry and generated plates inconsistent with numeric JSON. Judge art-to-blueprint likeness independently of blueprint internal correctness.
- Reject critical defects, return stable affected part IDs, protected component IDs and targeted corrections; rerun the spec validation and deterministic sheets after edits. G1.5 acceptance cannot bypass G2, G3 or G7 evidence, nor real export/reimport tests in G8.

### V1.6 — File intake evidence audit
- At G1/G1.5 check the coordinator's file intake report (or conversational inventory if no local filesystem), verify that every `observed` feature is actually supported by accessible original art, and reject claims based on files merely mentioned. Do not treat a source filename or file existence as proof of camera calibration.
- If the user explicitly lacks a recommended view, allow GCB with `inferred`/`unknown` surfaces instead of blocking for missing optional assets; retain critical missing essential-file blockers and the independent visual gate.


### V1.7 — Independent generated-image anatomical audit (G1-R)
- On user-requested reference-image generation, inspect **each actual generated image** against original art (if supplied), agreed style, all other generated views and the G1 reference ledger. Read `../../references/reference-image-generation-v17.md`. Do not approve by reading prompts, metadata, AI rationale or running structure validators alone.
- Check impossible unintended topology and anatomy: limb/horn count and side symmetry/asymmetry, body weight/support contacts, head-neck-spine-jaw coherence, wings/shoulder anchoring and fold clearance, tails/roots, physical part separation, overlapping/duplicated pieces, full 3D volume/perspective continuity, materials not masking bad geometry, and animation pivot feasibility. Fantasy logic may differ from biology but must remain consistently articulable and modelable.
- Record status per check (`PASS`, `FAIL`, `UNKNOWN`, `NA`) with stable affected part IDs and image paths, not just an aggregate score. Rejected critical defects block source-image handoff; request targeted revisions, preserve locked approved features and re-inspect changed and adjacent parts. Reviewer's recorded decision is independent of the generator. An unavailable or uninspected image must remain `PENDING_VISUAL_QA`.
- Generated alternate angles stay explicitly inferred; numeric spec/technical SVG remain deterministic and independently gated. Output QA details and a Codex-readable corrective note list. Never infer measured physical mm, claim engineering safety, or promise perfect art fidelity.


### V1.8 — Audit Atlas recommendations vs actual scene
- When GCB includes `blender_tool_plan.json`, verify documented tool IDs/page, justification, target compatibility and whether the agent actually checked Blender version/`bpy` operation behavior. Refer to `../../references/blender-atlas-routing-v18.md`. A valid recommendation is NOT proof it was executed, nor evidence that the mesh/surface/rig/export are correct.
- Reject technique choices that contradict the user-approved appearance, destroy protected geometry, fuse moving parts, increase cost without benefit or rely on unsupported modifiers/nodes after export. Preserve existing independent G1-R/G1.5/G2-G8 visual and target-runtime QA.

### V1.9 — Visual exemplar guardrails
- `3DERL` supplies optional relative quality criteria, not ground truth for the USER asset. Audit the actual source art, GCB spec, Blender renders and exported meshes independently; never pass/fail geometric fidelity solely because the result resembles a library thumbnail. Treat catalog images as IMAGE_ONLY, and pack format/animation claims as SOURCE_METADATA_ONLY unless actual Blender tests are performed.
- Reject unsupported statements like "topologia limpa", "rig validado", "perfeito para Roblox" from preview images. Check case-based synthetic anti-patterns in `../../references/3d-excellence-antipatterns-v19.json` (duplicated jaw J1, detached limbs, wrong pivots, fabricated hidden features, shaders masking missing geometric relief) when relevant. Preserve protected parts during repairs and log evidentiary limitations.

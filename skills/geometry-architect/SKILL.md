---
name: geometry-architect
description: "Construct Blender meshes via audited procedural geometry operators, precise blockouts and snapshot-guarded repairs. Plan source-backed GCB numeric blueprints and step-by-step model assembly from reviewed reference images."
---

# Geometry Architect

## Ownership and trigger
G2: shape, scale, part topology and spatial construction. Invoke when the task matches the description; load no other specialists unless a dependency or handoff genuinely requires them. The **AGENTS.md** coordinator owns sequencing and a single project manifest; do not assume this skill implies separate independent model execution.

## Inputs
G1 reference ledger, dimensional constraints, target mode, existing `.blend`/authorized scene.

## Required outputs
`work/checkpoints/g2_blockout.blend`, stable object/part hierarchy, neutral multi-view renders and measurements.

## Production procedure

1. Validate Blender route exists, master file is backed up, and `project.json` declares meters as scene units. Blender numeric object dimensions should match mm input after /1000 conversion.
2. Plan assembly hierarchy: primary shells/frames, supports, fasteners, secondary details, sculpt zones, material assignments. Each important part gets semantic `forge_part_id`; avoid accidental `.001` identity drift.
3. Blockout with intentionally simple forms; constrain outer width/height/depth and functional clearances before details. Use orthographic/clay views from reference-aligned cameras.
4. Prefer non-destructive Boolean/bevel/subdivision curves until visual silhouette passes. Ensure bevel width fits geometry thickness; avoid shading artifacts from inconsistent smooth normals, modifiers and inverted faces.
5. For hard surface, make real wall thickness, edge chamfers, fillets and functional contacts where visible. Avoid floating fasteners/interpenetrations not present in reference.
6. For organic/stylized work, use a proportion-driven sculpt base with anatomical structure or style rules, not only stretched primitives.
7. Emit a dimensional inspection, part naming list and view captures. Compare silhouettes against calibrated references, flag occluded zones. Do not hide errors with high-contrast materials.
8. Submit G2 to independent Fidelity Auditor; if rejected, revise blockout before materials/sculpt. Freeze approved primary proportions through the Geometry Fidelity Lock.


### V1.3 — Procedural Modeling, Localized Repair and Assembly
- Read `../../references/modeling-ops-v13.md`: compile bounded recipe version 1.3 and prevalidate before `blender_bridge.py run --task build-recipe`; an accepted JSON does not prove geometry was actually modeled.
- Read `../../references/geometry-repair-v13.md` when fixing parts: capture real scene inspect hash, declare affected IDs and protected IDs, run only fixed Blender `apply-repair` operators on a NEW candidate and send to independent QA.
- Read `../../references/assembly-v13.md` for measured proximity/clearance/center relations; box proxies are not manufacturing or collision certifications.


### V1.4 — Adaptive Intelligence Router (AIR)
- On every routed task, use the shared `../../references/air-orchestration-v14.md` **Adaptive Intelligence Router** contract: select **model class and reasoning effort per task**, not once for this whole skill. The coordinator owns capability/QA/budget negotiation; this specialist retains its original G0–G8 responsibilities and never selects an unauthorized runtime model.
- Treat `scripts/air.py` output as an **unexecuted task plan**. Accept task assignments only when the host actually supports the chosen model, effort, tools, and authorized subagent execution; otherwise stay with the current agent and record advisory mode. Do not report simulated `fixture.*` as real models.
- For changes to a `.blend`, require exclusive AIR-managed scene lease where supported, valid checkpoint and Geometry Fidelity Lock. Return actual evidence and status to the independent auditor; routing success is not model quality evidence.

## Rejection criteria
Beautiful shader disguising wrong scale; object duplication without purpose; wrong pivot orientation; shell floating off the assembly; overmodeling before silhouette review.

## Tool/runtime contract
- Inspect the actual Blender integration first: authorized Blender MCP, installed `blender` executable, or manual instructions. `bpy` in ordinary Python must never be assumed.
- Never invent visual QA, model files, geometry evidence, measured dimensions, export success or run logs.
- Read `../../references/workflow-gates.md`, `../../references/project-contract.md`, and the specialist checklist at `references/acceptance-checklist.md` when starting. For geometry refer to `../../references/geometric-detail-proof.md`; for QA refer to `../../references/fidelity-rubric.md`; for export consult `../../references/target-profiles.md`.
- Keep source reference files immutable, save stage-specific `.blend` checkpoints, and use stable semantic IDs for parts/features. A single-stage rejection yields targeted revision, not full regeneration without reason.
- Execute pure metadata tests via `python scripts/forge.py`; Blender artifact production requires actual Blender access. If missing, output a usable build plan with `NOT_EXECUTED` status.

## Handoff / acceptance checklist
See `references/acceptance-checklist.md`. Pass on unresolved risks, evidence filenames, uncertainty and affected part IDs to the next specialist. User-facing status in Brazilian Portuguese.

### V1.5 — Construction Blueprint System (new mandatory G1.5, between G1 and G2)
- For reference-derived multipart, articulated, stylized or complex geometry, read `../../references/construction-blueprint-v15.md` and author a **single source of truth** `planning/gcb/gcb_spec.json` before final G2 construction. Preserve all G1 observed/inferred/unknown and measured-vs-relative scale classifications; never invent millimeters from an uncalibrated concept image.
- Map every required part to a unique stable ID, primitive (`box`, `sphere`, `cylinder`, `cone`, `wedge`) or explicit `custom_mesh` vertex/face recipe, dimensions, world position, rotation, pivot, separate mesh, parent, attachment anchor/tolerance, and ordered assembly phase. Organic details beyond the primitive blockout remain G3 tasks; never falsely call them exact matches.
- Run `python scripts/gcb.py validate <spec.json>` and `python scripts/gcb.py prepare <spec.json> --out <project>/planning/gcb`; use `--require-png` only when CairoSVG is verified. The generated SVG/PNG front/side/top/3-4 plates, schematic exploded views and phased assembly come **from JSON**, not from independent image sampling. Images teach order/shape; Codex must use JSON for coordinates and sizes.
- With Blender available, run `blender --background --python scripts/gcb_blender.py -- --spec <project>/planning/gcb/gcb_spec.json --out <project>/work/gcb_blockout` to create only a **temporary** proof blockout. Check actual cameras/silhouette and submit to independent Fidelity Auditor. No Blender available -> `PLANNING_ONLY`, not G2 complete.
- Reject duplicate or missing parts (e.g. one `J1` mandibula both attached and fused); reject parent cycles, unexplained clearance, broken anchor tolerances and deviations from source art. Preserve prior G2 Geometry Fidelity Lock and fix specific IDs rather than rebuilding approved components.
- G1.5 approval requires external/independent art-to-model inspection; a green numeric script or plate render is not visual approval. AIR v1.4 must use deterministic scripts without wasteful subagents and serialize scene writes. Do NOT interpret G1.5 as replacement for G2–G8.

### V1.6 — G0-F precondition
- Before authoring a new GCB spec, verify the G0-F inventory (`references/gcb-file-intake-v16.md`); use only confirmed accessible source files and recorded textual data. In Codex local mode require `intake_report.json` to have `ready_for_g1=true` and pass it to GCB `prepare` using `--intake-report` when available. If a mandatory source is absent, request it via the coordinator rather than fabricating an image, mesh, dimension or rig.
- Missing optional frontal/top/back views permit documented geometric inference; every generated sheet remains subordinate to original source and the numeric GCB spec.


### V1.7 — Generated source image construction handoff
- When G1-R was invoked by an explicit user image-generation request, require its reviewed image manifest and per-part construction steps. Use `../../references/reference-image-generation-v17.md`: translate silhouette and anatomical attachment hypotheses into editable mesh primitives/profiles, operation order, separated moving parts, coordinate frames, pivot candidates and measurable **relative** dimensions. Label what is inferred/unknown. Do not turn an artistic perspective image into exact mm or validated physical constraints.
- The source-image guidance (`modeling_steps`/`parts`) supports the numeric `gcb_spec.json` but never overrides it. Ensure stable IDs for every major part and explain *how* Codex should model each part: primitive or custom mesh, extrusions/loops, attachment, expected geometry, what to verify in clay renders and joints to check. Preserve all required separations (e.g., independently rotating jaw/wings/tail), and never auto-merge them just to satisfy aesthetics.
- If a critical anatomical ambiguity remains, get targeted review or use a clearly labeled hypothesis with revision guidance; do not falsely certify source-image precision. Run GCB construction validation and independent audit after the G1-R gate. If an approved local QA report exists pass it as `--reference-qa-report` to GCB `prepare`.


### V1.8 — Atlas-backed modeling technique selection
- For G1.5/G2 construction, consult `../../references/blender-atlas-routing-v18.md` and run `python scripts/blender_tool_router.py search --query "<component plus modeling operation>" --stage G2 --target <roblox|web_glb|render|general> --limit 3` when local code execution exists. The produced `blender_tool_plan.json` in GCB is an advisory starting shortlist; inspect PDF entry/page and task constraints before selecting.
- Choose primitives, Extrude, Boolean, Bevel, Mirror, curves, Geometry Nodes or sculpt only if their actual advantages and exported behavior match the component. Prioritize low complexity, true mesh where required, protected IDs, joint separation and stable geometry; don't use new techniques because they are merely listed.
- Validate exact Blender version and API invocation in live `bpy` prior to modifications. An atlas operation name is not an executable `bpy.ops` signature, and an index match is not evidence of mesh quality. Keep G1.5 and G2 independent visual QA mandatory.

### V1.9 — 3DERL task-matched constructive precedents
- Before complex GCB/ G2 construction, optionally run `../../scripts/excellence_reference_router.py select` as described in `../../references/3d-excellence-library-v19.md`: select at most 3 CC0 examples matching style/domain/task. Analyze shape/construction lessons only; do not copy another model's proportions, materials, pivots or anatomy over the user-approved reference. Never treat an external render as a measurable blueprint or rig proof.
- Incorporate an `excellence/selected_references.json` + `.md` summary in Codex planning only when it helps. Pass GCB CLI `--excellence-references <path>` to attach as a NON-authoritative appendix. Combine with ATSE tool IDs for deciding HOW to construct, while `gcb_spec.json` sets actual coordinates. No mandatory network download or extra subagent. Do not let curated assets replace procedural geometry review or native Blender tests.

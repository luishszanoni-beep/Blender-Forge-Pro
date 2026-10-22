# Blender Forge Pro — Complete User Manual

**Public documentation for v1.9.0** · [Installation](INSTALLATION.md) · [Quick start](QUICK_START.md) · [Repository](https://github.com/luishszanoni-beep/Blender-Forge-Pro)

## 1. Purpose and boundaries

Blender Forge Pro coordinates **eight specialist skills** around a controlled, reference-driven 3D production process. It is useful for stylized characters and creatures, modular/Bloxy assets, furniture, mechanical objects, PBR materials, Blender-based previews, Roblox FBX models and web-oriented GLB deliveries.

The plugin distinguishes **planning**, **machine-verifiable geometry metadata**, **actual Blender execution**, and **independent artistic inspection**. A valid JSON specification or successful Python command does **not** guarantee a working, reference-faithful model. Blender and any target platform must actually be accessible and tested before making completion claims.

## 2. The eight specialist skills

| Skill | Main responsibility | Typical deliverables |
| --- | --- | --- |
| **Reference Analyst** | Intake, measurement confidence, view analysis, visibility/occlusion notes | Reference ledger, required-parts inventory, unresolved questions |
| **Geometry Architect** | GCB numeric plan, primitives, part positions, joins and G2 blockout | `gcb_spec.json`, construction plates, mesh construction steps |
| **Sculpt & Surface Specialist** | Physical surface relief, sculpt work and geometry-based seams/grooves | Geometry detail proof and before/after comparisons |
| **Material Specialist** | Materials, PBR response and export-safe shaders/textures | Material definitions, neutral-light comparisons |
| **Topology Engineer** | Mesh integrity, normals, UVs, poly/LOD optimization | Mesh/UV/triangle budget checks and topology evidence |
| **Rigging Specialist** | Articulation, bone pivots, deformation and animations when needed | Skeleton/skin and tested action clips |
| **Fidelity Auditor** | Independent multi-view evaluation; rejects missing, duplicated or incorrect parts | QA findings, gate decisions, visual evidence |
| **Export Engineer** | Save source and deliver requested formats; verify round-trip/import | `.blend`, FBX/GLB as applicable, verification and manifest |

A skill is a responsibility, **not necessarily a separate agent process**. Runtime delegation requires an actual supported adapter and access rights.

## 3. Recommended prompt structure

State these items whenever possible:

1. **Object and purpose:** e.g. 'rigged fantasy plant for Roblox Studio'.
2. **Visual style:** Bloxy/block-built, stylized, realistic, hard-surface, or mixed; show reference art.
3. **Destination:** `roblox`, `web_glb`, `render` or `general`.
4. **Dimensions:** exact supported measurements, relative proportions, or acknowledge uncertainty.
5. **Required geometry:** removable parts, jaw, horns, foliage, wings, surface relief, joints.
6. **Animation needs:** idle, attack, walk, constraints, retargeting or fixed mesh.
7. **Optimization constraints:** polygon budget, texture limits, draw calls, LOD where known.
8. **Deliverables:** editable `.blend`, FBX/GLB, preview views, QA report and hashes.
9. **Approval policy:** stop at GCB/G1.5 until source-based visual QA passes.

### Example: Roblox creature

> Build a **Bloxy—not generic low-poly** dragon for Roblox. Keep the jaw as a single separate object, never fused to the head or duplicated; preserve all four legs and physically meaningful joint placement. Start by auditing my references and producing a GCB spec, exploded diagram, pivot plan and staged instructions for Codex. Use real modeled detail where requested. Include a rig and looping Idle animation, then test FBX import in Roblox Studio if that environment is available. Report any unverified stage rather than claiming success.

### Example: furniture product render

> Reconstruct this chair from a manual and photos. Preserve observed dimensions and part count. Keep missing surfaces explicitly inferred. Model seams as actual geometry where required. Produce a high-quality editable Blender source and a lightweight GLB variant only after validating silhouette, materials, topology and exported files.

### Example: audit an existing Blender model

> Compare my existing `.blend` with these reference views. Do not overwrite the source. List critical proportion, part, joint and topology defects by stable part ID. Propose the smallest safe corrections and provide before/after evidence.

## 4. Quality gates: from input to delivery

| Gate | What is checked | Exit criterion |
| --- | --- | --- |
| **G0 / G0-F** | Files, rights, destination and execution availability | Required sources accessible; recommended inputs recorded |
| **G1** | Views, calibrated/relative scale, visible and hidden components | Reference ledger with observed/inferred/unknown tags |
| **G1-R** (conditional) | New images **only if user requests reference generation** | Anatomical and cross-view review explicitly approved |
| **G1.5 — GCB** | Part IDs, dimensions, pivots, attachment anchors, build steps | Valid spec **plus independent reference-to-plan audit** |
| **G2** | Geometric blockout and proportions | Neutral matched-view silhouette review |
| **G3** | Real mesh relief and component detail | Geometric proof, not only bump/normal maps |
| **G4** | Materials, lighting response and usable texture maps | Material QA in relevant lighting |
| **G5** | Topology, UVs, transforms, complexity and LOD | Export-safe topology and accepted resource budget |
| **G6** (if required) | Rig pivots, skin, poses and animation clips | Tested deformations/loops |
| **G7** | Independent visual fidelity check | No critical omissions, collisions or art mismatch |
| **G8** | Save/export/re-import | Requested files exist and pass appropriate destination checks |

**Allowed status labels** include `PENDING`, `BLOCKED`, `READY_FOR_VISUAL_QA`, `APPROVED` and `REJECTED`. **A numerical preflight success does not automatically advance a visual gate to APPROVED.** See [Workflow Gates](../references/workflow-gates.md).

## 5. File intake: G0-F

The agent should first inspect **already attached or accessible files**. It must ask once for missing essentials, distinguishing **required**, **recommended** and **answerable in text**. Extra camera views are recommended when useful but not universal prerequisites. An exact real-world scale cannot be asserted without trusted measurement references.

In a local project, prepare an intake manifest by adapting [this example](../examples/gcb/intake_example.json) to real file paths. Then run:

~~~bash
python scripts/gcb_intake.py planning/gcb/intake_manifest.json --root . --out planning/gcb/intake
~~~

Outputs:

- `planning/gcb/intake/intake_report.json` — verified local path inventory and readiness.
- `planning/gcb/intake/file_request.md` — missing essential/recommended file request (the generator's existing text is in Portuguese).

The output describes **file presence**, not a proof of visual resemblance or successful Blender execution. Missing mandatory source inputs block downstream work.

## 6. Generated reference images: G1-R

This flow is **conditional**: the plugin should generate modeling-reference images only when the user explicitly requests them and an actual image-generation capability exists.

The reference package should strive for:

- Front/side/back/top/three-quarter views where they are useful.
- Anatomically or mechanically plausible joints, supports and pivots.
- Consistent part count and proportions across all views.
- Clear separation of animated/movable pieces.
- Close-ups for ambiguous parts and an **assembly plan for Codex**.
- Explicit tags for **observed, inferred and unknown** details.

The quality checklist rejects duplicated jaws, fused moving parts, missing legs, floating pieces and contradictory orthographic views. The original user artwork remains authoritative.

For **already generated and visually inspected** images, adapt a QA manifest and run:

~~~bash
python scripts/gcb_image_qa.py validate planning/gcb/reference_images/image_reference_qa.json --root . --out planning/gcb/reference_images/image_reference_qa_report.json
python scripts/gcb_image_qa.py handoff planning/gcb/reference_images/image_reference_qa.json --root . --out planning/gcb/reference_images/codex_image_reference_handoff.md
~~~

Those commands validate **metadata, links and reviewer declarations**, not pixels or anatomy by themselves. Never fabricate `REVIEW_DECLARED_APPROVED` without inspecting the actual images.

## 7. GCB: Geometric Construction Blueprint (G1.5)

The Reference Analyst identifies parts. The Geometry Architect writes **one numeric source of truth**: `planning/gcb/gcb_spec.json`, based on [the schema](../references/construction-schema-v15.json).

Each required component should have:

- Stable ID and label.
- Primitive or explicitly specified custom mesh construction.
- Units, dimensions, translation and rotation.
- Attachment anchors and parenting relationship.
- Pivot location and intended deformation/animation behavior.
- Provenance and confidence for inferred measurements.
- A defined build order with validation checkpoints.

Validate the illustrative sample:

~~~bash
python scripts/gcb.py validate examples/gcb/demo_bloxy_plant.json
~~~

Generate its technical plates:

~~~bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out work/gcb-demo
~~~

Inspect the generated `work/gcb-demo/` folder:

| File or folder | Meaning |
| --- | --- |
| `gcb_spec.json` | Canonical geometry and build steps |
| `gcb_handoff.md` | Codex-facing construction guide |
| `gcb_preflight.json` | Structural preflight, warnings and **pending visual QA** |
| `sheets/*.svg` | Schematic overview, optional exploded plate and step plates |
| `blender_tool_plan.json` / `.md` | **Advisory** ATSE tool selection |

Optional CairoSVG can produce PNG variants of technical plates. To require them, use `--require-png` (the command fails clearly if unavailable):

~~~bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out work/gcb-demo-png --require-png
~~~

The demonstration's dimensions are **relative**. Its separate jaw `J1` and head are examples of correct component separation; it is not an exact copy of any user artwork.

### Feed in the real intake and approved image QA

~~~bash
python scripts/gcb.py prepare planning/gcb/gcb_spec.json --out planning/gcb --intake-report planning/gcb/intake/intake_report.json --reference-qa-report planning/gcb/reference_images/image_reference_qa_report.json
~~~

Pass `--reference-qa-report` **only** when the generated-image reference path exists and the independent visual review is complete. For tasks using original user images only, G1-R is not required.

## 8. Blender Atlas Tool Selection Engine (ATSE v1.8)

The bundled Atlas PDF catalogs **407 selected tool entries**, 16 chapters and 11 Blender workspaces for Blender 5.2.2 LTS. It is a secondary curated guide, **not the complete `bpy` API**. Every actual command must be checked against the installed Blender version and operator context.

~~~bash
python scripts/blender_tool_router.py verify-index
python scripts/blender_tool_router.py search --query "dragon wing membrane thickness" --stage G2 --target roblox --limit 5
python scripts/blender_tool_router.py search --query "idle tail rig" --stage G6 --target roblox --limit 5
~~~

This prints advisory tool names and reasons; it does not execute Blender. The GCB `prepare` command automatically adds step-specific advisory plans when the Atlas index and PDF are available.

Do **not** infer exact dimensions or choose topology solely from the Atlas description.

## 9. 3D Excellence Reference Library (3DERL v1.9)

This library selects at most **three** suitable quality examples from 15 catalog entries covering Kenney, Quaternius and Poly Haven. They inform **construction quality**, not the identity of your asset. Preview images are remote links and cannot certify rigging, geometry, UV quality or export compatibility.

~~~bash
python scripts/excellence_reference_router.py validate
python scripts/excellence_reference_router.py select --goal "bloxy dragon with rig and wings" --style bloxy --focus anatomy --focus rig --stage G1.5 --target roblox --out work/excellence
~~~

Expected outputs:

- `work/excellence/selected_references.json` — exact curated selection.
- `work/excellence/selected_references.md` — learning notes and limitations.
- `work/excellence/reference_gallery.html` — linked remote previews.

Use the optional selection as GCB context:

~~~bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out work/gcb-with-examples --excellence-references work/excellence/selected_references.json
~~~

**No download is required for ordinary selection.** Image caching is opt-in and requires an explicit `--allow-network` flag:

~~~bash
python scripts/excellence_reference_router.py cache --plan work/excellence/selected_references.json --out work/excellence/cache --allow-network
~~~

Downloaded assets are bounded by host, MIME type and size controls. This does not automatically authorize reuse of an external model outside its terms.

## 10. Adaptive Intelligence Router (AIR v1.4)

AIR categorizes tasks into five capability classes and four effort levels. It produces **advisory model/effort plans** unless an authorized host adapter actually supports delegation.

~~~bash
python scripts/air.py doctor
python scripts/air.py validate-registry examples/air/registry_simulation.json
python scripts/air.py validate-tasks examples/air/task_plan_chair.json
python scripts/air.py route examples/air/task_plan_chair.json --registry examples/air/registry_simulation.json
~~~

`registry_simulation.json` contains **synthetic fixtures**, not real available models or prices. A production registry must be populated with verified capability/cost details before its recommendations are actionable. Do not claim real subagents were spawned or model settings changed from `air.py route` alone.

## 11. Actually modeling in Blender

Start by verifying the Blender executable:

~~~bash
python scripts/blender_bridge.py doctor
~~~

For a safe **temporary GCB blockout** when Blender is reachable:

~~~bash
blender --background --python scripts/gcb_blender.py -- --spec work/gcb-demo/gcb_spec.json --out work/gcb-blockout
~~~

The blockout is an intermediate geometry proof. Continue with correct mesh operations, material preparation, topology, rigging and a real fidelity audit. Existing `.blend` files should not be overwritten; use project-local output folders and checkpoints.

**Important:** a ChatGPT web conversation without a Blender-enabled execution tool cannot edit your local file just because you installed the plugin.

## 12. Materials, topology and animation

- **Materials (G4):** use physically coherent values and lighting comparisons; bake textures only when the export target cannot reproduce procedural nodes.
- **Topology (G5):** validate normals, duplicate/loose geometry, UV distortion, triangle budgets and LODs. Do not smooth away a required stylized/block-built silhouette.
- **Rigging (G6):** pivot positions must match the GCB; moving pieces remain separate if specified, and deformation must be tested using poses.
- **Idle clips:** produce actual named animation Actions where required, verify frame-loop continuity and re-import the animation into the destination engine if accessible.
- **Roblox:** prefer a purpose-built FBX pipeline for skinning/animations when appropriate; inspect scale, bone names, pivot orientation, material conversion and animation loop in **Roblox Studio**, not just Blender.
- **GLB:** preserve export-safe PBR materials and check the resulting file in an independent viewer.

## 13. Fidelity audit and delivery

Before acceptance, require actual evidence of:

1. **All required parts present exactly once**, with clear transforms and attachments.
2. **Reference-aligned silhouette** and plausible proportions from supported views.
3. **Actual geometric details** wherever requested (not merely textures).
4. **Correct materials/UVs** and no missing texture images.
5. **Valid topology** and any agreed performance budget.
6. **Tested rig/animation** when specified.
7. **Saved and re-imported export files** when the destination is available.
8. **QA artifacts and hashes** matching the delivered files.

The intended delivery structure is described in [file layout](../references/file-layout.md). Use the supported validators:

~~~bash
python scripts/forge.py check-evidence planning/project.json --evidence qa/evidence.json --root .
python scripts/check_glb.py deliverables/final.glb
~~~

Use these only after the referenced files truly exist. The output may reject incomplete evidence. For a project-level manifest:

~~~bash
python scripts/forge.py manifest --root . --paths deliverables/final.glb --out manifest.json
python scripts/forge.py verify-manifest manifest.json --root .
~~~

Replace `final.glb` with an actual file you produced. Do not invent artifacts to make a checklist pass.

## 14. Common failures and recovery

| Problem | What to do |
| --- | --- |
| Missing source images | G0-F should request all indispensable items at once; optional views may remain inferred |
| Double jaw or fused moving pieces | Keep separate stable IDs and pivots; fail visual QA until corrected |
| Parts look correct in SVG but wrong in Blender | The SVG is a schematic; inspect actual fixed-camera Blender renders and revise the numeric GCB |
| Incorrectly interpreted Bloxy style | Preserve the block-built language and reference silhouette, rather than blindly decimating polygons |
| Atlas picks an unavailable operator | Verify Blender version, `bpy` signature and context; choose a supported equivalent |
| GCB status says pending | A valid JSON and SVG are not an independent visual approval |
| Image QA manifest passes but art is wrong | Reinspect real pixels and anatomy; metadata-only checks cannot catch all image defects |
| Rig works in Blender but fails in Roblox | Check baked animation, weights, transforms and actual FBX import |
| Python reports Blender unavailable | Install/configure Blender and make the executable accessible; don't claim any mesh was created |
| Tests complain about missing chair PNG fixtures | The public repository intentionally omits three private demo PNGs; create **legitimate** replacement test fixtures before running affected legacy tests |
| Security check finds a token | Do not push; revoke/rotate leaked credentials and notify maintainers privately |

## 15. Updates and support

~~~bash
codex plugin marketplace upgrade blender-forge-pro
codex plugin list
~~~

For a cloned source checkout, use `git pull` in your own clean working branch after reviewing remote changes. For security reports see [SECURITY.md](../SECURITY.md); for contributions see [CONTRIBUTING.md](../CONTRIBUTING.md).

### Reference documents

- [Operating contract](../AGENTS.md)
- [GCB construction schema](../references/construction-schema-v15.json)
- [Workflow gates](../references/workflow-gates.md)
- [Blender execution](../references/blender-execution.md)
- [Target profiles](../references/target-profiles.md)
- [Reference-image QA](../references/reference-image-generation-v17.md)
- [Blender Atlas technique routing](../references/blender-atlas-routing-v18.md)
- [3D example library](../references/3d-excellence-library-v19.md)

**Final principle:** the model is finished only when the **real exported artifact and its evidence** meet the user's request. No planning script, pretty preview, numerical score or passing unit test is sufficient on its own.

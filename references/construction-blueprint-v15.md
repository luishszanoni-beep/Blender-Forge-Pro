# GCB v1.5 | Geometric Construction Blueprint (mandatory G1.5)

## Objective / bounded claims

Replace the fragile `concept art -> one guessed 3D model` handoff with `immutable art references -> reference ledger -> one numeric GCB spec -> deterministic technical plates -> independently audited Blender blockout -> targeted G2 edits`.

A technical plate is NOT a second artistic reference; the source artwork remains the final likeness target. PNG/SVG measurements must be computed from the same numeric JSON, never invented by an image model. Artistic concept views and unknown occluded geometry cannot prove a 100% precise real-world model.

Keep **the same eight specialists** and existing G0–G8, AIR, Geometry Fidelity Lock, artifact validation, rigging, material, and export policies. G1.5 is an intermediate gate, not a ninth specialist or a new runtime model. Existing project.json schema 1.0 remains unchanged. Store GCB data in a separate `planning/gcb/gcb_spec.json` (see `construction-schema-v15.json`).

## When to run / adaptive cost

- **Required** before G2 for reference-matched multi-part/stylized/organic/blockout models, especially complex Roblox Bloxy assets, animated components or strict geometry fidelity.
- **Lightweight** for single components: one overview and one step sheet. Do not generate pointless plates to reach a numeric quota.
- **Medium** for several joints/independent pieces: overview, optional exploded sheet, one sheet per ordered assembly phase.
- **High** for occlusions, custom meshes, articulated parts and many operations: component-level phase sheets + separate Blender views and manual closeups where material (not a promise of 15 arbitrary pictures).
- **May be skipped** for audit-only or already physically measured existing assets with explicit documented reason; do not silently skip G1.5 for a source-art-reconstruction task.
- Use AIR v1.4 routing per task: reference inference/part breakdown (multimodal reasoning), geometry planning (spatial/code), independent G1.5/G7 audit (reasoning), deterministic SVG/PNG/JSON validation (no LLM). Do not spawn agents for a deterministic script; serialize Blender writes. AIR cannot create actual subagents when host adapter is unavailable.

## G0-F -> G1 -> G1.5 -> G2 handoff

First execute the G0-F collection defined in `references/gcb-file-intake-v16.md`: compare existing attachments/files against the requested source, ask once for missing essentials and available improvements. Only then create a reference ledger. When a local intake report exists, do not advance while `ready_for_g1=false`; optional absent views can be inferred and marked as such.


1. Reference Analyst inventories source files (stable IDs, projections, calibrated dimension sources, license, visibility, occlusion, uncertain reverse/inside faces). Mark part measurements individually as `observed`, `inferred` or `unknown`.
2. Geometry Architect plans a stable part hierarchy and topology options. Use `box`, `cylinder`, `sphere`, `cone`, `wedge` or `custom_mesh` with **explicit vertex/face data** (no executable Python embedded in JSON). For organic geometry, use a rough blockout + separately documented sculpt/mesh refinement, not a false claim that primitive-only geometry recreates organic detail.
3. Create `gcb_spec.json`: units, original source IDs, measured or relative scale, per-part transforms, primitive, stable `forge_part_id`, step order, parent, pivot, `separate_mesh: true`, confidence, anchor-to-anchor attachments and tolerance. Do not silently convert `relative` units to mm or claim image pixels provide absolute dimensions.
4. Run `python scripts/gcb.py validate <spec.json>`; **BLOCK** if invalid, missing mandatory step, duplicate ID/identical transform, nonfinite/negative dimensions, bad parent, disconnected anchor relation outside declared tolerance, uncalibrated mm claim or missing observed source IDs.
5. Run `python scripts/gcb.py prepare <spec.json> --out <project>/planning/gcb --require-png` if CairoSVG is installed, or omit `--require-png` for standards-compliant deterministic SVG output when CairoSVG is unavailable. Produce `gcb_spec.json`, `gcb_handoff.md`, `gcb_preflight.json`, dimensioned orthographic/3/4 SVGs and optional PNGs, cumulative phase sheets and, for multiple parts, exploded overview. The exploded offsets are SCHEMATIC and must never replace numeric world coordinates.
6. With a **verified** Blender route, run `blender --background --python scripts/gcb_blender.py -- --spec <project>/planning/gcb/gcb_spec.json --out <project>/work/gcb_blockout`. Save a separate `.blend` blockout, fixed-camera neutral renders of each phase and `gcb_blender_evidence.json`. Do not overwrite the user's original file.
7. Fidelity Auditor reviews BOTH the raw source art and GCB plates, measures credible silhouettes under compatible views, inspects part presence/pose, anchors, duplicate jaw/other repeated elements, seams, intentional vs accidental intersections, required relief, and labels uncertainties. **Reject** G1.5 if a critical unknown is misrepresented or blueprint differs from evidence; request a targeted revision to the GCB JSON, rerun plates (deterministic), then rerun Blender blockout.
8. Only after independent G1.5 audit can the Geometry Architect proceed to G2. A successful CLI, images or `.blend` file is never proof that the model matches the art. Existing G2–G8 audits and final export/reimport remain mandatory.

## Technical plate contract

- Orthographic front `(X,Z)`, side `(Y,Z)`, top `(X,Y)` and a 3/4 orientation; all views derive from the exact same world coordinate geometry.
- Global scale and static camera projection across steps so comparative alignment is not lost.
- Per-phase IDs, highlighted newly added parts, primitives, stable hierarchy, dimensions (in declared units) and origin axes. Callouts must not invent precise unobserved dimensions.
- Exploded visualization must announce that its offsets are **NOT manufacturing/construction coordinates**.
- For rig targets, pass pivots from the GCB to Rigging Specialist. The GCB does not by itself create a tested skeleton, clips or a Roblox-ready rig.
- For custom mesh, mesh data must be explicitly declared; absent geometry is a blocker, not permission to draw imaginary faces.
- Output status `SPEC_VALIDATED_PENDING_VISUAL_QA` means only numeric specification coherence; actual art-fit approval is a separate auditor decision.

## Required evidence and failure modes

G1.5 acceptance requires: complete required-part inventory with unique IDs; source confidence recorded; intended scale basis; structural compatibility of attachments/parent graph; stable numeric spec and synchronised plates; independent reviewer report on model/art; and a real neutral Blender blockout render if Blender execution is available. Missing Blender route -> `PLANNING_ONLY` with G2 unexecuted (do not make false success claims). If no explicit calibrated dimensions, preserve `relative` for speculative proportional geometry.

Blocking examples: two `J1` jaw components; jaw merged into HEAD while a separate jaw is required; child before parent; anchor gap above tolerance; contradictory reference measurements; missing camera calibration claimed as measured mm; a generated art panel contradicting the JSON; blockout wrong silhouette; preview visually rejected despite all CLI tests passing.

`GCB_APPROVED` **is not** `G7_APPROVED`, not physically certified collision, not a deformation/rigging proof, not material fidelity and not Roblox export QA. Geometry engineer and independent auditor must retain separate duties. Changes to GCB after G2 approval invalidate related snapshots and trigger existing Geometry Fidelity Lock + regression checks.

## CLI quickstart

```bash
python scripts/gcb.py validate examples/gcb/demo_bloxy_plant.json
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out /path/to/project/planning/gcb
# Optional; execute only if Blender is actually available in this environment:
blender --background --python scripts/gcb_blender.py -- --spec /path/to/project/planning/gcb/gcb_spec.json --out /path/to/project/work/gcb_blockout
python -m unittest discover -s tests -p 'test_gcb_v15.py' -v
```

CairoSVG optional to convert source-of-truth SVG -> PNG. If missing, SVGs remain usable reference images; avoid a silent/fictitious PNG artifact. Blender is REQUIRED to claim actual 3D blockout execution. Automated geometry checks are broadphase proxies and cannot replace visual inspection.


## V1.7 generated image source handoff (conditional)
When the user explicitly requests the image references to be generated, insert G1-R after G1 and before G1.5: create coherent image references, inspect actual images, and produce a per-part Codex construction plan under `planning/gcb/reference_images`. Use the approved report and image IDs as *visual* inputs only. The numeric GCB JSON remains the construction authority, and all SVG/PNG technical plates from `scripts/gcb.py` must still be rendered from the spec. Pass `--reference-qa-report <image_reference_qa_report.json>` in `gcb.py prepare` to block unreviewed generated-source handoffs when an image-qa report exists. Never claim an inferred viewpoint provides true orthographic physical measurements.

# G0-G8 State Machine + G1.5 Construction Blueprint

Use `PENDING`, `BLOCKED`, `READY_FOR_VISUAL_QA`, `APPROVED`, `REJECTED`. Stages are sequential by default, but authorized component revisions can loop within an earlier stage. Changes to locked features force targeted regression (affected views, connected features, exports). Only the Fidelity Auditor approves evidence-backed quality; technical tools may only mark prechecks as passed.

| Gate | Producer | Acceptance evidence | Blocking condition |
|---|---|---|---|
| G0 intake | coordinator | source inventory, destination, access to Blender | no execution surface claimed as available |
| **G0-F file readiness (v1.6)** | **coordinator + reference-analyst** | **verified accessible input inventory, unified request for essential/recommended assets, acknowledgement of unavailable files; optional local `intake_report.json`** | **reference reconstruction without source art/usable 3D reference; editing without existing source/authorized scene; physically exact sizing without trusted measurements; rig retarget without target skeleton data** |
| G1 reference | reference-analyst | part ledger, calibrated views if known, dimension/occlusion tags | required visible feature omitted or invented hidden feature claimed as observed |
| **G1-R generated modeling references (conditional)** | **reference-analyst + independent fidelity-auditor** | **reviewed generated image files, per-part anatomy/connection checklist, cross-view consistency, construction steps and status-aware GCB handoff** | **critical impossible/incoherent anatomy, duplicate/fused required separate parts, missing evidence or unreviewed generated references** |
| **G1.5 geometric construction blueprint** | **geometry-architect + independent fidelity-auditor** | **single GCB numeric spec, dimensioned technical SVG/PNG plates, step-by-step assembly, anchor checks, art/reference fit review, actual Blender neutral blockout when available** | **duplicate/missing required part, uncalibrated dimensions declared measured, invalid attachment, incompatible numeric/image data, critical art-to-blockout mismatch or unverified G1.5 audit** |
| G2 blockout | geometry-architect | neutral orthos, key dimension measurements | incorrect primary silhouette/ratios |
| G3 geometry relief | sculpt-surface | evaluated mesh plus marked detail ROI and wireframe/closeup | bump/normal only for a feature explicitly requiring geometry |
| G4 materials | material-specialist | material ledger and lighting comparison | reference material critically wrong or unsupported exported shader |
| G5 topology | topology-engineer | triangles, object transforms, normals, nonmanifold audit, UV when required | broken mesh/export budgets |
| G6 rigging | rigging-specialist (conditional) | deformation poses and pivot checks | rig needed but not built/validated |
| G7 fidelity | fidelity-auditor | matched-view evidence, per-part scoring, critical defects and confidence | any critical defect regardless of weighted score |
| G8 export | export-engineer | `.blend`, requested files, GLB stats, re-import check and file hashes | missing, empty, malformed or unverified requested file |

Never advance a required gate from `PENDING` to `APPROVED` merely because a script returned 0. See `references/fidelity-rubric.md` and the `check-evidence` command. If no Blender route is available, do analysis/planning and stop before asserting G2+ execution. If task is an **audit only**, G1/G7 may run on provided screenshots/meshes without authoring. User revision should update only target components and linked dependencies; keep immutable source backups.

G1.5 is a **new intermediate gate**, not a replacement or renumbering of G2-G8. `SPEC_VALIDATED_PENDING_VISUAL_QA` from `gcb.py` means only numerical/structural prechecks; a source-art fidelity verdict requires the independent reviewer. See `references/construction-blueprint-v15.md`.

G0-F is file preflight **before G1**, not a replacement for G1.5. The optional CLI `gcb_intake.py` reports verified local paths only; ChatGPT user uploads require an actual separate inspection. Missing multi-angle views are recommendations and are NOT absolute blockers unless the task explicitly requires them.


G1-R (v1.7) applies **only** when the user requests generating images for use as 3D modeling references. A free-form generated concept does not replace the original user artwork, does not carry calibrated dimensions, and is not automatically the GCB plate. Run `scripts/gcb_image_qa.py` on a reviewed reference-image manifest when local files are accessible; the CLI validates metadata consistency, not anatomy or resemblance. Independent image inspection is mandatory for release to G1.5. See `references/reference-image-generation-v17.md`. No image capability -> record `NOT_GENERATED` and do not claim an asset.

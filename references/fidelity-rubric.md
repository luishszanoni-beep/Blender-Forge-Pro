# 3D Fidelity Auditor | Scoring + blockers

Evaluate only after seeing actual `.blend`/renders in matching cameras. Weighted review (total 100): silhouette 22, proportions/dimensions 20, required parts 18, geometric features 15, materials 10, craftsmanship/topology 10, export fitness 5. Record `null` for unobservable areas rather than arbitrary 10/10. Use evidence IDs for each scored part and explain uncertainty; quality scores have no intrinsic calibration without blinded comparative human benchmark.

**Fatal blockers independent of score:** missing required component; a size error beyond user-approved tolerance when dimension was specified; faux geometry for a geometry-required feature; unapproved change to a locked part; major reversed geometry/intersection; corrupt files or unsupported output; evidence from mismatched camera labeled as matched. `approval=APPROVED` requires zero blockers, every required view actually inspected or explicitly waived by the user, and required geometry proof for specified features.

View setup: render front/back/left/right/top/bottom and 3/4 with CLAY material (uniform neutral), optional wireframe and normal visualization; match lens, camera position/projection/crop to real reference wherever possible. Never compare silhouettes on a perspective image with an arbitrary orthographic render and declare numeric confidence. Render checklist: camera/crop, scales, part names, light, contact shadows, reference metadata.

Automation (`compare_views.py`) measures segmented foreground IoU and centroid error *only for compatible masks*, and produces overlay; it does not automatically assess aesthetic/semantic fidelity. If segmentation/calibration is unsupported, return `INDETERMINATE`. Ask for second angle or dimensions when fidelity demands it; can continue with explicit inferred geometry, never label inferred surfaces exact.

`qa/evidence.json` includes gate record `{state, evidence_files, notes, reviewer, checked_at}`. Do not fabricate `reviewer` or `checked_at`. Auditor independent from model creator: review and record, hand corrections back to relevant specialist.

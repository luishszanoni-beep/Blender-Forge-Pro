# Geometry Fidelity Lock / Targeted Modification Contract

Use a pre-edit Blender inspection as **baseline** and a post-edit inspection for all user-approved or protected parts. Store under `qa/baseline_before.json` and `qa/baseline_after.json`; `scripts/check_baseline.py` evaluates a separate lock spec (example `examples/projects/lock_spec.json`).

Lock types:
- `lock_geometry`: exact evaluated world-space mesh fingerprint. If available, changing any evaluated vertex coordinate or mesh topology invalidates this lock. A highpoly mesh that exceeds fingerprint safety cap receives `UNKNOWN` (cannot be approved automatically).
- `max_bbox_delta_mm`: tolerance for object bounding box dimensions and position; use 0 for strict no-edit constraints, larger only if user allows.
- `lock_materials`: prevent shader/material assignment changes by comparing assigned material names (this does not detect internal shader node changes; evaluate separately).

A geometry lock is an object/part-scoped regression guard, NOT a semantic fidelity score. Objects may be renamed by Blender; use custom property `forge_part_id` and matching object count. New components explicitly authorized may appear outside locked set. When locked parts have changed, do not auto-replace or redraw them; return to the responsible specialist and ask for scoped repair. A fingerprint match does not prove material/UV/surface normals are correct. Do not infer that a missing/invalid fingerprint means "unchanged."

Example:
```
python scripts/check_baseline.py qa/baseline_before.json qa/baseline_after.json --locks planning/lock_spec.json --out qa/regression.json
```

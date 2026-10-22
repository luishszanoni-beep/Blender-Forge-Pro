# Artifacts / Handoff Layout

`input/` immutable reference sources; `planning/project.json`, `planning/part_ledger.md`; `work/checkpoints/*.blend`; `work/source.blend`; `qa/blender_inspection.json`, `qa/views/*.png`, `qa/geo_proofs/*.png`, `qa/view_comparison.json`, `qa/evidence.json`, `qa/gates.json`; `deliverables/final.blend`, `deliverables/final.glb` or specified format; root `manifest.json` (SHA-256 hashes).

Only list actual generated files. Never put a file in deliverables merely because it was requested. Each required part should have stable IDs in manifest and Blender custom props. Attach reference licensing if provided. Mark each check PASS/FAIL/UNKNOWN instead of conflating omitted checks with PASS. ZIP safe paths; no symlinks, archives inside archives, external references, or absolute paths. Generate evidence report after actual artifacts exist; verify archived hashes after packaging.

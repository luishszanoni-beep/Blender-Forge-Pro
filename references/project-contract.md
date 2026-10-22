# Project Contract / Project JSON schema (pragmatic)

`schema_version`: `1.0`; `project_id`: lowercase ASCII letters/numbers plus `-` or `_`, 3-60 chars; `destination`: `render`, `web_glb`, `roblox`, `general`; `mode`: `high_fidelity`, `game_ready`, `adaptive`.

Required: `project_id`, `title`, `destination`, `mode`, `units` (`m`), `references` array (can be empty for original designs), `parts` nonempty, `deliverables` nonempty. `scale` and `dimensions_mm` should be recorded when known. For each reference use `{id,path,view,projection,observations}`; `projection` is `orthographic`, `perspective`, or `unknown`. A file path is relative to project root; a real source must exist for checked measurements. References with `projection=unknown` are NOT suitable for numeric pixel silhouette comparison. A claimed orthographic view must really be orthographic, not merely a straight-on perspective photograph.

Each part: `{id,label,required,reference_ids,features,confidence,locked}`. Confidence = `observed`, `inferred`, or `unknown`; feature examples `{id,label,representation,required,source_ref_ids}`, representation `geometry`, `material`, or `either`. Use `representation=geometry` for silhouette, seam relief or openings where volume matters. Optional `min_relief_mm` indicates measurable evaluated mesh geometry (do not infer from renders).

Optional: `budgets={triangles_max, materials_max, glb_size_mb_max}`, `checks={required_views:[...], dimension_tolerance_mm}`; `rig_required` boolean; `notes`; `approval_baseline` with external saved manifests/hashes; `ref_source` text for attribution and rights. All geometry is defined in meters in Blender; store user-facing dimensions as mm and convert /1000.

Use stable part IDs across edits; never use mutable Blender object names as the only source of identity. Example `examples/projects/demo_chair.json`. Use `scripts/forge.py validate-project` to catch missing refs and malformed manifests. An exact verified part match requires explicit reference evidence and quality inspection, not simply a valid JSON manifest.

# Real Geometric Detail Protocol

A "modeled texture" in the user's sense means **surface geometry has been edited or geometry generated**, not just a PNG normal/roughness map. Classify each visible effect as: `structure` (silhouette / opening / physical assembly), `medium-relief` (seam, groove, stitch, bevel, sculpt line), `micro-detail` (pores, grain). Default strategy: structure/medium-relief must be geometric if the project demands; tiny detail may use PBR/normal maps unless user explicitly requires actual geometry. Never force millions of faces for invisible subpixel features.

G3 geometry proof for each `representation=geometry` required feature:
1. Record stable feature ID and linked part; isolate view layer or selected object.
2. Show actual Blender mesh/evaluated modifier result: edit-mode/wireframe and clay closeup from meaningful view, with rulers/dimensions if measurable. A shader bump/displacement output may not survive export: inspect evaluated mesh and export target.
3. Provide at least one of: vertex displacement in base-vs-evaluated snapshot, actual extruded mesh for seam/stitches, or revised mesh surface cross-section. Name `forge_part_id`, `forge_feature_ids` on objects where possible. Topology/dimension counts alone do not prove intended feature.
4. Export as required and re-import; check that target representation persists. Geometry Nodes/Modifiers may need `Apply`/bake, and render-only material displacement may not travel to GLB.
5. Have Fidelity Auditor inspect output under neutral materials and compare with source, recording confidence/uncertainty.

Evidence schema per feature `geometry_proofs[]`: `{feature_id,part_id,technique,mesh_object,evidence_files:[...],evaluated_mesh_verified:boolean,export_verified:boolean,reviewed:boolean}`. Cannot mark APPROVED if any required geo feature lacks proof or review. Examples: stitch can be a curve with bevel converted to mesh; upholstery quilting needs real mesh depressions; small leather grain can be normal if allowed by brief, or displacement mesh where silhouette/resolution benefits.

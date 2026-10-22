# Benchmark Execution Sheet (UNEXECUTED)

Run these with real Blender execution. A green `unittest` suite only validates scaffolding and error handling; it cannot prove a 3D artist's quality.

| Benchmark | Source input | Baseline | Evidence required | Reject when |
|---|---|---|---|---|
| TECH-CHAIR | 3 orthos + dimensions + seam closeup | manual/model without plugin | measured width/depth/height, neutral renders, underbody, actual stitch mesh, GLB reimport | missing mechanism/legs, incorrect dimensions, pseudo-geometry |
| HARD-SURFACE | prop photos with known chamfer radii | simple primitive script | front/side/3-4 clay, measured bevel, surface detail proof | silhouette, booleans, normals wrong |
| STYLIZED-RIG | 5-view character sheet + animation need | generic blockout | multiangle anatomy, 6 deformation poses, exported skeleton | identity drift, skin tears, wrong pivot |
| SCULPT-RELIEF | quilt/stone/engraving closeups | shader-only flat plane | evaluated vertex mesh + wireframe + depth section + GLB | detail exists only as bump/normal |

Record for each: reference UUID, Blender version/build, execution route, actual inputs, time/calls, output hashes, views inspected, score dimensions and blockers; 2 independent human reviewers for semantic likeness where possible. Target benchmark quality thresholds must be selected with a calibration set; no made-up 70/100 or 95% similarity from arbitrary photos.


### V1.3 execution status
`NOT_EXECUTED` for all four benchmark cases. The new schema validates records and compares baseline/candidate only after real images, GLB/BLEND artifacts and reviewer evidence exist. Do not count 180+ unit tests as one artistic benchmark.

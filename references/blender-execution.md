# Blender Execution Bridge / Trust Boundary

Run `scripts/forge.py doctor` and `scripts/blender_bridge.py doctor`. Blender is a separate executable with `bpy`; ordinary Python running outside Blender does not imply bpy is available. Supported routes: explicitly authorized Blender MCP connector (tool-specific actions), installed Blender CLI via known worker script, or manual Blender execution documented to user. Do not fabricate a completed model based on plans alone. Inspect actual tool availability first.

The bridge invokes ONLY the plugin's bundled trusted `scripts/blender_worker.py`, never a user-supplied Python path. It uses argument vectors (`subprocess.run([...])`, no shell), a timeout, `--factory-startup` when creating a diagnostic scene, and a caller-approved output directory. It does NOT automatically install software, plugins, packages, drivers, or sample assets. Reading a `.blend` may cause Blender to process embedded scene data; use trusted sources and isolated workfiles as required by environment security policy. Validate file paths and backups before running.

Commands:
```
python scripts/blender_bridge.py doctor --blender blender
python scripts/blender_bridge.py run --task diagnostic-sample --out /abs/project/work --blender blender
python scripts/blender_bridge.py run --task inspect --blend /abs/project/work/diagnostic.blend --out /abs/project/qa --blender blender
python scripts/blender_bridge.py run --task render-views --blend /abs/project/work/diagnostic.blend --out /abs/project/qa/previews --blender blender
python scripts/blender_bridge.py run --task geometry-proof --feature-id seat_raised_seam --blend /abs/project/work/diagnostic.blend --out /abs/project/qa/geo_proofs --blender blender
python scripts/blender_bridge.py run --task export-glb --blend /abs/project/work/diagnostic.blend --out /abs/project/deliverables --blender blender
```

`blender_worker.py` diagnostic mode is a **functional smoke fixture**, not an artistic modeler. For actual modeling, a specialist must create in Blender using authorized actions, project constraints, and intermediate checkpoints; it may use Blender MCP tools or implementation-specific operations. Rendering all views can be costly; use contact sheet low resolution for early gates, then higher-quality final renders. Save checkpoint `.blend` files and do not overwrite originals.

API portability: verify Blender version and `bpy.ops.export_scene.gltf`, `bpy.ops.import_scene.gltf` existence at runtime; operators and shading nodes differ across versions. If unavailable, mark unsupported rather than false `PASS`. Blender Python API: https://docs.blender.org/api/current/ ; glTF exporter reference: https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html .


## Tasks V1.3 (only the trusted bundled worker)

```
python scripts/blender_bridge.py run --task build-recipe --spec <recipe.json> --out <new_dir> --blender <blender>
python scripts/blender_bridge.py run --task apply-repair --blend <input.blend> --spec <repair.json> --out <new_dir> --blender <blender>
python scripts/blender_bridge.py run --task create-lods --blend <input.blend> --spec <lod.json> --out <new_dir> --blender <blender>
python scripts/blender_bridge.py run --task build-variant --blend <input.blend> --spec <variant_build.json> --out <new_dir> --blender <blender>
python scripts/blender_bridge.py run --task assembly-audit --blend <input.blend> --spec <assembly.json> --out <new_dir> --blender <blender>
```

All tasks require a bounded JSON spec (<=256 KB) and use only static supported operator types. `build-recipe` is intentionally on a fresh Blender scene; other tasks load a provided source as data with autoexec disabled. `apply-repair` demands a matching inspect snapshot hash and saves only to a separate candidate file. No arbitrary `.py` path is accepted. Blender CLI/bpy execution was NOT tested in the authoring environment; run a local smoke test before real production.

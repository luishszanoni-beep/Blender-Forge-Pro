# Target Profiles (choose adaptively)

**high_fidelity render**: retain subdivision/real sculpt layers and non-destructive procedural materials in `.blend` master; produce exportable lowpoly derivative only if requested. Optimize for evidence quality not minimal triangles. Use physically reasonable radius, thickness and wear. Larger textures alone never replace geometry.

**web_glb**: preserve units, material naming, base color/metallic/roughness texture paths and export-safe glTF PBR. Limit triangles/materials/draw calls by explicit budget; default budgets are provisional, never universal. Check re-import/export, GLB structure, `visible` surfaces and pivot; verify variants if configurator. Do not assume Blender procedural shader graph survives GLB; bake when appropriate and allowed. Avoid leaking hidden alternate materials or unrequested combinations.

**roblox**: favor clear silhouette at game distances, managed part counts and tri budgets, predictable pivots/naming, rig/skin constraints for engine. Roblox import compatibility depends on current engine pipeline and model type; do not invent compatibility. Verify exported units, bone transforms, skin weights and viewport appearance with the actual engine if accessible.

**general/adaptive**: clarify intended size, engine and animation need or keep both highpoly source and optimized derivative when feasible. Do not force a gaming poly budget for product imagery or use cinematic millions of triangles in a live web GLB.

LOD0 detailed near camera, LOD1 medium, LOD2 distant optional if real-time scale warrants it. Give part constraints and numeric budgets only when user/spec provides them; otherwise list assumptions and make budgets configurable per project.

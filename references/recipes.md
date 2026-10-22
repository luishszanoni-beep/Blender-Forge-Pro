# Specialization Recipes (load on demand)

## Furniture / manufactured objects (e.g. configurable chair)
- Input: actual technical manuals + photo/drawings + units + permissible product options. Inventory every mechanism, support, headrest, casters, armrests and upholstery construction supported by documentation.
- G2: dimensions/clearances and mechanically plausible joins before upholstery details.
- G3: if the user demands physical seam/quilting/mesh, use extrusion/sculpt or converted curves with evaluated mesh proof, not just fabric PNG. A visual texture may supplement physical detail.
- Variant strategy: separate structural options and compatible materials; never generate forbidden combinations. Protect product SKU/part IDs and export only approved configurations.
- For realtime web/GLB, use lowpoly derivatives and verify materials in glTF-compatible PBR and actual viewer where possible.

## Stylized character / creature / Roblox Stand
- Explicitly capture stylization traits (silhouette, proportion exaggeration, asymmetric armor, face details, scarf/cape shapes). Treat all character sheets as multi-view cross-checks; no invisible backside claims without source.
- G2: consistent anatomical construction and joint placement; avoid cubes as final anatomy unless style demands it.
- G3: sculpt plates/engravings/cloth thickness, distinguish actual folded geometry from image-only folds. Frame the character at target gameplay distance when judging necessary detail.
- G6: optional armature with pose tests and Roblox export constraints. Rigid armor should follow bones without unintended skin warping.
- Export: test rig/scale/shading in target engine if it is available; no automatic statement of Roblox compatibility from GLB parsing alone.

## Hard-surface product/prop
- G2: measured thicknesses, symmetry/intentional asymmetry, bevel radii and mechanical connections.
- G3: drill/engrave grooves in mesh for required cut depth; small procedural scratches may remain shader detail if permitted.
- G5: check shading across Boolean joins and modifier application, edge weighting, triangle density at curved surfaces.

## Organic sculpt / cloth / stone
- Start with large masses; use multires/voxel remesh only after silhouette and volume.
- Use physical wrinkle direction based on tension/gravity/anatomy; random displacement is not convincing sculpting.
- Preserve sculpt master, create retopology derivative for animation or export, verify displacement in neutral light.

## Source ambiguity resolution
- If only 1 image exists: model visible side faithfully and label all other surfaces inferred; provide 3/4 drafts for feedback, never claim exact reverse. If measurements conflict: prioritize explicit user-provided manufacturer specs, then reference documentation if authoritative, then labeled best-effort approximations; ask for clarification only when conflict blocks required accuracy.

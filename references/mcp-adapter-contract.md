# Blender MCP / GUI Capability Adapter

Blender MCP is optional and **not part of this plugin by default**. When connected to the user's Blender environment, first enumerate actually exposed actions; do not assume that a tool called `create_object`, `run_python` or `render_scene` exists. Require confirmed capabilities for: scene inspection, controlled construction/editing, selection/properties, checkpoint save, multi-angle render, mesh statistics and export. If any capability is unavailable, route that stage to an approved alternative or mark it not executed.

Minimum safe transaction per modeling operation:
1. Read current scene and source `.blend` path; create backed-up stage checkpoint.
2. Identify stable part/feature IDs and user-approved immutable regions, then precompute expected changes.
3. Execute one bounded operation in Blender (no arbitrary code sourced from the user/reference or web).
4. Re-read the affected objects and compare dimensions/geometry with the checkpoint.
5. If operator errors or changes outside scope, revert checkpoint, report reason and avoid repeating blindly.
6. Render/inspect evidence before marking a geometric stage complete.

Never give a model-generated instruction direct arbitrary filesystem or shell access through MCP. Require user permission for access to external directories, software installs, or uploads. The host that owns Blender remains in charge of authentication, approvals and file permissions. Use the executable bridge when Blender CLI is available; do not call it via MCP unless the connector advertises permissioned filesystem/command actions.

When scripting with `bpy`, choose non-destructive stage changes (new named collections/objects, modifiers) and stable custom IDs. Protect approved geometry by `check_baseline.py`. For a remote Blender service, save the actual `.blend` and evidence to an accessible mount only if that host permits it; do not fabricate a sandbox link.


## V1.3 fixed tasks vs. authorized MCP

Before calling remote Blender, inspect actual exposed actions. The bundled fixed procedural recipe is a **Blender CLI worker**, not an automatically available MCP action. An MCP bridge may implement analogous bounded operations only after explicit authorization and capability discovery. Do not synthesize tool names or claim that source-controlled JSON can execute itself in a browser. For repair, require real snapshots and respect `protected_part_ids` / `forge_locked`.

# Quick Start — Blender Forge Pro

New to the toolkit? Complete these steps in order. For marketplace setup first, follow the [installation guide](INSTALLATION.md).

## 1. Describe the target

Tell Codex what you need, where the model will be used, which style is mandatory, and what must remain editable. Example:

> Create a Roblox-compatible, block-built fantasy plant with a separate animated jaw. I need an editable Blender source, FBX export, an idle animation and a faithful visual match to the supplied references. Ask for all genuinely essential files at once. Do not invent dimensions. Start by generating a GCB blueprint and wait for visual review before detailed modeling.

The word **Bloxy** denotes the requested block-built design language, not merely a low polygon count.

## 2. Supply evidence

Attach or identify any front/side/back/top images, close-ups, scale references, existing mesh files, texture sources and animation needs. Unavailable optional views can be inferred **with explicit uncertainty**; required source art for a faithful reconstruction cannot be silently replaced with guesses.

## 3. Run the non-destructive checks

From the repository root:

~~~bash
python scripts/forge.py doctor
python scripts/excellence_reference_router.py validate
python scripts/blender_tool_router.py verify-index
python scripts/gcb.py validate examples/gcb/demo_bloxy_plant.json
~~~

## 4. Generate a sample construction plan

~~~bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out work/gcb-demo
~~~

Browse:

- `work/gcb-demo/gcb_spec.json` — canonical parts, dimensions and anchors.
- `work/gcb-demo/gcb_handoff.md` — Codex-friendly, ordered build instructions.
- `work/gcb-demo/sheets/` — deterministic SVG overview, exploded diagram and assembly steps.
- `work/gcb-demo/blender_tool_plan.md` — advisory Blender technique choices.

These are **demonstrations of planning**, not proof that Blender created an asset.

## 5. Connect a real Blender runtime (when modeling)

~~~bash
python scripts/blender_bridge.py doctor
~~~

Or specify the installed executable:

~~~text
python scripts/blender_bridge.py doctor --blender "<absolute-path-to-blender-executable>"
~~~

For a temporary numeric GCB blockout when Blender is actually available:

~~~bash
blender --background --python scripts/gcb_blender.py -- --spec work/gcb-demo/gcb_spec.json --out work/gcb-blockout
~~~

Run only in a trusted environment. This produces **blockout evidence**, not a detailed final model. Compare real renders with the user's references before proceeding.

## 6. Approve through evidence, not promises

An asset should not be marked complete until geometry, real material behavior, topology, optional animation, multi-view fidelity, and destination re-import have been independently checked.

For step-by-step examples and every command group, open the **[User Manual](USER_MANUAL.md)**.

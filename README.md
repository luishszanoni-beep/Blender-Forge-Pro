# Blender Forge Pro

**Reference-driven Blender 3D production with Codex — version 1.9.0.**

Blender Forge Pro is a **skills-first modeling toolkit** for reconstructing and creating 3D assets. It plans geometry from reference evidence, checks structural consistency, selects appropriate Blender techniques, supports rigging and materials, and produces verifiable handoffs for real Blender execution.

It is **not** a one-click image-to-3D converter: scripts that validate specifications do not magically generate final meshes, textures, animations, or Roblox-ready models.

## Documentation

| Guide | Purpose |
| --- | --- |
| **[Installation guide](docs/INSTALLATION.md)** | Install from GitHub in Codex CLI, use a local checkout, or access a workspace plugin in ChatGPT |
| **[Quick start](docs/QUICK_START.md)** | First-run checks and a simple end-to-end GCB example |
| **[User manual](docs/USER_MANUAL.md)** | All eight skills, G0–G8 gates, reference QA, Blender execution, export, troubleshooting |
| [Security policy](SECURITY.md) | Report issues securely and avoid unsafe inputs |
| [Contributing](CONTRIBUTING.md) | Tests, pull requests, and repository rules |
| [Third-party notices](THIRD_PARTY_NOTICES.md) | Licensing and external 3D references |

## Install in Codex CLI

Install the repository marketplace, then the plugin (requires a Codex version supporting plugin marketplaces):

~~~bash
codex plugin marketplace add luishszanoni-beep/Blender-Forge-Pro --ref main
codex plugin add blender-forge-pro@blender-forge-pro
~~~

Then start a **new Codex session**; choose the installed Blender Forge Pro plugin in the plugin browser (`/plugins`) or refer to its functionality in your prompt. Full instructions and alternatives: **[Installation](docs/INSTALLATION.md)**.

> The GitHub repository is a public source distribution. It is **not automatically listed in the universal ChatGPT Plugins Directory**. Workspace/plugin-directory access is separate from Codex marketplace installation.

## What is included?

| Component | Function |
| --- | --- |
| **8 specialist skills** | Reference analysis, geometry architecture, sculpt/surface, PBR materials, topology, rigging, fidelity QA, export |
| **AIR v1.4** | Advisory model/effort routing, without pretending to spawn or switch models |
| **GCB v1.5** | Geometric Construction Blueprint: part IDs, dimensions, attachment anchors, pivots, deterministic SVG plates, Codex assembly instructions |
| **G0-F v1.6** | Adaptive file intake and one consolidated request for missing essential references |
| **G1-R v1.7** | Structural/anatomical QA of **user-requested generated** modeling-reference images |
| **ATSE v1.8** | Indexed lookup of 407 techniques from the bundled Blender 5.2.2 LTS Atlas |
| **3DERL v1.9** | 15 curated CC0 3D example references, chosen by task and style; remote previews are not local assets |

## Requirements

- **Python 3.10+** for core command-line tools; **3.11+ recommended**.
- A recent **Blender** installation for real mesh/rig/render/export work. The included Atlas targets **Blender 5.2.2 LTS**; verify installed `bpy`/operator compatibility.
- **Codex CLI** for marketplace-based plugin installation, or an eligible ChatGPT/Codex workspace installation.
- Additional modules such as CairoSVG, Pillow or PyMuPDF are optional and only needed by specific functions. No credentials, add-ons, or remote assets are installed automatically.

## Smoke checks

Run these from the repository root:

~~~bash
python scripts/forge.py doctor
python scripts/excellence_reference_router.py validate
python scripts/blender_tool_router.py verify-index
python scripts/gcb.py validate examples/gcb/demo_bloxy_plant.json
~~~

Build a **technical plan**, not a finished model:

~~~bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out work/gcb-demo
~~~

The output includes `gcb_spec.json`, `gcb_handoff.md`, SVG construction sheets and advisory tool recommendations. Visual fidelity remains **pending independent review**.

## Typical workflow

**Input audit → Reference analysis → GCB planning → Blender blockout → Geometry/materials/topology → Optional rig/animation → Independent visual QA → Export and destination re-import.**

For Roblox/Bloxy models, preserve the requested block-built styling (not necessarily low-poly), use separate articulated parts, verify object pivots and animation loops, and test actual FBX import in Roblox Studio.

## Safety and licensing

This repository is distributed under its existing [MIT license](LICENSE) for code. The Blender Atlas and external reference assets have separate provenance and terms; see [third-party notices](THIRD_PARTY_NOTICES.md). Do not commit secrets or user-specific Blender assets. Review [SECURITY.md](SECURITY.md) before executing untrusted input.

**Validation distinction:** passing Python tests does **not** establish visual resemblance, Blender execution, rigging quality, or successful Roblox Studio import.

> Legacy Portuguese-language quick-start notes are retained under `INICIO_RAPIDO_PTBR.md` and `INICIO_RAPIDO_GCB_PTBR.md` for compatibility. The maintained public-facing guides are in English.

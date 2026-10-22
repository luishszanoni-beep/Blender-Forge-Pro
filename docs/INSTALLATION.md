# Installing Blender Forge Pro

**Version covered:** 1.9.0 · [Repository](https://github.com/luishszanoni-beep/Blender-Forge-Pro)

This is a practical installation guide for the **public GitHub package**. Blender Forge Pro is an instruction-and-script plugin: installing its skills does not install Blender, provide remote desktop access, or automatically connect an agent to your local `.blend` files.

## Before you start

| Component | Needed for |
| --- | --- |
| Codex CLI with plugin-marketplace support | Installing from this GitHub repository as a Codex plugin |
| ChatGPT/Codex desktop account with relevant plugin access | Installing from an available workspace or personal plugin directory |
| Python **3.10+** (3.11+ recommended) | Local validators, routing, blueprint generation |
| Blender | Real 3D modeling, rendering, animation and export |
| Git | Cloning/updating a working source checkout |
| Internet access | First GitHub marketplace install and optional preview images |

The public repository includes `plugin.json`, `.codex-plugin/plugin.json` and eight `skills/*/SKILL.md` entry points. It also includes the Atlas PDF used by the tool selector. The plugin does **not** bundle Blender itself.

## Option A — Install from GitHub in Codex CLI (recommended)

Open your terminal or PowerShell and make sure `codex` is installed and signed in. For supported versions, run:

~~~bash
codex plugin marketplace add luishszanoni-beep/Blender-Forge-Pro --ref main
codex plugin marketplace list
codex plugin list --available --json
~~~

The repository provides `.agents/plugins/marketplace.json` with the marketplace name **`blender-forge-pro`**. Install its single plugin:

~~~bash
codex plugin add blender-forge-pro@blender-forge-pro
codex plugin list
~~~

Then start a **new Codex session**:

~~~bash
codex
~~~

In Codex's interactive session, type `/plugins` to open the plugin browser and confirm that **Blender Forge Pro** is installed and enabled. Ask for a modeling plan or provide a reference asset and destination.

**If your Codex release does not recognize `codex plugin marketplace` or `codex plugin add`:** update Codex first. Some supported interfaces offer the equivalent **Add Marketplace → Install** workflow. The Codex IDE extension does not currently provide the same plugin browser; use Codex CLI or the supported desktop UI for plugin installation.

### Update or uninstall

~~~bash
codex plugin marketplace upgrade blender-forge-pro
codex plugin list
codex plugin remove blender-forge-pro@blender-forge-pro
~~~

An update may require a new Codex session to load the refreshed version. Plugin installation and local Git clones are distinct: updating one does not necessarily update the other.

## Option B — Clone the repository for local use

This installs the **source files**, not the plugin into the ChatGPT web interface:

~~~bash
git clone https://github.com/luishszanoni-beep/Blender-Forge-Pro.git
cd Blender-Forge-Pro
python scripts/forge.py doctor
python scripts/excellence_reference_router.py validate
python scripts/blender_tool_router.py verify-index
~~~

To register this checkout as a local Codex marketplace when supported:

~~~bash
codex plugin marketplace add .
codex plugin list --available --json
~~~

Install `blender-forge-pro` from the marketplace name reported by that list. The supplied repository marketplace is named `blender-forge-pro`; if your Codex version uses a different local alias, use the name it reports.

If you only need the Python utilities, the commands above work **without installing the plugin in Codex**. Run them from the repository root.

### Blender executable connectivity

If Blender is on the system PATH:

~~~bash
python scripts/blender_bridge.py doctor
~~~

If not, specify an existing, trusted Blender executable with `--blender`:

~~~text
python scripts/blender_bridge.py doctor --blender "<absolute-path-to-blender-executable>"
~~~

On Windows, locate `blender.exe` in the actual installed Blender directory. Do not assume the version or installation path. The bridge's `doctor` command only checks executable availability; it does not prove modeling or asset fidelity.

### Optional dependencies

The core routing and JSON checks use Python's standard library. Optional capabilities require separate tools:

- **CairoSVG** for PNG copies of GCB plates; SVG output is produced without it.
- **Blender's `bpy` runtime** for scene generation; ordinary Python scripts do not replace it.
- **Pillow / other analysis dependencies** for image operations where indicated by the specific command.
- **PyMuPDF** when rebuilding the Blender Atlas index from a PDF, not for normal indexed lookups.

Install optional dependencies only after reviewing the feature and in a virtual environment if appropriate. Never paste private tokens into a repository or issue.

## Option C — ChatGPT or desktop plugin directory

If **Blender Forge Pro** is already available to your ChatGPT account/workspace:

1. Open **Plugins** in ChatGPT or the supported desktop app.
2. Find **Blender Forge Pro** under your workspace or personal plugins.
3. Select **Install** if available, then start a fresh conversation.
4. Request a 3D asset workflow or invoke the plugin through the UI where supported.

**Important:** making this GitHub repository public does **not** automatically publish the plugin to the universal ChatGPT directory. The author's existing account plugin may be private to a workspace. Other users will need GitHub/Codex marketplace installation or an authorized workspace distribution route. Installation on ChatGPT web alone does not grant access to a Blender executable on your computer.

## Verify a successful installation

From a local copy of the repository:

~~~bash
python scripts/forge.py doctor
python scripts/excellence_reference_router.py validate
python scripts/blender_tool_router.py verify-index
python scripts/gcb.py validate examples/gcb/demo_bloxy_plant.json
~~~

Expected behaviors:

- `doctor` reports Python and tool availability. Blender may be unavailable if it is not on PATH.
- Reference-catalog validation checks the catalog's metadata; it does not download all 3D assets.
- `verify-index` must verify the bundled PDF's SHA-256 against the Atlas index.
- The example GCB `validate` command should report a structurally valid specification; it does not produce a finished 3D model.

For an offline GCB preparation example:

~~~bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out work/gcb-demo
~~~

Inspect `work/gcb-demo/gcb_handoff.md` and `work/gcb-demo/sheets/`. The output is a **planning artifact**, not a Blender render.

## Security before production work

- Review `SECURITY.md` and scan unfamiliar attachments before allowing scripts to process them.
- Keep source references and original `.blend` files immutable.
- Avoid enabling arbitrary script auto-execution from untrusted files.
- Use separate project directories; Blender Forge Pro scripts should work on copies of assets.
- Check app permissions and script paths before connecting Codex to your desktop/Blender environment.

## Troubleshooting

| Symptom | Explanation / next step |
| --- | --- |
| `codex: command not found` | Install or upgrade the official Codex CLI; verify your PATH and login |
| `plugin marketplace` command unavailable | Codex version/surface does not support this route; upgrade or use an available desktop installation method |
| Plugin missing from `/plugins` | Check marketplace list, verify installed state, and restart the Codex session |
| `blender_on_path: false` | Blender is absent from PATH; pass `--blender` to the bridge |
| Atlas checksum error | Ensure the original PDF exists at `assets/blender-atlas/Atlas_Blender_5_2_2_LTS_407_Ferramentas_e_11_Abas.pdf` without modifications |
| GCB PNGs not generated | SVG is the default; optionally install CairoSVG and use `--require-png` |
| Assistant reports an approved model without render evidence | Approval is unverified; request an actual Blender run, multi-view renders and a fidelity audit |
| Unable to modify `main` on GitHub | The repository's ruleset requires a branch, PR and passing CI; do not force-push |

## Official references

- [OpenAI: Package and distribute plugins](https://developers.openai.com/plugins/build/plugins)
- [OpenAI: Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference)
- [OpenAI: Plugins in ChatGPT](https://help.openai.com/en/articles/20001256)

Next: **[Quick start](QUICK_START.md)** → **[Complete user manual](USER_MANUAL.md)**.

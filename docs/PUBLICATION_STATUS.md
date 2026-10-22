# Public Source Publication and Security Audit

**Reviewed on:** October 22, 2026 · **Source version:** Blender Forge Pro v1.9.0

## Source review

The original plugin inventory contained **135 files** (131 text sources and four binary files). All 131 text files were previously reviewed with heuristic searches for known API-key families, GitHub credentials, private-key blocks, webhook tokens and other common secret patterns. The review found **no confirmed live credentials** in the textual sources.

A synthetic Basic-Authentication URL in a negative unit-test fixture was rewritten during the public import to avoid a misleading credential-like literal.

This is **not a mathematical guarantee** that no unknown secret or vulnerability exists. Follow [Security Policy](../SECURITY.md) and perform an independent audit before using sensitive assets or deploying model-execution infrastructure.

## Bundled Blender Atlas

The original Atlas PDF has now been uploaded to:

`assets/blender-atlas/Atlas_Blender_5_2_2_LTS_407_Ferramentas_e_11_Abas.pdf`

The expected SHA-256 is:

`1e8170c7631d1c86a073f45c926eea2e20157f104545eaa868c9ae401c9104cd`

Verify the local copy with:

~~~bash
python scripts/blender_tool_router.py verify-index
~~~

The Atlas is a **secondary guide**, not a substitute for current Blender API documentation or actual runtime tests.

## Intentionally excluded historical fixtures

The three demonstration PNG files `chair_front.png`, `chair_side.png` and `chair_top.png` were not imported into this public repository by maintainer decision. They are **not pending uploads**. Some historical test cases still reference those files; such cases need clean-room replacement fixtures before running the complete legacy test suite.

## Current GitHub protections

The `main` branch ruleset is **active**, requiring pull requests and the `source-checks` GitHub Actions job while blocking branch deletion and force pushes. Secret scanning/push-protection toggles require separate administrative verification; a workflow file does not prove they are enabled.

## Production assurance

The public source validates planning and routing logic. It does **not** establish that all Blender operators were executed, that a model looks correct, that a rig imports into Roblox, or that every optional test fixture is present.

# Contributing to Blender Forge Pro

Contributions are welcome when they preserve the eight-skill pipeline, transparent evidence gating and security constraints.

## Workflow

1. Open an issue describing the problem or feature **without sharing private files or credentials**.
2. Create a **feature branch**. The protected `main` branch does not allow direct updates or force pushes.
3. Keep pull requests focused. Document any change to Blender compatibility, pipeline gates, model routing, license attribution or external downloads.
4. Run the available checks before requesting a merge:

~~~bash
python scripts/security_scan.py
python -m compileall -q scripts tests
python scripts/excellence_reference_router.py validate
python scripts/blender_tool_router.py verify-index
~~~

5. Add or update targeted tests. Model-editing claims require real Blender output and visual QA; metadata validation alone is insufficient.
6. Wait for the required **`source-checks`** GitHub Actions job to pass, then merge the pull request.

## What not to contribute

- Tokens, secret-bearing configuration, arbitrary remote execution hooks or unreviewed downloads.
- Third-party models or images without license and provenance.
- Mock artifacts presented as real Blender outputs.
- New dependencies without rationale, compatibility notes or risk review.
- Force-pushes, bypass attempts or branch history rewriting.

## Test fixture note

The public GitHub repository intentionally excludes three historical chair PNG reference fixtures. Some legacy tests still refer to those filenames; tests requiring them need independently created and appropriately licensed test fixtures before they can run successfully. Do not insert fabricated private artwork as a replacement.

## Documentation

Public onboarding documentation is maintained in **English**:
[Installation](docs/INSTALLATION.md), [Quick Start](docs/QUICK_START.md) and [User Manual](docs/USER_MANUAL.md). Older Portuguese quick starts remain for backward compatibility.

# AIR Concurrency and Scene Write Protection

**One `.blend` scene, one active writer**. AIR schedules independent read-only analysis in limited parallel waves, and places writers in serial exclusive waves. The JSON plan's `schedule` is descriptive; only a connected runtime can create actual subagents. `max_parallel_readers` bounds waves; no writer shares its wave with any other task.

AIR provides a cooperative lease `scripts/air.py lease-acquire / lease-check / lease-release`. This is a filesystem **reservation**, not a native Blender lock, does not intercept Blender GUI edits and does not authorize access to the user's private filesystem. Keep the token private; the plugin stores its SHA-256 only and does not put token in the `.blend` metadata. No automatic stale-lock breaking (manual investigation is required after crash).

```bash
python scripts/air.py lease-acquire --project-root /absolute/project --holder geometry-agent
# Keep returned token privately for that run. Never paste it into chat logs.
python scripts/air.py lease-check --project-root /absolute/project --holder geometry-agent --token <SECRET>
python scripts/air.py lease-release --project-root /absolute/project --holder geometry-agent --token <SECRET>
```

For Blender CLI writes mediated through the Forge bridge, invoke with all of `--air-project-root`, `--air-holder`, `--air-token`, set `FORGE_AIR_MANAGED=1` in the execution environment, and restrict input/output paths to that project. Bridge validates lease and refuses partial credentials, while preserving the old unmanaged V1.3 CLI contract for existing projects. An external MCP writer must implement equivalent transaction and lease checks explicitly; a JSON schedule does not enforce MCP writes on its own.

Scene modifications must also use snapshot hash, feature ID, locked-part baseline, and output to **new checkpoint file**, followed by target-region regression and independent audit. The lease prevents *cooperating* simultaneous writes; the Geometry Fidelity Lock protects approved content from unintended changes. They are complementary, not interchangeable.

Host adapter must transition subagent lifecycle only with actual evidence: `PLANNED -> DISPATCHED -> RUNNING -> COMPLETED/FAILED`; audit may later mark `APPROVED/REJECTED`. Do not label `DISPATCHED` based on AIR CLI plan alone. On failure, stop/release lease only after executor termination and snapshot verification. No arbitrary user-provided command execution or autonomous installation.

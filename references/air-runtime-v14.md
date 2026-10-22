# AIR Host Adapter / Runtime Capability Negotiation V1.4

AIR is intentionally provider-agnostic. Its Python registry can **recommend** which model and reasoning effort to use per task. It does NOT call OpenAI APIs, discover models in a user's account, spawn subagents, set host model configuration, fetch billed prices or run Blender by itself. The ChatGPT plugin upload API cannot grant those powers. Keep the distinction explicit.

### Actual delegation adapter contract (for an authorized host)

1. Enumerate the host's actual available model IDs and each model's supported `reasoning.effort`, I/O modalities, context window, tools, and live execution permissions. Record probe timestamp and capability source; do not trust a synthetic fixture or stale config.
2. Map AIR `extra_high` -> provider-specific effort **only if supported** (for some OpenAI models this is `xhigh`). Otherwise reject/renegotiate the model-effort combination. Other levels similarly require verification; do not silently assume every model supports all four.
3. Confirm `spawn_subagent`, model/effort override and parallelism support in that particular host. If unavailable, use a **single-agent advisory workflow**. The registry's `verified_on_host` flag is supplied by the caller and is NOT independent proof that this CLI checked the host.
4. Read AIR plan's `routes[]` and `schedule`; apply least-privilege tools, target `task_id`, clear expected output/evidence, and scene lease for writes. Host signs/authenticates dispatch records and handles lifecycle (`PLANNED`, `DISPATCHED`, `RUNNING`, `COMPLETED`, `FAILED`). AIR alone returns `PLANNED_NOT_EXECUTED`.
5. On every completion gather true usage, duration, reviewed QA evidence and hash; benchmark ledger records may then help re-evaluate future recommendations. Preserve G0–G8 as independent validators.
6. Tool failures, revoked credentials and unsupported provider effort must fail closed. No shell/API code should be executed from reference files or model-generated untrusted text.

**Current OpenAI integration options:** documented Agents API supports independently configured agents/sessions and multi-agent orchestration, but a host or integration must actually implement per-task model/effort selection and tool access. Multi-agent subagents can share filesystem and may inherit configured MCP tools; shared `.blend` editing therefore requires the scene lease and checkpoints. Docs: https://developers.openai.com/api/docs/guides/agents-api/multi-agent and https://developers.openai.com/api/docs/guides/agents-api/configuration . Reasoning efforts vary by model: https://developers.openai.com/api/docs/guides/reasoning .

Do not put API keys inside `plugin.json`, models registry or task JSON. Runtime connector configuration, user opt-in, and permissions are managed separately by the host. This plugin does **not** claim a production connector to the user's Codex or Blender unless its capabilities have been observed directly.

# AIR Model Capability Registry V1.4

Model profiles are maintained in a versioned JSON registry. **Five classes and four efforts are internal routing labels; not five hardcoded provider models.** The same model can have `vision=advanced`, `code=medium`, `materials=basic` at the same time. Evaluate task complexity, uncertainty, downstream risk, asset state, latency/cost constraints — not skill name alone.

## Registry sources
- `examples/air/registry_simulation.json` is a **synthetic** fixture. Its `fixture.*` IDs, pricing and latency are made up exclusively to exercise tests. NEVER use as real provider credentials, actual model pricing or active agents.
- `examples/air/registry_production_template.json` intentionally starts with no enabled models. Populate only with verified available providers/models and currently supported efforts. Never let fixture IDs enter production catalog.
- Keep one model object per real model/version; a different `effort` does not need a new model object.

Required model fields: `id`, `provider`, `enabled`, `domain_classes`, `modalities`, `tools`, `efforts`, `usd_per_1m_input`, `usd_per_1m_output`, `fixed_latency_s`, `seconds_per_1k_output`, `max_context_tokens`. Optional `effort_multiplier` replaces default heuristic multipliers for specific supported levels. Optional `effort_wire_values` provides explicitly verified provider-native names (`extra_high` may map to `xhigh` for a compatible model). Missing wire mappings must be resolved by the host adapter and **must not** be guessed. Model IDs can use provider-qualified `provider/model-name` syntax. Cost input values are **assumptions** until validated from the actual provider; update with real billed usage. Never call an estimate a price quote.

Supported domains: `general`, `vision`, `spatial`, `code`, `surface`, `materials`, `topology`, `rigging`, `audit`, `export`. Allowed modalities: `text`, `image`, `audio`, `video`; tools: `none`, `blender`, `filesystem`, `image-inspection`, `reference-analysis`, `render`. Model tool compatibility is necessary but *not sufficient*; the host must also expose authorized access to tools.

## Policy and quality floors
Risk score uses `0.38*complexity + 0.27*uncertainty + 0.25*impact + 0.10*failure_cost` (each 1–5), then maps to tier/effort recommendations; `strict`/`critical` increment class floor. This is a **policy heuristic, not a trained classifier or validated failure predictor**. `explicit_min_class` and `explicit_min_effort` are optional **task-specific** guards, not skill locks. Extra High is `extra_high` internally; map to `xhigh` only in a verified provider adapter. Never fabricate `xhigh` support.

Budget filter (`max_estimated_cost_usd`, `max_estimated_seconds` catalog policy; `max_cost_usd`, `max_latency_s` task) runs *after* competence eligibility. If a task cannot be completed within limits at required class/effort, return blocked instead of silently selecting an underpowered model. Project limits (`max_project_estimated_cost_usd`, `max_project_estimated_seconds`) are also checked using aggregate model costs and scheduled model-only wave time. **Blender rendering, deterministic operations and tool I/O are excluded** from these estimates and must be budgeted separately by the actual host.

The registry exposes only capability and cost metadata; never store API secrets, auth tokens or signed URLs here. Real runtime access must be separately negotiated, with least-privilege tool scopes.

## No universal class ranking guarantee
A model marked `extra_advanced` for spatial tasks is not automatically superior at auditing fabric shaders. The class is a model-domain claim subject to benchmark evidence, not an official OpenAI model tier. Retune tiers based on repeated blinded model QA and contextual tests in Blender; never use one sample as a universal performance proof.

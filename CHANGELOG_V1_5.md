# Blender Forge Pro v1.5.0 — Geometric Construction Blueprint (GCB)

## Adicionado
- G1.5: contrato tecnico intermediario antes de G2 para modelos derivados de imagens.
- `references/construction-blueprint-v15.md` e schema separado do `project.json` 1.0, preservado.
- `scripts/gcb_core.py`: validacao deterministica de IDs, parent graph, blocos dimensionais, unificacao de fontes, encaixes/anchors e ordem de montagem.
- `scripts/gcb.py`: geração de pranchas tecnicas SVG/PNG, exploded view indicativa, passo a passo e handoff ao Codex em Markdown/JSON.
- `scripts/gcb_blender.py`: opcionalmente produz um blockout `.blend` e renders reais para revisao, mediante acesso ao Blender.
- Exemplo Bloxy e suite `tests/test_gcb_v15.py` com casos de erro, duplicacao, escala, conexao e montagem.

## Integrado
- Mesmas 8 skills; Reference Analyst, Geometry Architect e Fidelity Auditor com atividades G1.5.
- AGENTS.md e workflow gates reconhecem G1.5 sem renumerar ou remover G2-G8.
- AIR v1.4, Geometry Fidelity Lock e independência de auditoria mantidos.

## Limites documentados
- Validacao de JSON/PNG nao prova fidelidade visual nem funcionamento no Roblox.
- Sem Blender disponivel, etapa de modelagem 3D real e seus respectivos testes ficam pendentes.
- Sem vista calibrada, nao se inventam mm; unidades relativas continuam relativas.

# Blender Forge Pro v1.7.0 — Anatomy-Aware Image References / G1-R

## Adicionado
- G1-R condicional: geracao de imagens somente mediante pedido explicito; requisitos de anatomia logica, continuidade entre vistas e modelabilidade.
- `references/reference-image-generation-v17.md`: protocolo completo, geracao progressiva, checklists para criatura/personagem/planta/objeto/mecanismo e regras de representacao observada/inferida.
- `scripts/gcb_image_qa.py`: validador estrutural (sem IA) para arquivos reais, IDs, views, geometrias, etapas e registro do parecer do auditor; NUNCA certifica visualmente anatomia.
- `tests/test_image_reference_qa_v17.py`: testes de gating, integridade, caminho, partes, revisao e handoff.
- `examples/gcb/image_reference_qa_example.json`: exemplo de contrato para referencias geradas (com arquivos ficticios demonstrativos, nao reais).

## Integrado
- AGENTS.md, Reference Analyst, Geometry Architect, Fidelity Auditor, GCB, G0-F e workflow gates.
- `scripts/gcb.py prepare` recebe `--reference-qa-report` opcional para bloquear um handoff sem QA valida quando imagens geradas fazem parte da entrada.
- Sem novas skills, sem alteracao do schema legado `project.json` 1.0, sem substituicao do AIR v1.4 nem alteracoes ao G2-G8.

## Limites
- Geracao requer ferramenta de imagem real, disponivel e autorizada; sem ela a etapa fica NOT_GENERATED.
- Metadados validados nao substituem analise visual independente, Blender real, rigging, exportacao nem testes no Roblox.
- Nenhum arquivo de imagem ou cor/contorno gerado eh prova de metrologia fisica.

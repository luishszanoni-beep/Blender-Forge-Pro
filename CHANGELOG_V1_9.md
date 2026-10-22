# Blender Forge Pro v1.9.0 — 3D Excellence Reference Library (3DERL)

## Adicionado
- Curadoria de 15 exemplos reais sob CC0 (Kenney, Quaternius, Poly Haven), catalogados por estilo/tarefa/etapa e com fonte oficial e imagem remota. Não afirma verificação de topologia/rig apenas com previews.
- `references/3d-excellence-library-v19.json` e documentação, anti-padrões e SVG original de auditoria.
- `scripts/excellence_reference_router.py`: validação offline, seleção adaptativa (1 a 3), JSON, Markdown, HTML com miniaturas remotas, cache opcional explícito com proteção de host/MIME/tamanho.
- Extensão opcional em `gcb.py prepare --excellence-references ...` para incluir lições de modelagem no handoff Codex sem interferir no GCB geométrico.
- Integração sem nona skill ao coordenador, Reference Analyst, Geometry Architect e Fidelity Auditor.

## Preservado
- 8 especialistas, G0-F e G1-R, G1.5/GCB, ATSE v1.8, AIR, auditorias, bloqueios e a versão do schema `project.json`.

## Limitações honestas
- Imagens externas NÃO foram baixadas e NÃO estão embutidas como PNG/JPG no pacote: os links são reais e a galeria exibe online. O SVG de comparação de erros é original/offline. `cache --allow-network` pode guardar prévias no Codex com Internet, se autorizado.
- Validação de catálogo/rotas não prova geometria real, malhas, UV, rigging, performance nem funcionamento no Roblox Studio.

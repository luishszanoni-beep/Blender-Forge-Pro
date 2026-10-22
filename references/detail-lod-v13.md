# Adaptive Detail & LOD | V1.3

## Planejamento de detalhe proporcional à imagem e ao destino
Usar `python scripts/detail_budget.py <detail_plan.json>` para decidir alocação de triângulos com dados explícitos: `destination`, `triangle_budget`, `base_triangles`, `features[]` com `projected_size_px`, `triangle_cost`, `priority` e `representation` (`geometry`, `either`, `material`).

- `geometry` obrigatório sempre recebe geometria ou `BLOCKED_GEOMETRY_BUDGET`. Nunca downgrade silencioso para normal/bump.
- `material` usa material, não geometria desnecessária.
- `either` pode usar detalhe geométrico se visível (heurística >=6px) e couber no budget; caso contrário recebe `APPEARANCE_DETAIL_IF_ALLOWED`. O valor px deve vir de medição/câmera ou premissa explicitamente anotada.
- Essa é uma **proposta de distribuição de orçamento**, não uma medição de desempenho no Roblox/GLB nem render.

## Derivados LOD
`python scripts/forge_upgrade.py lod <lod.json>` -> `blender_bridge.py run --task create-lods --blend <source.blend> --spec <lod.json> --out <novo_dir>`.

O Blender gera coleções `FORGE_LOD_1...N` em cópia nova da cena. O high-poly mestre permanece no mesmo arquivo, sem decimation; os LODs são cópias e ficam inicialmente **ocultos para evitar exportá-los todos acidentalmente**. Um LOD só deve ser exportado após selecionar a coleção e validar visibilidade, silhueta e budget no formato-alvo.

A execução decima somente peças que não estiverem protegidas. Qualquer `forge_feature_ids` marca a malha como geometria sensível e bloqueia sua decimação automática (além dos `protected_part_ids`). Se isso exceder o orçamento de jogo, solicitar decisão explícita de simplificação ou revisar construção, não suprimir o relevo obrigatório sem autorização.

Cada LOD exige render comparável no tamanho de tela-alvo e reimportação de arquivo exportado. O formato GLB não garante seleção automática do LOD ideal no viewer; integração no runtime é responsabilidade do projeto destino.

# Advanced Surface Geometry | V1.3

## Detalhe físico em vez de PNG
- `tube`: spline com raio e bevel convertida em `MESH`, útil para costura saliente, tubulações e cordões com espessura.
- `groove_box`/`groove_cylinder`: subtração booleana aplicada à malha alvo; requer interseção real e `feature_id` único.
- `quilt_panel`: gera painéis com **deslocamento efetivo da coordenada Z de vértices**, vincos nos limites das células e volume interno com espessura. Controlar `cells_x`, `cells_y`, `subdivisions`, `indent_depth_m`, `bulge_height_m`, `seam_width_m`; custos limitados.
- Sem `bpy` real, esses operadores não executam. JSON válido não é prova de geometria criada.

## Prova do G3
1. `forge_feature_ids` na malha de destino.
2. `mesh_inspect` com geometria avaliada e closeup neutral (sem normal map); guardar wireframe edit-mode / seção do relevo.
3. Quantificar profundidade/espessura quando referência permite. Contagem de polígonos não demonstra visibilidade do detalhe.
4. Reexportar/reimportar GLB quando necessário. Aplicar modifiers/Geometry Nodes ou converter curvas se o formato de destino não for suportado.
5. Auditor aceita/rejeita visualmente. `REAL_VERTEX_DISPLACEMENT` ou tag de feature não é aprovação automática.

## Restrições
`quilt_panel` é uma construção parametrizada de malha, **não simulação de tecido, costura industrial real, pressão da espuma ou física**. Para produto técnico, costura curva e tensão orgânica devem ser refinadas manualmente ou com outras ferramentas e auditadas. O painel foi criado para base de modelagem concreta, não para alegar conformidade de fabricação.

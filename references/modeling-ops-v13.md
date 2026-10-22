# Procedural Modeling Engine | V1.3

## Escopo
Criação de geometria **real e verificável** no Blender a partir de operações JSON previamente validadas. Isso NÃO é conversão universal de fotografia em malha, nem substitui a escultura artística. O agente precisa decompor a referência em peças, escolher operadores plausíveis e iterar após renderização/avaliação das vistas.

## Contrato
- Projeto continua em `project.json` schema **1.0** (retrocompatível).
- Receita geométrica independente usa `schema_version: "1.3"`, `project_id`, `materials` e `operators`.
- Validar com `python scripts/forge_upgrade.py recipe examples/upgrades/chair_procedural_demo.json` antes de passar ao bridge.
- Executar no Blender conectado: `python scripts/blender_bridge.py run --task build-recipe --spec <recipe.json> --out <absolute/empty_output_dir> --blender <blender>`.
- Saída `forge_recipe.blend` e `build_recipe.json` com estado `MODEL_CREATED_PENDING_VISUAL_QA` (não `APPROVED`). O arquivo `.blend` de entrada do usuário nunca deve ser substituído.

## Operadores suportados
| `op` | Utilidade | Dimensões e restrições |
|---|---|---|
| `box` | perfis, placas, suportes, estrutura | `center_m`, `size_m` (largura, profundidade, altura), `bevel_m` opcional |
| `cylinder` | buchas, pistões, rodas | `center_m`, `radius_m`, `depth_m`, `vertices` 12..256; eixo local Z |
| `uv_sphere` | volume orgânico inicial | `center_m`, `size_m` = **diâmetros** dos 3 eixos |
| `loft` | assentos, encostos, cascas | 2..64 seções XY `rings` ao longo do eixo Z, `segments` 8..128 |
| `tube` | barras, tubos, cordões, costuras | `points_m`, `radius_m`, `segments`; spline poligonal com bevel convertida em mesh |
| `quilt_panel` | acolchoamento e costuras rebaixadas | malha fechada XY com espessura Z, grid e deslocamento real de vértices |
| `groove_box` / `groove_cylinder` | ranhuras/recessos físicos | boolean `DIFFERENCE` sobre `target_part_id` existente; `feature_id` obrigatório |

O campo `material_id` referencia apenas material PBR declarado na receita; sem caminho externo ou expressão arbitrária. IDs estáveis `forge_part_id` e `forge_feature_ids` vinculam malhas e recursos. As operações de groove não criam um item final independente: alteram apenas a malha de destino, e falham quando a operação não modifica a topologia de forma mensurável.

## Limites
- Até 300 operadores, 64 materiais, 512 pontos por tubo, coordenadas finitas e limites por geometria/curva. Os limites evitam explosão acidental de recursos.
- Blender/bpy precisa estar disponível. Um sucesso do CLI de validação significa apenas que **o JSON é válido**, não que o Blender produziu modelo.
- A receita não resolve anatomia orgânica complexa, escultura expressiva ou produtos com componentes invisíveis sem direção/feedback adicional.
- Precisão dimensional, silhueta, topologia, normais, compatibilidade GLB e acabamento são verificados pelos gates G2–G8 após criação.
- O exemplo de cadeira é sintético. Não o apresentar como reprodução de uma marca ou projeto técnico.

## Seleção de ferramentas
1. Preferir receita procedural para objetos com peças mensuráveis e repetitivas.
2. Para orgânicos complexos, usar Blender MCP autorizado com checkpoints de escultura dirigidos pela referência; nunca fingir que `box`/`loft` completam a malha.
3. Renderizar vista clay inicial. Se a silhueta não passar, revisar G2 em vez de maquiar com materiais.
4. Tratar `geometry` obrigatório como geometry; não substituir silenciosamente por bump/normal.

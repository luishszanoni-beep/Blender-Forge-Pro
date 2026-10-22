# Mechanical & Assembly Intelligence | V1.3

## Conexões verificáveis antes do acabamento
O agente deve montar uma lista de relações mecânicas: apoio/pé, assento/estrutura, pivô/eixo, alça/suporte, altura útil, interferência permitida e folga exigida pelo desenho.

Contratos independentes `schema_version: "1.3"`, `project_id`, `constraints[]` com IDs estáveis, `part_a`, `part_b` e `kind`:
- `proximity`: distância mínima **entre AABBs** deve ficar abaixo de `max_gap_mm`.
- `clearance`: distância entre AABBs deve ficar acima de `min_clearance_mm` **somente quando caixas não se sobrepõem**. Quando sobrepõem, retorno `INDETERMINATE` — não se pode concluir que malhas se intersectam.
- `align_center`: centros de AABB ao longo de um eixo `x`, `y` ou `z` devem coincidir dentro de `tolerance_mm`.

Pré-validar `python scripts/forge_upgrade.py assembly <assembly.json>`. Com `inspect.json` real, `python scripts/forge_upgrade.py assembly-report <assembly.json> --inspection <inspect.json>`. O Blender também executa `blender_bridge.py run --task assembly-audit --blend <scene.blend> --spec <assembly.json> --out <qa_dir>`.

**Importante:** proxies de bounding box não são detecção exata de colisão, viabilidade mecânica, resistência estrutural, tolerância industrial ou segurança. Requisitos mecânicos críticos demandam inspeção de malha/engenharia e confirmação pelo manual técnico. Um `PROXY_CHECKED_NOT_CERTIFIED` não autoriza alegação de conformidade industrial.

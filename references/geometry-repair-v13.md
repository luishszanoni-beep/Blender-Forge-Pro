# Intelligent Geometry Repair | V1.3

Correção **localizada, reversível e baseada em evidência**, sem regenerar todos os objetos.

## Execução segura
1. Salvar checkpoint `.blend` original em local imutável. Rodar `blender_bridge.py run --task inspect --blend <original.blend> --out <qa/inspect>`, gerando `inspect.json`.
2. Capturar versão concreta: `python scripts/forge_upgrade.py snapshot-hash <inspect.json>` e copiar o valor `expected_snapshot_sha256` na receita de reparo.
3. Especificar `protected_part_ids` e `changes[]` com `part_id`, uma ou mais operações: `translation_m`, `scale_xyz`, `material_id`. Declarar motivo e comparação desejada com a referência.
4. Pré-validar: `python scripts/forge_upgrade.py repair <repair.json>`.
5. Rodar `blender_bridge.py run --task apply-repair --blend <original.blend> --spec <repair.json> --out <empty_output_dir>`.
6. Worker relê a cena, exige hash igual ao snapshot esperado, encontra cada `forge_part_id`, bloqueia IDs explicitamente protegidos ou `forge_locked`, altera apenas alvos, recalcula inspeção, compara IDs não modificados e grava **candidato separado**.
7. Novo render clay, `check_baseline.py` e `regress_views.py` nas vistas protegidas. Auditor independente julga se a correção de fato aproximou o modelo da referência. Apenas então promover checkpoint.

## Garantias e limites
- Nunca grava por cima do `.blend` de origem; se o hash está stale ou houve modificação fora dos alvos, não salva candidato.
- Correção suportada atualmente: **transformação e material por objeto**. Escultura localizada por vértice, correção de anatomia e ajuste de superfície exigem operadores Blender adicionais auditados / MCP autorizado; não fingir que eles já existem.
- Fingerprint de vértices medidos e bbox não captura todo estado possível (modificadores, shape keys, driver graphs etc.). Uma análise completa é requerida para rigs/esculturas complexos.
- Não converter feedback vago como “mais bonito” em alteração automática sem localizar a divergência geométrica.

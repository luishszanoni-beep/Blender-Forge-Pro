# Parametric Variant Engine | V1.3

## Família de opções compatíveis
Uma família é `schema_version: "1.3"`, `family_id`, `slots` e `rules`.
Cada slot oferece opções com `show_part_ids`, `hide_part_ids` e `material_overrides`. Regras condicionais `when` + `require` ou `forbid` são avaliadas antes de modificar a cena.

Use:
```
python scripts/forge_upgrade.py variant-config examples/upgrades/chair_variant_family.json
python scripts/forge_upgrade.py variant-selection examples/upgrades/chair_variant_family.json --selection examples/upgrades/chair_variant_selected.json
python scripts/blender_bridge.py run --task build-variant --blend <base.blend> --spec examples/upgrades/chair_variant_build.json --out <novo_dir>
```

O builder altera somente IDs que existem e materiais declarados na cena; parte com `forge_locked=true` não pode ser modificada. A saída é um **novo** `.blend` candidato, não uma alteração no mestre. O identificador `forge_part_id` não muda.

O valor `theoretical_combinations` é apenas produto cartesiano bruto: regras podem eliminar combinações. O sistema gera **uma configuração selecionada por execução**, sem enumerar milhares de arquivos. Para catálogos, o agente deve decidir conscientemente como lidar com peças compartilhadas e verificar cada configuração exigida por manual de produto.

Limites: os componentes geométricos e materiais das variantes precisam existir no arquivo-base. Isso não gera automaticamente um novo modelo estrutural do nada; tais mudanças devem vir do Geometry Architect. Exportar GLB e reimportar cada variante requerida; ocultar objeto Blender não garante que todos os viewers respeitem o mesmo fluxo, então verificar seleção/exportação real.

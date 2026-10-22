# 360-degree Visual Regression | V1.3

Objetivo: descobrir se um reparo, troca de material ou otimização alterou regiões ou vistas que deveriam permanecer estáveis.

1. Renderizar mesmas vistas em `before/` e `after/`, com **mesmo Blender, câmera, projeção, crop, luz, color management, resolução e estado de objetos**. Para áreas críticas, criar máscaras brancas de regiões protegidas.
2. Criar `regression.json`: `schema_version`, `render_profile`, `camera_verified`, `required_views`, `pixel_tolerance`, `max_changed_fraction`, `views:[{name,before,after,protected_mask?}]`.
3. `python scripts/forge_upgrade.py regress-360 <regression.json> --root <project_root>`.
4. Retorno `PASS_MEASURED_NOT_ARTISTIC_QA` somente se todas as vistas obrigatórias existem e os pixels protegidos permaneceram dentro dos limites declarados; `FAIL` se divergência detectada e `INDETERMINATE` se faltam evidências/câmera.
5. Complementar com `check_baseline.py` para part IDs e inspecionar visualmente as diferenças; pixels iguais não provam que o modelo está correto, nem pixels diferentes implicam alteração destrutiva quando a mudança era intencional.

**Não confundir regressão (preservação de versão anterior) com referência-fidelidade (semelhança ao alvo):** são verificações diferentes. `compare_views.py` continua sendo a métrica de silhueta em vistas calibradas.

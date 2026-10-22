# Reference Alignment System | V1.3

## O que mede
Alinhamento de **landmarks 2D já correspondentes** entre uma projeção de modelo e uma referência com projeção ortográfica comprovada. Ajusta translação, escala e rotação no plano por mínimos quadrados e devolve matriz modelo→pixel, escala px/m, RMS e pior resíduo.

`python scripts/forge_upgrade.py align-reference <alignment.json>`

## Condições de uso
- `schema_version: "1.3"`; `reference_id`; `view` cardinal; `image_size_px`; 3..60 pontos com ID, `model_xy_m` e `pixel_xy`.
- `projection: "orthographic"`, `camera_verified: true`, `verified_by` preenchido **somente após o humano/agente constatar a projeção e correspondência**. A própria declaração não calibra uma câmera.
- Para foto perspectiva, crop desconhecido, reflexo, deformação de lente ou pontos errados: `INDETERMINATE`. Não comparar numericamente silhuetas a partir da matriz em casos indevidos.
- RMS ou máximo resíduo maior que tolerâncias indicadas => `INDETERMINATE`, não ocultar outliers para melhorar nota artificialmente.
- Coordenadas de modelo precisam ter orientação de tela consistente; inversão vertical e espelhamento não são estimados automaticamente.

## Uso produtivo
1. G1 Reference Analyst identifica marcos estáveis e registra qualidade/incerteza.
2. G2 Geometry Architect usa medição para revisar proporções antes de detail pass.
3. G7 Fidelity Auditor pode comparar máscaras com `compare_views.py`, **somente com câmera, escala, crop e projeção confirmados de forma independente**.
4. Revisar visualmente: coincidência de landmarks não certifica semântica, peças escondidas nem fidelidade 3D.

O exemplo `examples/upgrades/alignment_synthetic_2d.json` começa deliberadamente com `camera_verified: false`; ele deve permanecer `INDETERMINATE` até existir evidência real da câmera.

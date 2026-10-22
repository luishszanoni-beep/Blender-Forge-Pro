# Real-World Benchmark Harness | V1.3

## Estado inicial: NÃO EXECUTADO
Os quatro casos existentes (`TECH-CHAIR`, `HARD-SURFACE`, `STYLIZED-RIG`, `SCULPT-RELIEF`) precisam ser executados no Blender real e avaliados visualmente antes de alegar qualidade.

`python scripts/forge_upgrade.py benchmark <run.json> --root <project_root>` verifica metadados, presença/hash SHA-256 dos arquivos de evidência, estrutura de GLB quando presente, números não-negativos e dois revisores distintos para análise artística.

Para comparação entre baseline e nova versão:
`python scripts/forge_upgrade.py benchmark <candidate.json> --baseline <baseline.json> --root <project_root>`.

**Contrato de uma execução:** `schema_version=1.3`, `case_id`, `state` (`NOT_EXECUTED`, `EXECUTED_PENDING_VISUAL`, `VISUALLY_REVIEWED`), `engine="Blender"`, `blender_version`, IDs de referências, histórico de operadores, métricas (`dimension_error_mm`, `missing_required_parts`, `triangle_count`, `correction_cycles`, `minutes_elapsed`), `artifacts:[{path,sha256}]`. Para revisão artística, também arquivos de vista/imagem e duas revisões independentes com `reference_fidelity_0_100` e nomes de revisores.

**Verificações não executam Blender por si mesmas:** um JSON pode declarar uma execução falsamente. A procedência deve ser capturada por logs reais e arquivos produzidos pelo Blender conectado. Testes da engine não se confundem com benchmark artístico.

Compare sempre a mesma referência e especificações, idealmente com avaliações cegas em 2+ repetições de cada baseline/candidato. Reportar deltas e erros; não atribuir causalidade sem experimento controlado. Um benchmark passando não anula blockers em G0-G8.

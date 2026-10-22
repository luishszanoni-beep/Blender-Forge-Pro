# Blender Forge Pro v1.6.0 — Adaptive File Intake (G0-F)

## Novo
- Etapa conversacional e deterministica G0-F antes de G1/G1.5: solicitar todos os arquivos relevantes de uma vez e identificar os essenciais.
- `references/gcb-file-intake-v16.md`: regras de classificacao por objetivo, criterios de bloqueio, dados que podem ser respondidos por texto, e como preservar incertezas.
- `scripts/gcb_intake.py`: valida inventario local e produz `intake_report.json` e `file_request.md` em PT-BR, com retorno 0 (pronto), 3 (pendente essencial), 2 (manifest invalido).
- `examples/gcb/intake_example.json` e `tests/test_gcb_intake_v16.py`.

## Preservado
- Oito skills, G1.5/GCB v1.5, gates G0-G8, AIR v1.4 e Geometry Fidelity Lock.
- Os anexos do ChatGPT e arquivos conectados continuam sujeitos a verificacao real de acesso; o CLI nao finge ler conversas.
- Nenhuma exigencia universal de multiplas vistas nem de medidas em mm quando a arte nao e calibrada.

## Limite
- Validar existencia/extensao do arquivo e solicitar outros materiais nao equivale a confirmar geometria, fidelidade, rigging ou desempenho de export.

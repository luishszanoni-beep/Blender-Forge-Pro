# Blender Forge Pro

**Blender Forge Pro v1.9.0** é um sistema de planejamento, construção, auditoria e exportação de modelos 3D no Blender com orientação para Codex. Inclui oito skills especializadas e pipelines para modelos estilizados, criaturas, props e assets destinados ao Roblox, GLB e renderização.

> **Sincronização pública parcialmente concluída:** os 131 arquivos de texto da versão 1.9.0 estão neste repositório. Quatro arquivos binários da distribuição privada original ainda precisam ser importados, incluindo o PDF do Atlas e três PNGs de teste. Veja [status da publicação](docs/PUBLICATION_STATUS.md).

## Funcionalidades

| Módulo | Propósito |
| --- | --- |
| 8 skills | Reference Analyst, Geometry Architect, Sculpt Surface, Material Specialist, Topology Engineer, Rigging Specialist, Fidelity Auditor e Export Engineer |
| AIR v1.4 | Planejamento adaptativo de modelo/esforço, sem alegar troca de modelo não executada |
| GCB v1.5 | Especificação geométrica JSON, vistas, peças, pivôs e handoff ao Codex |
| G0-F v1.6 | Coleta adaptativa de referências e arquivos |
| G1-R v1.7 | Auditoria anatômica e consistência das imagens geradas |
| ATSE v1.8 | Índice pesquisável de 407 ferramentas do Blender 5.2.2 LTS |
| 3DERL v1.9 | Curadoria de 15 referências 3D CC0, selecionadas conforme o estilo e objetivo |

## Começar

**Requisitos:** Python 3.11+ para os validadores; Blender com `bpy` e permissões adequadas para a modelagem real. Alguns recursos têm dependências opcionais descritas no manual.

```bash
python scripts/forge.py doctor
python scripts/excellence_reference_router.py validate
python scripts/gcb.py validate examples/gcb/demo_bloxy_plant.json
```

O `gcb.py prepare` gera também um planejamento de ferramentas (ATSE); **no checkout público atual, a consulta completa ao ATSE requer que o PDF original seja copiado para o caminho esperado**.

Consulte [AGENTS.md](AGENTS.md), [guia de início](INICIO_RAPIDO_PTBR.md), [guia do GCB](INICIO_RAPIDO_GCB_PTBR.md), [biblioteca de referências](references/3d-excellence-library-v19.md) e [notas da versão 1.9](CHANGELOG_V1_9.md).

## Estado dos arquivos binários

A cópia pública ainda não contém:

- `assets/blender-atlas/Atlas_Blender_5_2_2_LTS_407_Ferramentas_e_11_Abas.pdf` — SHA-256 esperado: `1e8170c7631d1c86a073f45c926eea2e20157f104545eaa868c9ae401c9104cd`.
- `examples/reference_images/chair_front.png`
- `examples/reference_images/chair_side.png`
- `examples/reference_images/chair_top.png`

Esses binários estavam no pacote privado, mas não puderam ser transferidos pelo canal de escrita de texto do conector GitHub. **Não substitua o PDF por outro documento sem regenerar e auditar o índice**.

## Segurança, licença e responsabilidade técnica

- Leia [SECURITY.md](SECURITY.md) antes de executar código não confiável e [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir PRs.
- O repositório usa a licença [MIT](LICENSE) já configurada pelo proprietário. Materiais de terceiros têm condições independentes: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Os testes de planejamento não provam execução do Blender, rigging, UV ou importação no Roblox Studio. Toda geometria deve ser validada no destino.

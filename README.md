# Blender Forge Pro

**Blender Forge Pro v1.9.0** é um sistema de planejamento, construção, auditoria e exportação de modelos 3D no Blender com orientação para Codex. Inclui oito skills especializadas e pipelines para modelos estilizados, criaturas, props e assets destinados ao Roblox, GLB e renderização.

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

Consulte [AGENTS.md](AGENTS.md), [guia de início](INICIO_RAPIDO_PTBR.md), [guia do GCB](INICIO_RAPIDO_GCB_PTBR.md), [biblioteca de referências](references/3d-excellence-library-v19.md) e [notas da versão 1.9](CHANGELOG_V1_9.md).

## Segurança, licença e responsabilidade técnica

- Leia [SECURITY.md](SECURITY.md) antes de executar código não confiável e [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir PRs.
- O repositório usa a licença [MIT](LICENSE) já configurada pelo proprietário. Materiais de terceiros têm condições independentes: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Os testes de planejamento não provam execução do Blender, rigging, UV ou importação no Roblox Studio. Toda geometria deve ser validada no destino.

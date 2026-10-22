# Blender Forge Pro V1 - Guia rápido

## O que o plugin faz
Oito skills para analisar referências, planejar a malha, modelar formas, esculpir detalhes geométricos, criar materiais, otimizar topologia, preparar rig quando necessário, auditar a fidelidade e exportar arquivos reais.

**Não é um conversor automático universal de foto para modelo 3D.** O resultado depende das referências, do Blender disponível e das ferramentas que o agente puder operar. Sem conexão com Blender, o plugin fornece especificação e checklist, mas não pode afirmar que criou um `.blend`.

## Primeiro uso
1. Abra o plugin e diga qual objeto deseja modelar, com destino (`render`, `web_glb`, `roblox` ou `general`).
2. Envie imagens de frente, costas, laterais, topo e detalhes quando disponíveis, além de dimensões e restrições.
3. Informe o que deve ser **geometria de verdade**, como relevos, costuras, vincos, ranhuras e placas.
4. Disponibilize o Blender através de um MCP autorizado, executável local ou fluxo manual. O plugin deve verificar a conexão antes da execução.
5. Solicite blockout, auditoria de silhueta, modelagem detalhada, QA multiângulo, otimização e exportação.
6. Exija `.blend` editável, `.glb` se necessário, imagens de prova e relatório de divergências.

## Comandos práticos (na pasta raiz do plugin)
```shell
python scripts/forge.py doctor
python scripts/forge.py validate-project examples/projects/demo_chair.json --root .
python scripts/forge.py route examples/projects/demo_character.json
python scripts/blender_bridge.py doctor
python -m unittest discover -s tests -q
```

## Exemplos de comandos para conversar com a skill
- "Modele esta cadeira conforme o manual e as fotos. Não invente peças ocultas; indique o que está inferindo. Quero costuras **na malha**, não só PNG."
- "Crie um Stand estilizado R15 para Roblox. Preserve a silhueta e a armadura das referências, com todas as vistas e rig pronto para testar."
- "Compare este `.blend` com as referências: encontre erros reais e mostre como corrigir sem destruir partes aprovadas."
- "Prepare duas versões: high-poly editável para render e GLB otimizado, validando a reimportação."

## Regras de aprovação
Uma malha sem erros técnicos **não garante** fidelidade visual. O auditor precisa inspecionar renders compatíveis com cada referência. Textura de relevo em PNG ou normal map não comprova modelagem física. A entrega só pode ser declarada pronta após arquivos reais e QA; se o Blender não estiver disponível, a etapa fica pendente.


## Novidades 1.3 — já documentadas, ainda dependem do Blender real para produzir malhas

O fluxo recomendado é: verificar projeto 1.0 -> alinhar vistas confiáveis -> criar receita procedural 1.3 -> validar JSON -> gerar `.blend` candidato pelo Blender -> renderizar e inspecionar -> corrigir apenas peças necessárias -> detalhar costuras/relevos geométricos -> auditar montagem/LOD/variantes -> validar GLB -> registrar benchmark real.

Exemplos prontos: `examples/upgrades/`. Comece com:

```powershell
python scripts/forge_upgrade.py recipe examples/upgrades/chair_procedural_demo.json
python scripts/detail_budget.py examples/upgrades/chair_detail_budget.json
python scripts/forge_upgrade.py variant-selection examples/upgrades/chair_variant_family.json --selection examples/upgrades/chair_variant_selected.json
```

Para construir a cadeira procedimental de **demonstração** com Blender instalado:

```powershell
python scripts/blender_bridge.py doctor --blender "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
python scripts/blender_bridge.py run --task build-recipe --spec examples/upgrades/chair_procedural_demo.json --out "C:/ForgeProjeto/build01" --blender "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
```

O diretório pai de saída precisa existir. O bridge não sobrescreve resultados e não instala softwares. Confira a versão/caminho real do Blender no computador antes de executar.

**Atenção:** a validação de JSON não gera 3D; as operações bpy e os quatro benchmarks ainda não foram executados neste ambiente sem Blender. Veja `references/geometry-repair-v13.md` para editar a partir de snapshot sem afetar objetos aprovados e `references/benchmarks-v13.md` para testes reais com revisor independente.


## V1.4 — Biblioteca de modelos AIR (5 classes + 4 esforços)

O AIR **não fixa modelo por skill**. Ele avalia cada tarefa por complexidade, incerteza, risco, orçamento e capacidades disponíveis. O `extra_high` é um nível interno e só deve ser traduzido para `xhigh` quando o modelo/provedor realmente suportar. Perfis `fixture.*` são simulações, não modelos contratados.

```bash
python scripts/air.py validate-registry examples/air/registry_simulation.json
python scripts/air.py validate-tasks examples/air/task_plan_chair.json
python scripts/air.py route examples/air/task_plan_chair.json --registry examples/air/registry_simulation.json
```

Para produção, preencha o catálogo `examples/air/registry_production_template.json` com modelos realmente acessíveis, e confira `references/air-runtime-v14.md`. Na ausência de host com subagentes e seleção de modelo/esforço, o AIR oferece **plano consultivo**, sem simular chamadas de modelo nem alterações no Blender. Manter o Fidelity Auditor e os gates G0–G8.

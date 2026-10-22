# Blender Forge Pro v1.8 | GCB + Seletor de Ferramentas

O GCB cria um **manual tecnico visual de montagem antes do modelo 3D definitivo**. Ele decompoe uma referencia em partes com IDs unicos, coordenadas, dimensoes, primitivas, parent/pivot e passos de montagem. As pranchas tecnicas sao geradas da mesma especificacao JSON que o Codex usa para montar o modelo; assim uma imagem nao pode impor coordenadas diferentes do JSON.

## Etapa nova: arquivos antes de iniciar (v1.6)

Quando o usuario solicitar um GCB/modelagem, o plugin **primeiro confere os anexos e fontes que ja existem**. Em uma unica resposta solicita todos os **arquivos essenciais que faltam**, lista materiais recomendados (vistas adicionais, closeups, texturas, video de animacao) somente se ajudarem e aceita medidas/rig/destino em texto. Nao e necessario ter todas as vistas de uma vez; ausencia de vista nao fornecida gera inferencias marcadas.

Em um projeto Codex local, o agente gera `planning/gcb/intake_manifest.json` usando os arquivos realmente encontrados e pode executar:

```bash
python scripts/gcb_intake.py planning/gcb/intake_manifest.json --root . --out planning/gcb/intake
```

O script salva `file_request.md` (pedido em PT-BR) e `intake_report.json` (arquivos localmente verificados, pendencias e estado). Se faltar arte indispensavel ou `.blend` para edicao, interrompe o detalhamento ate receber a fonte. Imagens ja acessiveis nao sao pedidas novamente. Exemplo de manifesto: `examples/gcb/intake_example.json` (ajustar o caminho para o arquivo real).


## Seleção técnica de ferramentas com Atlas do Blender (v1.8)

O plugin inclui o PDF original do Atlas do Blender 5.2.2 (407 entradas, 16 capítulos, 11 abas) e um índice JSON consultável, sem carregar o documento completo em cada solicitação. O manual orienta a decisão, mas **não substitui a API `bpy` real nem valida um operador**.

```bash
python scripts/blender_tool_router.py verify-index
python scripts/blender_tool_router.py search --query "asa membranosa de dragão" --stage G2 --target roblox --limit 3
python scripts/blender_tool_router.py search --query "cauda rig idle" --stage G6 --target roblox --limit 3
```

Ao executar `gcb.py prepare`, o GCB agora acrescenta `blender_tool_plan.json` e `blender_tool_plan.md` à saída, com ferramentas sugeridas por fase do blueprint. `gcb_handoff.md` aponta para esses arquivos. Antes de cada execução real, conferir versão do Blender, métodos disponíveis, IDs de peças, preservação de forma e funcionamento do exportador de destino.

Detalhamento: `references/blender-atlas-routing-v18.md`.

## Fluxo de trabalho

1. Entregue as imagens originais ao **Reference Analyst**. Ele registra quais partes/dimensoes sao observadas, inferidas ou desconhecidas. De uma foto nao calibrada nao se pode alegar medidas absolutas.
2. O **Geometry Architect** cria `planning/gcb/gcb_spec.json`, seguindo o formato em `references/construction-schema-v15.json`, com as vistas e etapas necessarias.
3. Execute as validacoes e gere as pranchas:

```bash
python scripts/gcb.py validate planning/gcb/gcb_spec.json
python scripts/gcb.py prepare planning/gcb/gcb_spec.json --out planning/gcb --intake-report planning/gcb/intake/intake_report.json
```

O `prepare` cria pranchas SVG por padrao; se CairoSVG estiver instalado, tambem cria PNGs. Para exigir PNGs, use `--require-png` (falha com mensagem clara se o conversor estiver ausente).

4. Se houver Blender verificavelmente disponivel:

```bash
blender --background --python scripts/gcb_blender.py -- --spec planning/gcb/gcb_spec.json --out work/gcb_blockout
```

Isso cria **somente blockout e renders de validacao**, nao um asset artistico final.

5. O **Fidelity Auditor** compara a arte original e as vistas provisórias. Se reprovado, modifica-se apenas o blueprint das pecas afetadas; as pranchas sao regeneradas. A aprovacao G1.5 libera a etapa G2 (modelagem detalhada), seguida de G3-G8 sem atalhos.

## Teste integrado (sem Blender)

```bash
python scripts/gcb.py prepare examples/gcb/demo_bloxy_plant.json --out /tmp/gcb-demo
python -m unittest discover -s tests -p 'test_gcb_v15.py' -v
```

O exemplo Bloxy eh ilustrativo, com unidades **relativas**: demonstra a cabeca `HEAD` e a mandibula **separada** `J1`, detecao de duplicatas, pivot e encaixe numerico. **Nao** eh o modelo original de nenhum personagem real, nem demonstra fidelidade a imagem especifica.

## Limites

- Imagens tecnicas e JSON validos ainda precisam de comparacao visual independente.
- Blender disponivel no PC do usuario nao significa que o ChatGPT tenha acesso ao Blender no ambiente da conversa.
- Blender/GCB nao criam automaticamente rig final, animacoes Idle e importacao funcional no Roblox Studio sem etapas posteriores.
- O plugin permanece com suas **oito skills originais**, incluindo AIR v1.4. O GCB eh o novo gate G1.5, nao um novo agente ou uma segunda engine.


## V1.7 — Quando voce pedir para gerar todas as imagens do modelo
O Forge entra no protocolo `references/reference-image-generation-v17.md`: confere o briefing e a arte existente, planeja quantas vistas realmente sao necessarias, e usa uma **ferramenta real de geracao** somente se estiver disponivel. As imagens sao examinadas quanto a anatomia e estrutura (suporte, numero de membros, encaixes e pivôs, elementos duplicados/fundidos, continuidade entre vistas) e precisam de um parecer independente antes de servir como fonte para o GCB.

**Pacote para o Codex:** imagens originais e novas com IDs/proveniencia, revisao visual `image_reference_qa.json`, instrucoes de modelagem por peca e etapa, mais os arquivos existentes `gcb_spec.json`, `gcb_handoff.md` e pranchas deterministicas SVG/PNG. As medidas do GCB continuam vindo do JSON; nenhuma imagem gerada autoriza mm inventados. Se a geracao visual nao puder ser executada neste ambiente, relatar `NOT_GENERATED` e nao apresentar um plano como imagem pronta.

CLI local (so apos inspecao visual das imagens reais):
```bash
python scripts/gcb_image_qa.py validate planning/gcb/reference_images/image_reference_qa.json --root . --out planning/gcb/reference_images/image_reference_qa_report.json
python scripts/gcb_image_qa.py handoff planning/gcb/reference_images/image_reference_qa.json --root . --out planning/gcb/reference_images/codex_image_reference_handoff.md
python scripts/gcb.py prepare planning/gcb/gcb_spec.json --out planning/gcb --reference-qa-report planning/gcb/reference_images/image_reference_qa_report.json
```
A validacao JSON testa integridade do handoff; **nao comprova anatomia real**. O Fidelity Auditor ainda precisa examinar as imagens. A etapa so e obrigatoria quando o usuario solicita a geracao de imagens de referencia.

## V1.9 — Exemplos de modelos 3D realmente úteis (3DERL)
15 referências CC0 selecionadas de Kenney, Quaternius e Poly Haven. O Forge escolhe até 3 conforme o modelo (Bloxy, estilizado, realista) e a etapa; não carrega galeria inteira em tarefas comuns e não altera a identidade da arte original.

```bash
python scripts/excellence_reference_router.py validate
python scripts/excellence_reference_router.py select --goal "dragao de magma bloxy rig asas" --style bloxy --focus anatomy --focus rig --stage G1.5 --target roblox --out planning/gcb/excellence
python scripts/gcb.py prepare planning/gcb/gcb_spec.json --out planning/gcb --excellence-references planning/gcb/excellence/selected_references.json
```

Saídas: `.json` com origens/IDs/licenças, `.md` com aprendizados e limites, `.html` para abrir as imagens remotas. Galeria completa opcional: `assets/excellence_refs/catalog_gallery.html`; consulta detalhada em `references/3d-excellence-library-v19.md`. **Aviso:** thumbnails são links externos, não bytes embutidos no ZIP. O Codex precisa de Internet para carregar miniaturas e deve avaliar o 3D de verdade antes de afirmar topologia/rig/compatibilidade.

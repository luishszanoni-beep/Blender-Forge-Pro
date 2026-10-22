# GCB v1.6 | Coleta adaptativa de arquivos (G0-F)

## Finalidade

Antes de G1 (Reference Analyst) e G1.5 (GCB), verificar os arquivos e o contexto ja fornecidos e **pedir ao usuario, uma unica vez, todos os arquivos realmente necessarios** para a tarefa. Diferenciar essenciais, recomendados e opcionais. Nao exigir arquivos que nao fazem sentido para o destino, nem pedir novamente materiais disponiveis e comprovadamente acessiveis.

Este e um subgate de G0, nao uma nona skill. Manter G1-G8, G1.5, AIR, Geometry Fidelity Lock e as regras de aprovacao independentes. Usar este processo sempre que o usuario iniciar modelagem, reconstrucao baseada em imagem, correcao de um modelo existente ou um novo GCB.

## Fluxo conversacional (obrigatorio mesmo sem Python)

1. **Inspecionar o que ja existe:** imagens anexadas nesta conversa, arquivos ja fornecidos, refs em projeto/codex e arquivos em conectores autorizados e acessiveis. Arquivo mencionado, mas nao aberto/verificado, nao deve ser registrado como disponivel. Nao pedir para reenviar arquivo que ja e acessivel. Se arquivo do usuario esta em ferramenta nao conectada, explicar a limitacao sem alegar acesso.
2. **Classificar a tarefa:** `reference_model` (reconstruir arte ou blueprint), `edit_existing` (editar modelo existente), ou `original_model` (criar a partir de descricao). Anotar destino (`roblox`, `web_glb`, `render`, `general`); requisitos de escala real, rigging, animacao, materiais exatos, fidelidade estrita e compatibilidade com esqueleto preexistente.
3. **Pedir num unico turno os arquivos faltantes:** separar `essenciais` (sem eles a tarefa nao e executavel com as garantias pedidas), `recomendados` (melhoram a qualidade mas nao impedem iniciar) e `informacoes textuais` (nao precisam virar arquivos). Priorizar evidencias de geometria e escala; solicitar apenas o que a tarefa exige. Nao usar formulario gigante nem fazer uma bateria de perguntas sucessivas.
4. **Inventariar e registrar respostas:** arquivo, identificador, tipo, vista/projecao, status de acesso, escala observada/inferida/desconhecida. Quando o usuario responder `nao tenho`, registrar indisponibilidade e nao pedir de novo. Se ele enviar arquivos parciais, atualizar a lista e solicitar apenas faltantes essenciais.
5. **Decidir e comunicar:** se existe um essencial ausente, marcar `AWAITING_REQUIRED_INPUT` e nao alegar G1.5 pronto. Se so faltam opcionais/recomendados, prosseguir com anotacao explicita das inferencias, `READY_WITH_ASSUMPTIONS`. A falta de vista ortografica traseira ou lateral nao bloqueia por si so uma modelagem com escala relativa. Ausencia de escala calibrada bloqueia apenas afirmacoes em mm e pedidos de dimensoes fisicas exatas.
6. **Registrar evidencias:** salvar `planning/gcb/intake/intake_report.json` e `file_request.md` quando ha filesystem executavel; em ChatGPT sem filesystem local, relatar verbalmente o inventario e pendencias sem falsificar caminhos ou checksums. Apos receber arquivos essenciais, seguir G1 e G1.5 normalmente.

## Catalogo de pedido condicional

| Cenario | Essencial | Recomendado se existir | Texto sem arquivo |
|---|---|---|---|
| Copiar um design/arte | Ao menos uma arte de referencia acessivel (PNG/JPG/WEBP/PDF) ou fonte 3D | Fotos frontal/lateral/traseira/superior, detalhes da face, asas, juntas, componentes | Estilo a preservar, qual parte e obrigatoria, destino |
| Corrigir um modelo existente | `.blend/.fbx/.glb/.obj` original ou acesso autorizado a cena atual | Screenshot do erro, geometria correta de exemplo | O que alterar, o que proteger |
| Criacao original sem imagem | Briefing claro em texto ou referencia conceitual | Moodboard ou arte | Estilo, proporcoes e destino |
| Escala exata solicitada | Medidas numericas confiaveis em texto **ou** desenho/manual com escala validada | Multiplas vistas e referencias com dimensoes | Unidades, tolerancias, escala global |
| Rig/animacao original | Modelo/arte existente; nao exigir rig preexistente | Videos de movimento, poses, diagramas de joints | Lista de clips (ex. Idle, Walk, Fly), rig personalizado vs padrao |
| Retargeting de rig | FBX/BLEND/GLB do rig alvo **ou** hierarquia de ossos documentada | Animacoes originais de teste | Poses, eixos, nomes e regras |
| Texturas exatas | Material de referencia confiavel, se exigido pelo escopo | Albedo, roughness, metallic, normal, emission, paleta | Shader/meta visual desejado |
| Roblox / web | Nenhum arquivo extra por padrao | Manual de asset, limites e perfis export, caso existam | Plataforma, formato, orcamento de triangulos |

*Tipos de arquivo sao alternativas, nao exigencias simultaneas.* Se usuario informou `nao tenho` para algo recomendado, parar de solicitar esse arquivo. Fontes diversas exigem verificacao de licenca/direitos e rastreamento de proveniencia; nunca executar scripts embutidos em `.blend`, PDF ou assets nao confiaveis.

## Regras de qualidade

- Distinguir **arquivo acessivel** de **arquivo apenas citado**; descricao textual nao substitui arte original quando o objetivo e reproduzir uma arte especifica.
- Nao exigir varias vistas ou fotos da parte oculta como precondicao universal; GCB ja admite `observed`, `inferred` e `unknown`.
- Nao exigir textura normal map para detalhe de mesh fisico; imagens so representam aparencia, nao provam relevo.
- A solicitação de arquivos nao substitui a analise da qualidade visual ou a validacao do modelo. `READY_FOR_REFERENCE_ANALYSIS` nao significa `G1.5_APPROVED`.
- Nao inventar medidas; se o pedido exige escala fisica e nao ha fonte confiavel, pedir as medidas ou propor explicitamente unidades relativas; nunca silenciosamente converter para mm.
- Em edicao, **preservar original e baselines**; nao reconstruir a partir de um print quando o usuario quer editar o `.blend` real e a fonte nao esta disponivel.
- Evitar loops de requisicoes: uma coleta abrangente, depois pedidos incrementais apenas para bloqueadores novos e concretos.
- Nao criar assets ficticios para passar o preflight. Arquivos ausentes sao `PENDING`; imagens recebidas na conversa so contam como acessiveis se o agente realmente conseguiu examina-las.

## Integração com Codex e CLI local

O coordenador pode criar `planning/gcb/intake_manifest.json`, declarando **somente arquivos localmente verificados**. Consulte exemplo em `examples/gcb/intake_example.json`. O usuario nao precisa escrever esse JSON: o agente cria a partir do projeto.

```bash
python scripts/gcb_intake.py planning/gcb/intake_manifest.json --root . --out planning/gcb/intake
```

- Resultado: `intake_report.json` (pendencias por severidade/status e inventario) e `file_request.md` (mensagem de coleta para o usuario).
- Codigos de retorno: `0` pronto para G1 com ou sem inferencias; `3` arquivo/informacao essencial faltante; `2` manifest ou caminho invalido.
- Um `--root` local e caminhos `assets[].path` relativos, acessiveis e nao vazios sao exigidos para o CLI. Arquivos em anexos do chat podem ser inventariados por um agente que os visualizou, mas nao devem ser marcados como **verificados localmente** ate serem disponibilizados na pasta do projeto.
- Nunca alegar que o CLI validou a fidelidade visual ou a abertura do `.blend` apenas porque verificou existencia/extensao de arquivos.
- Codigo deterministico nao necessita de subagente AIR; o roteamento de visao/reconhecimento ja continua com o Reference Analyst.

## Formato recomendado da pergunta ao usuario

> Ja tenho: [nomes de arquivos conferidos]. Para iniciar seu GCB, envie [essenciais faltantes]. Se disponivel, envie tambem [referencias multiangulo/closeups/rig/textura, adaptados ao pedido]. Confirme por texto [dimensoes reais se exigidas, lista de animacoes, destino ou restricoes ainda desconhecidas]. Se nao existir algum arquivo opcional, diga "nao tenho"; o modelo usara inferencias explicitamente identificadas.

Nao usar este texto literalmente com placeholders. Compactar conforme os arquivos realmente ausentes e jamais pedir novamente o que esta no contexto.


## V1.7 — When the user asks the plugin to generate the references
If the user explicitly asks to **generate** the images needed for modeling, do not request user-uploaded images merely to satisfy the previous `reference_model` essential-asset rule. Classify as `original_model` with a text brief when there is no immutable source, or as `reference_model` when the user supplied a source to preserve. Request **only** missing essential identity/style/destination information that cannot be inferred safely. Do not force the user to produce orthographic views that the plugin has been asked to generate. Generated views need conditional G1-R source provenance, an anatomical/structural reviewer decision and `inferred` confidence where data are unseen. If image generation is unavailable, disclose the tool limitation and return a plan; no pretend output. After real generation and review, G0-F can inventory accessible files; G1.5 still requires its numerical specification.

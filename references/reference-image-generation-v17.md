# GCB v1.7 — Image Reference Production & Anatomical QA (G1-R)

## Finalidade / ativacao

Ativar G1-R **somente** quando o usuario solicitar que o plugin gere imagens destinadas a construcoes 3D (uma imagem especifica, character sheet, vistas faltantes, closeups ou "gere todas as imagens necessarias para o Codex"). O objetivo e gerar **referencias de producao legiveis, anatomicamente e estruturalmente coerentes**, nao apenas arte atraente. Nao transformar toda modelagem, edicao ou blueprint GCB em solicitacao de gerar imagem. Se nao existir ferramenta de geracao de imagem autorizada e disponivel, retornar `NOT_GENERATED` com plano; nunca inventar caminhos, imagens ou auditorias.

G1-R e um subgate condicional depois de G0-F/G1 e antes do G1.5. O **Reference Analyst** e responsavel pelo contrato de identidade/procedencia e planos de vistas; **Fidelity Auditor** faz verificacao independente dos pixels gerados; **Geometry Architect** prepara instrucao por peca e GCB numerico. AIR pode ajudar em planejamento complexo, mas nenhuma delegacao e garantida sem runtime.

### Principio fundamental

A arte original do usuario (se houver) continua imutavel e e o alvo visual. **Imagens geradas de vistas ocultas sao hipoteticas**, nunca prova observada de superfícies ou dimensoes reais. Quando nao houver referencia original, a arte gerada que o usuario aprovar pode se tornar *design reference*, nunca medida fisica. A prancha GCB tecnica final e renderizada **a partir de `gcb_spec.json`**: nao usar imagem gerada livremente para preencher medidas, coordenadas ou calibracao de camera.

## 0. Integração com coleta (G0-F)

- Verificar anexos e arquivos ja presentes antes de pedir qualquer coisa. Se o usuario pediu ao plugin que **gere** as referencias, nao exigir que ele entregue essas mesmas imagens; classificar `original_model` quando apenas o briefing existe, ou `reference_model` se houver arte original a preservar.
- Solicitar apenas o contexto essencial ausente e nao inferivel: identidade/estilo/proibições estritas/pecas fundamentais, destino e detalhes especificos quando realmente alteram a representacao. Nao forcar desenho traseiro, foto frontal ou escala fisica inexistentes.
- Se houver restricoes legais/autorais de assets, respeitar fontes e termos disponiveis. Nao converter imagens em execucao de scripts.

## 1. Contrato de identidade antes de gerar

Registrar um inventario unico de partes com IDs estaveis: silhueta, proporcoes relativas, perspectiva conhecida, quantidades, conexoes, cores/materiais e elementos protegidos. Estabelecer um canon visual (imagem principal aprovada ou referencia imutavel): mudar SOMENTE componentes solicitados. O conjunto de imagens deve mostrar o **mesmo** asset, nao diferentes designs sob titulos iguais.

Para criaturas e personagens, avaliar explicitamente:
- Contagem e lateralidade de pernas, bracos, asas, dedos, cornos, olhos, mandiculas e cauda; simetria somente quando faz sentido; nao duplicar peca visivel e peca explodida no modelo final.
- Trajeto estrutural cranio/pescoco/torso/pelve/membros; insercao de asas e cauda; base da mandibula separada quando articulada; continuidade dos segmentos do esqueleto.
- Apoio, centro de massa visual, contato com chao, eixo de dobra e curso de juntas; estado neutro que caiba fisicamente sem atravesar volumes rigidos.
- Anatomia fantastica pode nao ser biologicamente realista, mas **deve possuir um modelo interno consistente** de cargas, juntas, articulacoes e movimentacao. Nao impor anatomia animal real a criaturas Bloxy ou stylized. **Bloxy nao equivale a low-poly.**

Para plantas: verificar enraizamento ou fixacao, distribuicao de caules/folhas, espessura, plano de flexao, estabilidade, folhas que nao brotam de ponto flutuante, cabecas/flores se conectando a um eixo plausivel; plantas fixas nao viram personagens humanoides. Para mecanicos/veiculos/props: espessura funcional, posicao de eixos, pivôs, montagem, volume e folgas coerentes; detalhes decorativos nao podem mascarar geometria impossivel.

## 2. Plano de imagens adaptativo

- **Principal:** vista de referencia master clara, fundo neutro, silhueta distinguivel e junta/encaixe visivel. Se referencia original existir, NAO substituir por uma reinterpretacao.
- **Vistas adicionais:** frontal/lateral/oposta/traseira/superior ou perspectiva 3/4 apenas quando isso reduz a incerteza relevante. Conservar escala aparente/proporcao, cores/placas, numero de partes, assimetria e localizacao das articulacoes. Vistas sinteticas sao `generated_inferred`, a menos que venham de cameras verificadas de um 3D real.
- **Closeups tecnicos:** juntas, mandíbulas, conexoes de asas, materiais de superficie, encontros de segmento, cavidades, partes ocultas de alta relevancia. Cada closeup deve identificar componente e orientacao.
- **Decomposicao/explodido:** apenas quando a separacao entre pecas e montagem nao estiver clara. Rotular deslocamento explosivo como *ilustrativo*, nunca coordenada do mundo.
- **Separacao de etapas:** se houver mais de uma fase, as imagens sao derivadas do mesmo master; manter referencias cruzadas por IDs sem inventar dimensoes. Nao produzir 12 imagens se duas resolvem a construcao.

Nao confundir o poster de uma geracao de imagens com o **blueprint geometrico real**. Texto, numeros e setas incluidos por modelo de imagens devem ser inspecionados e tratados como decorativos/hipoteses ate conferidos contra o JSON.

## 3. Contrato de prompt de geracao

Para cada imagem, preparar internamente:
1. Identidade e caracteristicas obrigatorias do master, `source_reference_ids`, contagem de partes, regras de silhueta e estilo.
2. Especificacao de camera (`front`, `side`, `back`, `top`, `three_quarter`, `closeup`) e **tipo de projeção real** se comprovado. Nunca chamar uma geracao livre de camera calibrada.
3. Objetivo geometricamente verificavel: quais conexoes, superficies, perfis, volumes, separacoes e articulacoes esta vista esclarece.
4. Nao permitir membros extras, membros ocultos omitidos quando obrigatorios, fusoes impossiveis, fisica involuntariamente quebrada, sombras ocultando juntas, pernas atravessando o chao, decal flutuante, asa sem raiz, mandíbula duplicada.
5. Material/texture language (glow, roughness, pedra, metal, escamas, placas) separada de instrucoes para **geometria fisica**; brilho nunca justifica dispensar juntas.
6. Respeitar o material original, a paleta e a representacao pedida sem improvisar ornamentos ou trocar o tema para outro estilo. Zero IDs soltos/unreferenciados.

Quando o usuario pedir so uma imagem, gerar apenas uma; validar e indicar o que segue inferido, sem forcar vistas extras.

## 4. Inspecao real da imagem / auditoria independente

**Obrigatorio apos cada geracao:** abrir/inspecionar visualmente o arquivo final. Prompt bem escrito nao e evidencia de resultado certo. O Fidelity Auditor — separado da funcao criadora, quando o host oferecer revisao independente; caso contrario registrar revisao disponivel e seus limites — compara contra master, outras vistas e requisitos. Verificar:

| Categoria | Criterios | Bloqueio critico |
|---|---|---|
| `identity` | mesmo personagem/objeto, silhueta/cores/quantidades | arte virou outro design ou perdeu componente obrigatorio |
| `anatomy` | anatomia e apoio/fixacao logicamente coerentes | membro duplicado/faltante; membro impossivel; cauda ou cabeca solta |
| `connections` | raiz de asas/cauda, juntas, encaixes, volumetria | parte flutuando, atravessando volume indevidamente, ou fundida apesar de ser movel |
| `articulation` | pivôs, orientacao e amplitude de junta para rig quando requisitado | mandíbula/asa/junta exige movimento impossivel na montagem |
| `views` | consistencia entre as imagens; inferencias identificadas | comprimento/cor/contagem mudaram sem explicacao; vistas falsamente calibradas |
| `geometry` | reproduzibilidade como mesh, espessuras, separacao | efeito 2D substitui volume obrigatorio ou nao existe perfil montavel |
| `surface` | relevo real vs mapas; escala de texturas e microdetalhes | textura esconde problema estrutural ou relevo exigido inexiste |
| `handoff` | IDs, construcao por etapas, risco e criterios de sucesso | Codex fica sem partes/operacoes/referencia para reproduzir |

Verificacao nao implica prova de engenharia, simulacao fisica ou garantia de fidelidade. Para categorias irrelevantes marcar `NA` com justificativa. Para obstruidas marcar `UNKNOWN`, nunca `PASS`; desconhecido critico/obrigatorio impede aprovacao e exige nova imagem ou inferencia explicitamente sujeita a revisao. Registre `FAIL`, `UNKNOWN` com ids de imagens/partes, causa, severidade (`critical`, `major`, `minor`) e correcao localizada. Limitar tentativas quando repetir geracao nao melhora: pare com `REJECTED` e exponha bloqueadores em vez de inventar um sucesso.

## 5. Handoff para Codex (sem execucao ficticia)

Consolidar, por peca:
- ID estavel e nome, imagens e evidencia visual, `observed` na imagem originaria / `generated_inferred` em vistas reconstruidas / `unknown` nas superficies ocultas. Origem (user-original, generated-design, generated-inferred) SEMPRE separada da confianca; cada vista `generated_inferred` informa `based_on_ids` apontando para imagens reais de origem.
- Forma base (`box`, `sphere`, `cylinder`, `cone`, `wedge`, `custom_mesh`), volume proporcional, orientação; que deve ser geometry real e o que pode ser textura/material.
- Se movel: especificar pivô candidato, partes que devem permanecer separadas, articulacao prevista e tolerancia/encaixe sob comprovacao no Blender.
- Ordem de construcao, operacoes `bpy` ou ferramenta equivalente, detalhes por prioridade, criterios de QA por fase, riscos e limites de extrapolacao.
- Imagens aprovadas como referencias visuais + `image_reference_qa.json` + relatorio CLI de integridade + `codex_image_reference_handoff.md` + `gcb_spec.json`/pranchas deterministicas do G1.5.

Exemplo de dados: `examples/gcb/image_reference_qa_example.json`; contrato: `references/reference-image-qa-schema-v17.json`; utilitario opcional `scripts/gcb_image_qa.py` valida referencias e gera relatorio/handoff. **O utilitario NAO inspeciona imagem semanticamente, nao detecta anatomia por pixels e nao cria imagens nem modelos.** Verificacao de arquivo e checklist preenchido jamais sao prova de qualidade visual. Um avaliador precisa examinar o conteudo real, assinar a decisao e justificar as excecoes.

## 6. Condicoes de liberacao / rollback

- Imagens nao criadas: `NOT_GENERATED`; arquivos inexistentes ou nao abertos: `PENDING_VISUAL_QA`.
- Um check critico `FAIL` ou `UNKNOWN` sem justificativa resolvida: `REJECTED` ou `BLOCKED`; gerar correcao de vista/peca e verificar novamente.
- Liberar para G1.5 somente com inspecao visual real, cobertura suficiente, partes e vistas coerentes, decisao do auditor registrada. O validador offline pode retornar `ready_for_gcb` **somente quanto ao contrato e declaracao de revisao**, nao prova que a revisao efetivamente ocorreu.
- Se mudaram pecas aprovadas, invalidar as vistas dependentes e a baseline anterior; preservar arquivo original e versoes aceitas. G1.5 ainda e independente de G2-G8.

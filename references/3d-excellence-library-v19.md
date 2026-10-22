# Blender Forge Pro v1.9 | 3D Excellence Reference Library (3DERL)

## Objetivo e contratos

A biblioteca serve como **referência comparativa de qualidade** de assets 3D para ajudar o Codex/Blender a escolher princípios de construção, complexidade adequada, hierarquia, forma, materiais, modularidade e rigging.
**NÃO** transforma render de terceiros em planta de fabricação, coordenadas GCB, topologia comprovada, rig validado ou arquivo `.blend` já importado.

Fontes com licenças CC0 verificadas: [Kenney](https://kenney.nl/assets), [Quaternius](https://quaternius.com/faq.html) e [Poly Haven](https://polyhaven.com/license). As 15 entradas curadas (`references/3d-excellence-library-v19.json`) guardam origem, autor quando conhecido, link de miniatura oficial, licença e lições observáveis. Não substituir a arte do usuário por desenhos nem plagiar estilos/identidades específicas dos exemplos. O GCB JSON sempre é a verdade para geometria relativa do projeto.

### Tipos de evidência

- **Imagem / render de divulgação:** demonstra leitura de silhueta, proporções aproximadas, variedade de formas, materiais aparentes e gramática visual. *Não prova* fluxo de arestas, clean quad topology, rigs, pesos, pivôs, animações, UVs, compatibilidade Roblox ou triângulos.
- **Descrição no site oficial do asset:** pode informar que um pack possui animações/formatos/LOD. É uma **afirmação do produtor**, não uma execução ou inspeção nossa.
- **Modelo real no Blender/engine, inspecionado:** somente aqui verificar via QA a topologia, rig, tempo de animação, pivôs, modificadores, materiais e importação.
- **Referência original fornecida pelo usuário:** sempre prevalece na identidade visual, medidas observadas e restrições de estilo, mesmo quando o exemplar parecer mais polido.

### Handoff adaptativo G1 → G1.5 → G2

1. Classificar o asset alvo: `bloxy`, `stylized` ou `realistic`, além de destino (`roblox`, `render`, `web_glb`, `general`) e problema dominante (`anatomy`, `rig`, `furniture`, `foliage`, `hard_surface`, `modular`, `PBR`, `sculpt`). Não assumir que **bloxy == low-poly**.
2. Consultar até 3 referências que sejam realmente relacionadas à etapa. Diversificar problemas/fornecedores, não despejar a galeria inteira em cada prompt. Se não houver correspondência relevante, não usar a biblioteca.
3. Identificar **2–3 princípios de execução transferíveis** por referência; dizer o que é apenas aparência e não pode ser inferido.
4. Analisar arte original fornecida pelo usuário separadamente e listar conflitos. Nunca trocar proporções aprovadas por conveniência de outro asset.
5. Se o alvo for GCB, anexar `selected_references.json` e `selected_references.md` ao handoff como **referências consultivas**. A geometria usa `gcb_spec.json` e G1/ G1-R, não os thumbnails. `gcb.py prepare --excellence-references <...>` permite esse anexo opcional.
6. Usar Atlas Tool Selection Engine (ATSE v1.8) para sugerir ferramentas que materializem as decisões; não converter a recomendação do exemplo diretamente em `bpy.ops` sem verificar a API real.
7. Independently: Fidelity Auditor deve confrontar o **modelo gerado** com **arte do usuário**, sob projeções compatíveis. A galeria pode inspirar critérios de acabamento/organização, nunca substituir G1.5/G7 nem aprovar geometria.

### Como consultar no Codex

```bash
# Índice válido de referências CC0 sem acessar a rede
python scripts/excellence_reference_router.py validate

# Para um dragão Bloxy com asas e rig (máximo de três exemplos relevantes)
python scripts/excellence_reference_router.py select --goal "dragao bloxy com asas e rig" --style bloxy --focus anatomy --focus rig --stage G1.5 --target roblox --out planning/gcb/excellence

# Anexar recomendações de qualidade ao handoff técnico sem modificar a especificação GCB
python scripts/gcb.py prepare planning/gcb/gcb_spec.json --out planning/gcb --excellence-references planning/gcb/excellence/selected_references.json
```

A seleção gera `selected_references.json`, `selected_references.md` e `reference_gallery.html`. O HTML exibe **pré-visualizações remotas** via Internet e informa essa condição. Os **bytes das miniaturas NÃO são incorporados** ao plugin nesta versão; seus links e licenças são persistentes. Se for exigido uso offline, baixar miniaturas apenas mediante autorização explícita e conexão verificada:

```bash
python scripts/excellence_reference_router.py cache --plan planning/gcb/excellence/selected_references.json --out planning/gcb/excellence/cache --allow-network
```

O cache valida host HTTPS permitido, MIME, assinatura e limita o tamanho; falha de rede não autoriza fingir que imagens foram inspecionadas. Não adicionar dependência de carregamento dessas imagens ao G0-F, para não bloquear tarefa de usuário por conta da disponibilidade de biblioteca suplementar.

### Critérios técnicos que a biblioteca deve ensinar

- **Bloxy/Roblox:** massas segmentadas deliberadas, faces sólidas, conexões e articulações claras, controle de escala e nível de detalhe. Não forçar low-poly facetado nem R15 quando o modelo requer um rig próprio.
- **Criaturas e plantas:** silhueta, suporte de peso, volumes, tecidos/folhas/caules, oclusões assumidas, apêndices separados e pivôs alinhados.
- **Hard-surface e móveis:** montagem em subcomponentes, espessuras visíveis, curvas e chanfros com propósito, não-dependência de materiais para esconder defeitos.
- **Materiais:** distinguir relevo geométrico de bump/normal PBR, avaliar compatibilidade com engine.
- **Animação e export:** não extrapolar rig/Actions a partir de imagem; testar Blender e destino real.

### Anti-padrões (didáticos, não alegações sobre assets da biblioteca)

Veja `references/3d-excellence-antipatterns-v19.json` e `assets/excellence_refs/assembly_qa_diagrams.svg`, criado como diagrama sintético. Deve reprovar: mandíbula fundida e duplicada; membro desconectado; pivô fora da junta; vistas contraditórias; face transparente por normais; detalhes de shader usados como relevo falso.

### Proibição de sobrecarga

Não inserir as 15 imagens em cada resposta nem abrir toda a biblioteca para tarefas simples. Não baixar MBs de exemplos e não instalar add-ons externos sem necessidade/consentimento. Em modo offline, o catálogo textual de evidências e critérios ainda opera normalmente.

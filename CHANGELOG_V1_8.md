# Blender Forge Pro v1.8.0 — Atlas Blender Tool Selection Engine (ATSE)

## Implementado
- Integração do PDF original fornecido pelo usuário (85 páginas; 407 entradas; 16 capítulos; 11 workspaces), preservando bytes e SHA-256.
- Índice de 407 ferramentas `references/blender-atlas-index-v18.json`, cada qual com nome, capítulo, página, o que faz, aplicações, quando, motivo, uso correto e life-hack.
- Roteador Python read-only `scripts/blender_tool_router.py` para consultas por etapa G1.5–G8, alvo (Roblox/GLB/render) e descrição de tarefa. Registra o contexto do documento e sinaliza API `UNVERIFIED` até prova real.
- Gerador de índice reproduzível `scripts/build_blender_atlas_index.py`, dependência PyMuPDF apenas para manutenção/rebuild.
- Integração automática opcional ao `scripts/gcb.py prepare`: saída `blender_tool_plan.json` / `.md` e apontamento dentro do `gcb_handoff.md` para o Codex.
- Procedimento de decisão `references/blender-atlas-routing-v18.md` e instruções de uso no agente coordenador, Geometry Architect e Fidelity Auditor.

## Preservado
- Oito skills, as permissões/origem do plugin e a interface/default prompt, G0-F, G1-R, G1.5, G2-G8, AIR 1.4, Geometry Fidelity Lock e os formatos atuais do GCB.

## Limitações verificadas
- O atlas é documento de consulta secundário, não mapeamento de `bpy.ops` nem compatibilidade comprovada da versão instalada.
- Os testes determinísticos comprovam extração/roteamento/integração do handoff, não fidelidade artística ou execução em Blender/Roblox Studio.

# Relatório de publicação pública — 22/10/2026

**Fonte:** Blender Forge Pro, plugin privado original v1.9.0. O código textual foi importado após revisão de segurança.

## Auditoria

- Inventário da versão original: **135 arquivos** (131 textuais + 4 binários).
- Arquivos textuais examinados: **131 de 131**.
- A busca não identificou tokens reais OpenAI/GitHub/AWS/Google/Stripe/Slack, chaves privadas PEM nem URLs de webhooks.
- Um exemplo **fictício** de URL com autenticação básica em `tests/test_excellence_references_v19.py` foi reescrito sem alterar o teste.
- Nenhum arquivo com nome típico de segredos (como `.env`, `credentials.json` e chaves privadas) foi encontrado no inventário.
- A licença MIT existente foi mantida.

## Atlas do Blender

Foi criada a pasta rastreável `assets/blender-atlas/`, com `.gitkeep` temporário, para receber manualmente:

`assets/blender-atlas/Atlas_Blender_5_2_2_LTS_407_Ferramentas_e_11_Abas.pdf`

SHA-256 esperado: `1e8170c7631d1c86a073f45c926eea2e20157f104545eaa868c9ae401c9104cd`.

Até o envio do PDF, os testes e a consulta completa que verificam a integridade do Atlas poderão falhar. Não substituir o PDF por outro com conteúdo diferente sem atualizar e verificar o índice técnico correspondente.

## Imagens de cadeira

As três imagens `chair_front.png`, `chair_side.png` e `chair_top.png` **não serão publicadas**, por decisão do mantenedor. Elas não são pendências de upload.

**Nota técnica:** alguns testes e exemplos herdados da versão privada ainda fazem referência a esses arquivos; esses cenários precisam de fixtures alternativas caso se deseje executar a suíte integral sem os PNGs.

## Limites da auditoria

A análise de padrões reduz riscos, mas não comprova a ausência absoluta de segredos desconhecidos. Os binários originais não tiveram auditoria com a mesma cobertura dos arquivos textuais. Proteção de branches, secret scanning e push protection dependem de configuração e verificação nas definições do GitHub.

A publicação de scripts e testes não comprova, por si só, geometria real, rigging ou exportação funcionando no Blender/Roblox Studio.

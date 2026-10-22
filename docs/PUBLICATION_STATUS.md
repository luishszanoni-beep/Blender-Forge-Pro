# Relatório de publicação pública — 22/10/2026

**Fonte:** Blender Forge Pro, plugin privado original v1.9.0. A importação pública inclui 131 arquivos de texto, com revisão heurística anterior à publicação.

## Auditoria

- Inventário: **135 arquivos** (131 textuais + 4 binários).
- Arquivos textuais lidos e examinados: **131 de 131**.
- Nenhum token real OpenAI/GitHub/AWS/Google/Stripe/Slack, chave PEM ou webhook foi identificado nas varreduras realizadas.
- Um exemplo **fictício** de URL contendo autenticação básica, presente em `tests/test_excellence_references_v19.py`, foi reescrito para montar a URL em tempo de execução. O teste negativo de URL permanece.
- Arquivos com nomes típicos de segredos (`.env`, `credentials.json`, chaves privadas etc.): **nenhum identificado** no inventário do plugin.
- Licença MIT existente no GitHub preservada.

## Quatro arquivos binários pendentes

| Caminho original | Estado |
| --- | --- |
| `assets/blender-atlas/Atlas_Blender_5_2_2_LTS_407_Ferramentas_e_11_Abas.pdf` | Pendente |
| `examples/reference_images/chair_front.png` | Pendente |
| `examples/reference_images/chair_side.png` | Pendente |
| `examples/reference_images/chair_top.png` | Pendente |

**SHA-256 esperado do PDF:** `1e8170c7631d1c86a073f45c926eea2e20157f104545eaa868c9ae401c9104cd`.

Esses arquivos devem ser importados **sem alteração de conteúdo**, após inspeção de metadados, segurança e direitos. O PDF é necessário para a validação de integridade do ATSE; testes que dependam desses assets podem falhar até sua inclusão.

## Limites

Esta auditoria usa detecção de padrões e revisão do inventário, não prova ausência absoluta de credenciais desconhecidas. Os quatro binários ainda não foram auditados com a mesma cobertura dos textos. As configurações da interface do GitHub (secret scanning, proteção de branch e push protection) devem ser verificadas pelo proprietário; arquivos de configuração não as ativam automaticamente.

O upload do código **não comprova** modelagem real, rigging, exportação nem execução no Roblox Studio.

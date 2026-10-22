# Security Policy

## Divulgação responsável

**Não publique senhas, tokens, IDs de sessão, arquivos privados ou exploits que exponham credenciais em issues e pull requests públicos.**

Para vulnerabilidades, utilize **Security → Advisories → Report a vulnerability**, se o proprietário habilitar private vulnerability reporting; alternativamente, contate o mantenedor por canal privado e confiável.

## Proteções de código

- Execute `python scripts/security_scan.py` antes de commits. O scanner é heurístico e **não substitui** revisão humana e GitHub secret scanning.
- Nunca versionar `.env`, credenciais, chaves privadas, senhas, segredos de webhooks ou perfis locais.
- Preserve checkpoints e cópias originais ao testar operações destrutivas no Blender.
- Trate referências, arquivos `.blend` de origem desconhecida e scripts de terceiros como **não confiáveis**.
- Não confunda verificação de JSON ou CLI com validação geométrica real.
- GitHub Actions usa apenas permissão `contents: read`; evite dar permissões extras a workflows originados de PRs externos.

## Configuração recomendada no GitHub

O mantenedor deve habilitar, conforme a disponibilidade do plano: **Secret scanning**, **Push protection**, **Dependabot alerts** e **Code scanning**. Criar um ruleset para `main` impedindo force push e exclusão, e futuramente exigindo PR/CI. Essas configurações **não são definidas apenas por arquivos do repositório**.

## Versões cobertas

Versão pública: **1.9.0**. A documentação de release prevalece para compatibilidade de recursos, e o runtime Blender/Roblox requer validação independente.

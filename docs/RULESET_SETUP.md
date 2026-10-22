# Proteção da branch principal — Blender Forge Pro

Este diretório contém um **modelo de Ruleset para importar no GitHub**, não uma configuração ativada automaticamente. Apenas o administrador pode ativá-lo em **Settings → Rules → Rulesets**.

## Como ativar

1. Faça download do arquivo [main-branch-protection.json](rulesets/main-branch-protection.json) utilizando **Raw → Save as** ou o botão de download.
2. Abra **Settings → Rules → Rulesets → New ruleset → Import a ruleset**.
3. Importe o JSON, revise a seleção da branch padrão (deve atingir `main`), confira **Enforcement: Active** e mantenha **Bypass list** vazia.
4. Confira **Require status checks**, com o check exato `source-checks` e fonte GitHub Actions (App ID `15368`).
5. Crie/ative o ruleset e depois valide que ele consta em **Rulesets** como **Active**.

## Segurança que este modelo aplica

- **Block deletions**: impede exclusão da branch principal.
- **Block force pushes**: impede reescrever o histórico publicado.
- **Require a pull request before merging**: força revisão da alteração por PR, embora exija **zero aprovações humanas** para não bloquear um mantenedor solo.
- **Require conversation resolution**: threads pendentes devem ser resolvidas.
- **Require status checks to pass**: exige o job `source-checks`, executado pelo aplicativo oficial GitHub Actions, sobre a base atualizada.

## Limitações e recomendações

- **Aprovação humana independente:** o modelo usa zero aprovações. Se houver outro colaborador confiável, aumente para **1 aprovação**; isso oferece proteção contra alterações indevidas mesmo quando uma conta com permissão de escrita foi comprometida. O autor de um PR normalmente não pode aprovar o próprio PR.
- **Sem bypasss:** nenhum ator recebe exceção às regras. Isso inclui o mantenedor e o aplicativo usado pelo Codex/ChatGPT. Atualizações deverão seguir branch → PR → CI → merge.
- **Signed commits** e **linear history** não são exigidos inicialmente; ativá-los sem preparar as ferramentas de commit/merge pode bloquear o pipeline.
- **Secret scanning e Push protection** precisam ser habilitados em **Settings → Advanced Security** separadamente; este JSON não os ativa.
- **Actions**: preserve tokens com privilégio mínimo e workflow permissions `Read repository contents`.
- Este arquivo no repositório não impede ataques por si só: o ruleset só passa a valer depois da ativação pela interface administrativa do GitHub.

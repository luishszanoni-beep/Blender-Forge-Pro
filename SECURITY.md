# Security Policy

## Supported version

Public source distribution: **Blender Forge Pro v1.9.0**. The source is actively maintained via pull requests and a protected default branch. Blender integration still requires verified runtime access and target-application checks.

## Report a vulnerability privately

**Never post API keys, access tokens, passwords, private models, exploit payloads containing credentials, or confidential project files in public issues or pull requests.**

If GitHub private vulnerability reporting is enabled, use **Security → Advisories → Report a vulnerability**. Otherwise contact the maintainer through an established private channel. If a credential has already leaked, revoke/rotate it promptly.

## Local execution and asset safety

- Run `python scripts/security_scan.py` before publishing changes. This is a **heuristic pre-check**, not a substitute for GitHub secret scanning or a professional security review.
- Keep `.env`, access tokens, private keys, account configuration and machine-specific paths outside source control.
- Review third-party Blender scripts, add-ons and `.blend` content before opening/running them in a trusted environment. Disable automatic execution for untrusted sources.
- Preserve immutable source references and checkpoints. Never overwrite the only copy of a user's original scene.
- Treat locally downloaded 3D previews and external references as **untrusted input** until validated.
- Validate export artifacts in their destination tools. An apparently successful Python process does not prove a secure or correct Blender/Roblox result.
- GitHub Actions uses minimal `contents: read` privileges; do not increase permissions or execute untrusted PR code with secrets.

## GitHub repository protections

The repository administrator has enabled a **`main` branch ruleset** preventing deletions and non-fast-forward updates and requiring pull requests plus the official GitHub Actions `source-checks` job. Changes must follow **branch → PR → passing CI → merge**, with no force push.

Also enable/verify **Secret scanning**, **Push protection**, **Dependabot alerts** and **Code scanning** under the repository's security settings when available. These security settings are administered on GitHub and cannot be enabled merely by adding a Markdown file.

See [branch-protection instructions](docs/RULESET_SETUP.md) and [responsible contribution guidelines](CONTRIBUTING.md).

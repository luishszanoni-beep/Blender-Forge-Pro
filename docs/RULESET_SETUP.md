# Protected Main Branch — GitHub Ruleset

**Current repository status:** the `Blender Forge Pro | Protect main` ruleset was confirmed **active** on October 22, 2026. GitHub ruleset ID: `25614653`.

The JSON under [rulesets/main-branch-protection.json](rulesets/main-branch-protection.json) is a **source template** for the current protection policy. Saving this JSON in Git alone does not activate a ruleset.

## Enforced controls

| GitHub rule | Purpose |
| --- | --- |
| Block deletions | Prevent accidental or malicious deletion of the protected branch |
| Block force pushes | Prevent non-fast-forward history rewriting |
| Require pull requests | Avoid direct edits to `main` |
| Resolve PR conversations | Keep review issues explicit |
| Require passing status checks | Require `source-checks` before merge |
| Require branch to be up to date | Revalidate PRs against current `main` changes |
| Bypass actors | No privileged bypass actors configured |

The required check is `source-checks` produced by the **official GitHub Actions** app, integration ID `15368`. The repository is maintained by a solo developer and the ruleset currently requires **zero independent approvals**. If a second trusted maintainer joins, consider requiring one independent approval.

## Repository contribution flow

1. Open a new branch from `main`.
2. Make changes on that branch; do not force-push to `main`.
3. Open a pull request.
4. Allow `source-checks` to complete successfully, resolve review threads and ensure your PR is current.
5. Merge using a supported merge method.

If checks fail, repair the proposed branch rather than bypassing protections.

## If you need to restore the ruleset

Repository administrators can open **Settings → Rules → Rulesets** and import the JSON template; select the default `main` branch and set enforcement to **Active**. Confirm status checks and zero bypass actors. Do not create duplicate active rulesets without understanding their interaction.

## Additional security controls

Enable secret scanning, push protection and Dependabot alerts in **Settings → Advanced Security**, as available on the GitHub account plan. Keep GitHub Actions workflow permissions to **Read repository contents** by default.

Branch protection alone cannot prevent account compromise or malicious changes that pass all tests; multi-factor authentication and code review remain important.

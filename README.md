# career-systems-internal

Internal Career Systems ops plugin: batch-process and redact Skool screenshots, log wins to the proof sheet.

Skills:
- `skool-redaction-workflow` — orchestrates the full screenshot → proof-log pipeline
- `skool-redact-images` — redacts avatars, names, and @mentions
- `skool-update-proof-log` — uploads redacted images and appends proof-log rows

## Install via Claude Code

This repo is a Claude Code marketplace. Add the marketplace, then install the
plugin from it (the install form is `<plugin>@<marketplace>`):

```bash
# 1. Add the marketplace (owner/repo or full URL)
/plugin marketplace add Blaze212/cs-internal-skills

# 2. Install the plugin from that marketplace
/plugin install career-systems-internal@career-systems-internal
```

Once installed, the skills auto-discover and trigger from natural language.

Useful management commands:

```bash
/plugin marketplace list            # marketplaces you've added
/plugin marketplace update career-systems-internal   # pull the latest version
/plugin marketplace remove career-systems-internal
/plugin                             # browse / install / uninstall via the UI
```

## Releasing updates

This repo is consumed as a Claude Code marketplace plugin. Consumers only pull a
new copy when the **version bumps**, so every time you change a skill you must
bump the version. The version lives in three places that must stay in sync:

- `.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json` → `metadata.version`
- `.claude-plugin/marketplace.json` → `plugins[].version`

Use the bump script — it updates all three at once:

```sh
node scripts/bump-version.mjs            # patch bump (default): 2.0.1 -> 2.0.2
node scripts/bump-version.mjs minor      # 2.0.2 -> 2.1.0
node scripts/bump-version.mjs major      # 2.1.0 -> 3.0.0
node scripts/bump-version.mjs 3.4.2      # set an explicit version
node scripts/bump-version.mjs patch --commit   # also commit + tag v<version>
```

Typical flow when shipping a change:

```sh
# 1. make your skill edits
node scripts/bump-version.mjs patch --commit
git push --follow-tags
```

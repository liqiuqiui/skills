# Personal Agent Skills

This repository is a personal catalog of reusable agent skills.

It follows the `vercel-labs/skills` discovery convention: each skill lives under `skills/<skill-name>/SKILL.md`.

## Contents

```text
<repo>/
  README.md
  scripts/
    validate-skills.py
  skills/
    develop-maibot-plugin/
      SKILL.md
      README.md
      references/
      evals/
```

Do not put a `SKILL.md` at the repository root if this catalog will contain multiple skills. The `skills` CLI gives a root `SKILL.md` priority and, by default, stops before scanning nested skills.

## Available Skills

- `develop-maibot-plugin` - develop, migrate, debug, and package MaiBot plugins with `maibot-plugin-sdk`.

## Install With `skills`

After publishing this directory as a GitHub repository, list available skills:

```bash
npx skills add https://github.com/liqiuqiui/skills --list
```

Install one skill:

```bash
npx skills add https://github.com/liqiuqiui/skills --skill develop-maibot-plugin
```

Equivalent shorthand:

```bash
npx skills add liqiuqiui/skills@develop-maibot-plugin
```

Install from a direct tree URL:

```bash
npx skills add https://github.com/liqiuqiui/skills/tree/main/skills/develop-maibot-plugin
```

For Codex, project-level installs are placed under `.agents/skills/` by the installer. Global installs use `~/.codex/skills/`.

## Local Validation

Validate all skills in this catalog:

```bash
python3 scripts/validate-skills.py
```

Check what the `skills` CLI discovers locally:

```bash
npx skills add . --list
```

## Adding More Skills

Create each new skill as:

```text
skills/<new-skill-name>/
  SKILL.md
  references/
  scripts/
  assets/
```

Only `SKILL.md` is required. Keep supporting files inside that skill directory so installers copy them together.

# develop-maibot-plugin

Skill for creating, migrating, debugging, and packaging MaiBot plugins with `maibot-plugin-sdk`.

## Install Path

Install this directory as the skill:

```text
skills/develop-maibot-plugin
```

The required entry point is:

```text
skills/develop-maibot-plugin/SKILL.md
```

## What It Covers

- New plugin scaffolding under `MaiBot/plugins/`
- `_manifest.json` and capability declarations
- `MaiBotPlugin`, lifecycle methods, and `create_plugin()`
- `@Tool`, `@Command`, `@EventHandler`, `@HookHandler`, `@API`, `@MessageGateway`, and `@LLMProvider`
- method-level `self.ctx` capability references that should be checked against the local SDK
- component decorator signatures and config model patterns
- Migration from old `src.plugin_system` plugins
- Manifest schema validation against the local MaiBot manifest schema
- Focused validation and debugging workflow

# Migrating Old MaiBot Plugins

Use this reference when a plugin imports `src.plugin_system`, uses old base classes, or follows the old in-process plugin model.

## Core Translation

| Old | New |
|---|---|
| `BasePlugin` | `MaiBotPlugin` |
| `@register_plugin` | remove; add module-level `create_plugin()` |
| `BaseAction` | `@Tool` for new code, `@Action` only for compatibility |
| `BaseCommand` | `@Command` method |
| `BaseTool` | `@Tool` method |
| `BaseEventHandler` | `@EventHandler` method |
| `get_plugin_components()` | remove; decorators are collected automatically |
| `ConfigField` / `config_schema` | `PluginConfigBase` + `Field` + `config_model` |
| `section_meta` | model class metadata such as `__ui_label__`, `__ui_order__`, `__ui_icon__` |
| `self.send_text(...)` | `await self.ctx.send.text(...)` |
| `self.get_config(...)` | `await self.ctx.config.get(...)` or `self.config` |
| direct `src.*` API calls | `self.ctx.<capability>` |
| `WorkflowStep` | `HookHandler` |

## Migration Workflow

1. Read `<sdk-dir>/docs/migration-guide.md` for the exact old construct being replaced.
2. Replace imports with `maibot_sdk` imports.
3. Collapse component classes into decorated async methods on one `MaiBotPlugin` subclass unless the plugin has a strong reason to split helper classes.
4. Remove manual component registration.
5. Convert old config schema to `PluginConfigBase` sections.
6. Replace old direct APIs with `self.ctx` calls.
7. Update `_manifest.json`:
   - `manifest_version`: 2
   - SDK bounds compatible with local `<sdk-dir>/pyproject.toml`
   - capabilities reflecting actual `ctx` calls
   - dependency entries using local schema `dependencies` items, not old ad-hoc fields
   - LLM provider declarations if applicable
8. Run syntax/import checks and targeted load tests.

## Action To Tool Guidance

Old `Action` often mixed activation rules, parameters, and prompting. For new SDK-style behavior:

- Put "when to use" text in `brief_description` and `detailed_description`.
- Convert `action_parameters` to `ToolParameterInfo` or object schema.
- Return structured dicts where possible.
- If the old action sent a message, keep `stream_id` as a required parameter or obtain it from handler kwargs when the Host supplies it.

Use legacy `@Action` only when a narrow migration needs compatibility with old metadata and the task does not ask for a full modernization.

## Common Pitfalls

- `create_plugin()` must not require constructor arguments.
- `self.ctx` is available after Runner injection; use it in `on_load`, not in `__init__`.
- The plugin process is isolated. Shared global state in the main process is not available.
- `WorkflowStep` is removed; do not silently alias it.
- Component protocol names are uppercase internally (`TOOL`, `COMMAND`, `EVENT_HANDLER`, etc.).
- `ctx.logger` is a standard logger; do not use removed async logging APIs.
- `self.ctx.db.*` calls map to manifest capability names `database.*`.

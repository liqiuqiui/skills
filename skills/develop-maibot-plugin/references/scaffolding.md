# MaiBot Plugin Scaffolding

Use this reference when creating a new plugin or reshaping a plugin folder.

Local source of truth:

- Manifest schema: `<maibot-dir>/plugins/_manifest.schema.json`
- Example plugin: `<maibot-dir>/plugins/hello_world_plugin/`
- SDK version and API: inspect the `maibot_sdk` package imported by `<maibot-dir>/.venv/bin/python`; use a separate `<sdk-dir>` checkout only as supporting material unless the user explicitly says it is the active SDK source.

## Folder Layout

Recommended:

```text
<maibot-dir>/plugins/my_plugin/
  _manifest.json
  plugin.py
  config.toml
  README.md
  utils.py
```

Only `plugin.py` is the hard entry point. `_manifest.json` is still important because the Host uses it for identity, version compatibility, dependencies, capabilities, and static declarations such as LLM providers.

## Manifest Checklist

Base fields should mirror `<maibot-dir>/plugins/hello_world_plugin/_manifest.json` and satisfy `<maibot-dir>/plugins/_manifest.schema.json`:

```json
{
  "manifest_version": 2,
  "version": "0.1.0",
  "name": "插件显示名称",
  "description": "插件说明",
  "author": {
    "name": "作者",
    "url": "https://example.com"
  },
  "license": "GPL-v3.0-or-later",
  "urls": {
    "repository": "https://example.com/repo",
    "homepage": "https://example.com",
    "documentation": "https://example.com/docs",
    "issues": "https://example.com/issues"
  },
  "host_application": {
    "min_version": "1.0.0",
    "max_version": "1.0.0"
  },
  "sdk": {
    "min_version": "2.0.0",
    "max_version": "2.99.99"
  },
  "dependencies": [],
  "capabilities": [],
  "i18n": {
    "default_locale": "zh-CN",
    "locales_path": "_locales",
    "supported_locales": ["zh-CN"]
  },
  "plugin_type": "extension",
  "id": "author.my-plugin"
}
```

Schema-sensitive details:

- `version`, `host_application.*`, and `sdk.*` must be strict `x.y.z` semantic versions.
- `author.url` and `urls.repository` must be HTTP(S) URLs. Optional URL fields, when present, must also be HTTP(S) URLs.
- `id` must contain at least one `.` or `-`, for example `author.weather-notice`.
- `dependencies` entries use `{ "type": "plugin", "id": "...", "version_spec": ">=1.0.0" }` or `{ "type": "python_package", "name": "...", "version_spec": ">=1.0.0" }`.
- `i18n.default_locale` is required by the local schema.
- Add `llm_providers` only for provider plugins, and make it exactly match collected `@LLMProvider` declarations.

Add capabilities that match actual `self.ctx` usage. Examples:

- `send.text`, `send.image`, `send.forward`, `send.hybrid`, `send.emoji`, `send.custom`
- `config.get`
- `emoji.get_random`, `emoji.get_by_description`
- `message.get_recent`, `message.build_readable`
- `llm.generate`, `llm.generate_with_tools`, `llm.embed`
- `database.query`, `database.save`, `database.count`
- `chat.open_session`
- `gateway.route_message`, `gateway.update_state`
- `render.html2png`
- `knowledge.search`
- `statistics.local.token_trend`, `statistics.local.message_trend`

If the exact capability names are uncertain, inspect `<maibot-dir>/plugins/_manifest.schema.json`, `<sdk-dir>/maibot_sdk/context.py`, and `<sdk-dir>/maibot_sdk/capabilities/`.

When `<sdk-dir>` differs from the SDK package imported by the current MaiBot environment, prefer the imported package for plugin compatibility decisions.

## Config Model Pattern

Use a config model when a plugin has user-tunable settings or WebUI configuration.

```python
from maibot_sdk import Field, MaiBotPlugin, PluginConfigBase


class PluginSection(PluginConfigBase):
    __ui_label__ = "插件"
    __ui_icon__ = "package"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="0.1.0", description="配置版本")


class FeatureSection(PluginConfigBase):
    __ui_label__ = "功能设置"
    __ui_icon__ = "settings"
    __ui_order__ = 1

    greeting: str = Field(
        default="你好",
        description="默认问候语",
        json_schema_extra={"label": "问候语", "placeholder": "请输入问候语"},
    )


class MyPluginConfig(PluginConfigBase):
    plugin: PluginSection = Field(default_factory=PluginSection)
    feature: FeatureSection = Field(default_factory=FeatureSection)


class MyPlugin(MaiBotPlugin):
    config_model = MyPluginConfig
```

Inside handlers, read validated config through `self.config.feature.greeting`. Use `await self.ctx.config.get("feature.greeting", "你好")` only when a lightweight raw lookup or cross-plugin/global lookup is better.

Optional `config.toml` should mirror the model defaults when the user needs editable defaults:

```toml
[plugin]
enabled = true
config_version = "0.1.0"

[feature]
greeting = "你好"
```

## New Plugin Implementation Steps

1. Create `<maibot-dir>/plugins/<plugin_id>/`.
2. Add `_manifest.json` based on the example plugin.
3. Add `plugin.py` with `MaiBotPlugin`, lifecycle methods, decorators, and `create_plugin()`.
4. Add `config_model` if the plugin has settings.
5. Add `config.toml` if the Host expects a config file or if defaults should be visible before first load.
6. Add `README.md` when the plugin has commands, setup requirements, external credentials, or operational caveats.
7. Run focused validation from `testing-debugging.md`.

## Dependency Guidance

For normal plugin code, depend on `maibot-plugin-sdk` and standard Python packages. If a plugin needs an extra third-party dependency, add a `dependencies` item with `type: "python_package"` and document operational requirements in the plugin README. Avoid adding dependencies to the main project unless the task explicitly asks for a repository-level dependency change.

---
name: develop-maibot-plugin
description: Develop, migrate, debug, and package MaiBot plugins using the local MaiBot main project and maibot-plugin-sdk. Use this skill whenever the user asks to create a MaiBot plugin, modify a plugin under MaiBot/plugins, migrate an old src.plugin_system plugin to the SDK, add Tool/Command/EventHandler/HookHandler/API/MessageGateway/LLMProvider components, work with _manifest.json or config.toml, or debug plugin loading/runtime behavior, even if they only say "写个麦麦插件" or "给 MaiBot 加个插件功能".
---

# MaiBot Plugin Development

Use this skill to build plugins for the local MaiBot workspace. Treat the local repositories as the source of truth:

- Main project: `MaiBot/`
- Plugin SDK: `maibot-plugin-sdk/`
- Local SDK guide: `maibot-plugin-sdk/docs/guide.md`
- SDK migration guide: `maibot-plugin-sdk/docs/migration-guide.md`
- Example plugin: `MaiBot/plugins/hello_world_plugin/`
- Online docs to verify when network is available: `https://github.com/Mai-with-u/docs/tree/main/develop` and its plugin development area. The user may refer to `plugin-dev`; current docs may use `plugin_develop`, so inspect the tree instead of assuming the path.

## First Moves

1. Inspect the target plugin and nearby examples before editing:
   - `rg --files MaiBot/plugins maibot-plugin-sdk | sort`
   - `sed -n '1,260p' MaiBot/plugins/hello_world_plugin/plugin.py`
   - `sed -n '1,220p' MaiBot/plugins/hello_world_plugin/_manifest.json`
2. Read the SDK docs section that matches the task. Prefer `maibot-plugin-sdk/docs/guide.md` over memory.
3. Decide the plugin shape:
   - Ordinary user-facing ability: `@Tool` for model-invoked actions, `@Command` for explicit slash/regex commands.
   - Passive reaction or pipeline observation: `@EventHandler`.
   - Named pipeline extension with ordering/error policy: `@HookHandler`.
   - Plugin-to-plugin callable surface: `@API(public=True)` plus `self.ctx.api.call`.
   - External platform bridge: `@MessageGateway` plus `self.ctx.gateway.update_state` and `route_message`.
   - Custom model provider: manifest `llm_providers` plus `@LLMProvider`.
4. Keep plugins isolated from MaiBot internals. New plugin code should import from `maibot_sdk` and ordinary third-party libraries, not `MaiBot/src/*` or `src.*`.

## Required Plugin Contract

Every SDK plugin needs:

- A folder under `MaiBot/plugins/<plugin_name>/`.
- `plugin.py` as the entry file.
- A `MaiBotPlugin` subclass.
- Implemented async lifecycle methods:
  - `on_load(self) -> None`
  - `on_unload(self) -> None`
  - `on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None`
- A module-level `create_plugin()` that returns an instance. It receives no arguments, so do setup in `on_load`.
- Usually a `_manifest.json` with `manifest_version`, `id`, version bounds, dependencies, and capability declarations.

Minimal skeleton:

```python
from maibot_sdk import CONFIG_RELOAD_SCOPE_SELF, Command, MaiBotPlugin, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType


class MyPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        self.ctx.logger.info("Plugin loaded")

    async def on_unload(self) -> None:
        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        if scope == CONFIG_RELOAD_SCOPE_SELF:
            self.ctx.logger.info("Plugin config updated: version=%s", version)
        del config_data

    @Tool(
        "say_hello",
        brief_description="在当前聊天中发送问候",
        detailed_description="参数说明：\n- stream_id：string，必填。当前聊天流 ID。",
        parameters=[
            ToolParameterInfo(
                name="stream_id",
                param_type=ToolParamType.STRING,
                description="当前聊天流 ID",
                required=True,
            ),
        ],
    )
    async def handle_say_hello(self, stream_id: str, **kwargs):
        del kwargs
        await self.ctx.send.text("你好！", stream_id)
        return {"success": True, "message": "已回复"}

    @Command("hello", pattern=r"^/hello$")
    async def handle_hello(self, stream_id: str = "", **kwargs):
        del kwargs
        await self.ctx.send.text("Hello!", stream_id)
        return True, "Hello!", True


def create_plugin() -> MyPlugin:
    return MyPlugin()
```

## Development Workflow

When asked to implement a plugin:

1. Identify whether this is new development, modification, migration, or debugging.
2. Read the relevant references:
   - New plugin or feature: `references/scaffolding.md` and `references/components-and-capabilities.md`.
   - Exact decorator arguments, config model details, dynamic APIs, or component signatures: `references/component-signatures.md`.
   - Exact `self.ctx` capability methods, method signatures, and manifest capability names: `references/sdk-methods.md`.
   - Migration from old plugin system: `references/migration.md`.
   - Debug/test/load problem: `references/testing-debugging.md`.
3. Implement close to existing project style. Use `MaiBot/plugins/hello_world_plugin` as the local style anchor.
4. Update `_manifest.json` capabilities when the plugin uses `self.ctx.*` features such as `send.text`, `emoji.get_random`, `config.get`, `llm.generate`, or `gateway.route_message`.
5. Add or update `config_model` and `config.toml` only when configuration is needed. Prefer strong typed `PluginConfigBase` models for new plugins.
6. Validate with the most focused available checks:
   - Syntax/import check for the plugin.
   - SDK tests if changing SDK code.
   - Main project plugin load or targeted tests if available.

## Design Rules

- Prefer `@Tool` over legacy `@Action` for new behavior. `Action` is retained as a compatibility entry and is converted internally to Tool metadata.
- Do not directly call host internals. Use `self.ctx` capability proxies.
- Avoid blocking operations inside async handlers; use async libraries or `asyncio.to_thread` for unavoidable blocking work.
- Make Tool descriptions useful to the LLM: include when to use the tool, required context, parameter meanings, and return semantics.
- Make Command regexes anchored and explicit. Read `matched_groups` from `kwargs` when named groups are used.
- Keep state on the plugin instance only for runtime cache/state. Persist durable data through `ctx.db` or explicit files only when the plugin design calls for it.
- Use `self.ctx.logger` for logs. The old async logging API is removed.
- For message models, copy dictionaries before mutation when you need to modify message content.

## Common Return Shapes

- `@Tool`: return a dict, commonly `{"success": True, "message": "...", ...}` or `{"name": "...", "content": "..."}`.
- `@Command`: existing examples return `(success: bool, message: str, show_to_user: bool/int)`.
- `@EventHandler`: follow the guide and existing examples for tuple shape; keep no-op handlers returning a successful continuation.
- `@MessageGateway`: return a dict with at least `success`; include `external_message_id` when available.
- `@LLMProvider`: follow the SDK guide exactly for request/response fields and manifest declarations.

## Reference Routing

- Read `references/scaffolding.md` before creating a new plugin folder, manifest, config model, or README.
- Read `references/components-and-capabilities.md` when selecting decorators or using `self.ctx`.
- Read `references/component-signatures.md` when implementing `@API`, `@Tool`, `@Command`, `@EventHandler`, `@HookHandler`, `@MessageGateway`, `@LLMProvider`, legacy `@Action`, config models, or dynamic APIs.
- Read `references/sdk-methods.md` when using a specific `self.ctx` method or updating `_manifest.json` capability declarations.
- Read `references/migration.md` before changing legacy plugins that import `src.plugin_system`, use `BasePlugin`, `register_plugin`, `BaseAction`, `BaseCommand`, `ConfigField`, `WorkflowStep`, or direct `src.*` APIs.
- Read `references/testing-debugging.md` before claiming a plugin loads, before changing SDK code, or when diagnosing reload/runtime failures.

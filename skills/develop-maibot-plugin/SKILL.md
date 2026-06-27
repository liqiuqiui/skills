---
name: develop-maibot-plugin
description: Use when creating, modifying, migrating, debugging, validating, or packaging MaiBot plugins with maibot-plugin-sdk; when prompts mention 麦麦/MaiBot 插件, a plugins directory, _manifest.json, config.toml, Tool/Command/EventHandler/HookHandler/API/MessageGateway/LLMProvider, src.plugin_system migration, plugin loading, or plugin runtime failures.
---

# MaiBot Plugin Development

Use this skill to build plugins for the local MaiBot workspace. Treat local code as the contract and online docs as reference only. If docs and code disagree, follow code.

- Main project: use the MaiBot path supplied by the user; if none is supplied, discover it from the plugin path.
- Plugin SDK: use the SDK source actually imported by the current MaiBot environment, usually under the main project's `.venv`.
- Local SDK guide: `<sdk-dir>/docs/guide.md`
- SDK migration guide: `<sdk-dir>/docs/migration-guide.md`
- Example plugin: `<maibot-dir>/plugins/hello_world_plugin/`
- Manifest schema: `<maibot-dir>/plugins/_manifest.schema.json`
- Remote SDK repository, supplementary only: `https://github.com/Mai-with-u/maibot-plugin-sdk/tree/main`
- Remote MaiBot repository, supplementary only: `https://github.com/Mai-with-u/MaiBot`
- Online plugin docs, lowest-priority reference only: `https://github.com/Mai-with-u/docs/tree/main/develop/plugin-dev`

## Source Priority

Use this order when facts conflict:

1. Current development environment MaiBot source code.
2. SDK source imported by that MaiBot environment, especially the package visible from `<maibot-dir>/.venv`.
3. Any separate local SDK checkout supplied by the user.
4. Remote MaiBot and SDK repositories.
5. Online plugin docs.

Plugin development depends on the main program's runtime and loader behavior, so do not design only from SDK docs or remote repositories. Always verify against the current MaiBot source and the SDK version that this MaiBot environment actually imports.

## First Moves

Before editing, establish the real local API surface:

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
SDK_PACKAGE_DIR="$("$MAIBOT_DIR/.venv/bin/python" - <<'PY'
import inspect
import maibot_sdk
from pathlib import Path
print(Path(inspect.getfile(maibot_sdk)).resolve().parent)
PY
)"
SDK_DIR="${SDK_DIR:-$(cd "$SDK_PACKAGE_DIR/.." && pwd -P)}"
rg --files "$MAIBOT_DIR/plugins" "$SDK_PACKAGE_DIR" "$SDK_DIR/docs" | sort
sed -n '1,320p' "$MAIBOT_DIR/plugins/hello_world_plugin/plugin.py"
sed -n '1,260p' "$MAIBOT_DIR/plugins/hello_world_plugin/_manifest.json"
sed -n '1,220p' "$SDK_PACKAGE_DIR/__init__.py"
sed -n '1,260p' "$MAIBOT_DIR/plugins/_manifest.schema.json"
```

If `<maibot-dir>/.venv/bin/python` does not exist, inspect the project files to find the active virtual environment or Python interpreter before relying on any SDK checkout.

Then read only the references that match the job:

- New plugin/folder/manifest/config: `references/scaffolding.md`
- Decorator selection and `self.ctx` capabilities: `references/components-and-capabilities.md`
- Exact decorator/config signatures: `references/component-signatures.md`
- Exact capability methods and manifest capability names: `references/sdk-methods.md`
- Old `src.plugin_system` migration: `references/migration.md`
- Load/reload/runtime failures or completion claims: `references/testing-debugging.md`

## Choose The Shape

- Ordinary user-facing ability: `@Tool` for model-invoked actions, `@Command` for explicit slash/regex commands.
- Passive reaction or pipeline observation: `@EventHandler`.
- Named pipeline extension with ordering/error policy: `@HookHandler`.
- Plugin-to-plugin callable surface: `@API(public=True)` plus `self.ctx.api.call`.
- External platform bridge: `@MessageGateway` plus `self.ctx.gateway.update_state` and `route_message`.
- Custom model provider: manifest `llm_providers` plus `@LLMProvider`.

Prefer `@Tool` over legacy `@Action` for new behavior. `Action` exists for migration compatibility and is internally converted to Tool metadata. `WorkflowStep` raises at runtime; migrate it to `HookHandler`.

## Required Contract

Every SDK plugin needs:

- Folder under `<maibot-dir>/plugins/<plugin_name>/`.
- `plugin.py` entry file.
- One `MaiBotPlugin` subclass.
- Async lifecycle methods: `on_load`, `on_unload`, `on_config_update`.
- Module-level `create_plugin()` returning an instance with no arguments.
- Usually `_manifest.json`; follow `<maibot-dir>/plugins/_manifest.schema.json`.

Minimal command/tool skeleton:

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
            self.ctx.logger.info("Config updated: version=%s", version)
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

1. Classify the task: new plugin, existing plugin change, migration, runtime debugging, SDK/runtime change, or packaging.
2. Inspect the target plugin and local SDK/source files before choosing APIs.
3. Implement in the existing style. Use `hello_world_plugin` as a style anchor, but modernize new behavior to `Tool` rather than copying old `Action`.
4. Keep plugin code isolated from host internals. New plugin code should import from `maibot_sdk` and ordinary third-party libraries, not `MaiBot/src/*` or `src.*`.
5. Update `_manifest.json` using the schema, including exact capability strings for each `self.ctx.*` call.
6. Add `config_model` and `config.toml` only when configuration is needed. Prefer typed `PluginConfigBase` models for new configurable plugins.
7. Validate with the most focused available checks before claiming success.

## Design Rules

- Do not directly call host internals. Use `self.ctx` capability proxies.
- Avoid blocking operations inside async handlers; use async libraries or `asyncio.to_thread` for unavoidable blocking work.
- Make Tool descriptions useful to the model: include when to use the tool, required context, parameter meanings, and return semantics.
- Make Command regexes anchored and explicit. Read `matched_groups` from `kwargs` when named groups are used.
- Keep state on the plugin instance only for runtime cache/state. Persist durable data through `ctx.db` or explicit files only when the plugin design calls for it.
- Use `self.ctx.logger` for logs. The old async logging API is removed.
- Use `self.ctx.paths.data_dir` and `runtime_dir` for plugin-owned files instead of writing into arbitrary host paths.
- For message dictionaries, defensive-check keys and copy before mutation when modifying message content.

## Common Return Shapes

- `@Tool`: return a dict, commonly `{"success": True, "message": "...", ...}` or `{"name": "...", "content": "..."}`.
- `@Command`: existing examples return `(success: bool, message: str, show_to_user: bool | int)`.
- `@EventHandler`: follow the guide and existing examples for tuple shape; keep no-op handlers returning a successful continuation.
- `@MessageGateway`: return a dict with at least `success`; include `external_message_id` when available.
- `@LLMProvider`: follow the SDK guide exactly for request/response fields and manifest declarations.

## Validation Standard

Before reporting a plugin is done or loads:

- Run a syntax/import check for the edited plugin.
- Instantiate `create_plugin()` and inspect collected components when the SDK is importable.
- Validate `_manifest.json` against `<maibot-dir>/plugins/_manifest.schema.json` when a manifest was changed.
- Run SDK or MaiBot targeted tests if SDK/runtime code changed.
- Report exactly which checks ran and what passed. If dependencies block a check, say so and include the strongest check that did run.

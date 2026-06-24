# Component Signatures

Use this reference when implementing or migrating MaiBot SDK components. It is based on local `maibot-plugin-sdk` version 2.5.4.

## Imports

```python
from maibot_sdk import (
    API,
    Action,
    Command,
    EventHandler,
    Field,
    HookHandler,
    LLMProvider,
    LLMProviderBase,
    MaiBotPlugin,
    MessageGateway,
    PluginConfigBase,
    Tool,
)
from maibot_sdk.types import (
    ActivationType,
    ChatMode,
    ErrorPolicy,
    EventType,
    HookMode,
    HookOrder,
    ToolParameterInfo,
    ToolParamType,
)
```

`WorkflowStep` still exists as an import name but raises at runtime. Treat it as removed and migrate to `HookHandler`.

## Plugin Base Contract

Every SDK plugin should expose:

```python
class MyPlugin(MaiBotPlugin):
    async def on_load(self) -> None: ...
    async def on_unload(self) -> None: ...
    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None: ...


def create_plugin() -> MyPlugin:
    return MyPlugin()
```

`create_plugin()` receives no arguments. Put initialization that needs `self.ctx` in `on_load()`, not in `__init__()`.

Useful base APIs:

- `self.ctx`: injected `PluginContext`.
- `self.config`: validated config object, only when `config_model` is declared.
- `get_default_config()`: generated defaults from `config_model`.
- `get_webui_config_schema(...)`: generated WebUI schema from `config_model`.
- `get_components()`: collected decorated components plus dynamic APIs.
- `get_llm_providers()`: collected `@LLMProvider` declarations.
- `register_dynamic_api(...)`, `unregister_dynamic_api(...)`, `sync_dynamic_apis(...)`: maintain runtime API declarations.

## API

Signature:

```python
@API(name: str, description: str = "", version: str = "1", public: bool = False, **metadata)
```

Use `@API(public=True)` when other plugins should call your plugin via `self.ctx.api.call(...)`. Private APIs can still be useful for internal host-side registration but are not generally visible to other plugins.

Example:

```python
@API("sum_numbers", description="计算整数和", version="1", public=True)
async def sum_numbers(self, a: int, b: int) -> dict[str, int]:
    return {"result": a + b}
```

Dynamic APIs:

```python
component = self.register_dynamic_api(
    "runtime_tool",
    self.handle_runtime_tool,
    description="运行时动态 API",
    version="1",
    public=True,
)
await self.sync_dynamic_apis()
```

Use dynamic APIs for externally backed capabilities that appear/disappear while the plugin is running.

## Tool

Signature:

```python
@Tool(
    name: str,
    description: str = "",
    brief_description: str = "",
    detailed_description: str = "",
    parameters: list[ToolParameterInfo] | dict[str, Any] | None = None,
    **metadata,
)
```

Use `@Tool` for LLM-invoked behavior. Prefer explicit parameter schemas and descriptions that tell the model when the tool is useful.

Typed parameters:

```python
@Tool(
    "lookup_profile",
    brief_description="查询指定用户资料",
    parameters=[
        ToolParameterInfo(name="platform", param_type=ToolParamType.STRING, description="平台名", required=True),
        ToolParameterInfo(name="user_id", param_type=ToolParamType.STRING, description="平台用户 ID", required=True),
    ],
)
async def lookup_profile(self, platform: str, user_id: str, **kwargs):
    ...
```

Dict parameters:

```python
@Tool(
    "search",
    parameters={
        "query": {"type": "string", "description": "关键词", "required": True},
        "limit": {"type": "integer", "description": "返回数量", "default": 5},
    },
)
```

Common return shape:

```python
return {"success": True, "message": "已完成", "data": {...}}
```

## Command

Signature:

```python
@Command(name: str, description: str = "", pattern: str = "", aliases: list[str] | None = None, **metadata)
```

Use `@Command` for explicit text commands. Keep regex patterns anchored and read named captures from `kwargs["matched_groups"]` when provided.

```python
@Command("set_mode", description="设置模式", pattern=r"^/mode\s+(?P<mode>\w+)$", aliases=["/m"])
async def set_mode(self, stream_id: str = "", **kwargs):
    mode = ((kwargs.get("matched_groups") or {}).get("mode") or "").strip()
    if not mode:
        return False, "用法：/mode <mode>", True
    await self.ctx.send.text(f"模式已切换为 {mode}", stream_id)
    return True, f"模式已切换为 {mode}", True
```

## EventHandler

Signature:

```python
@EventHandler(
    name: str,
    description: str = "",
    event_type: EventType = EventType.ON_MESSAGE,
    intercept_message: bool = False,
    weight: int = 0,
    **metadata,
)
```

Use `intercept_message=True` only when the handler must block the message chain and return a decision synchronously. Higher `weight` runs earlier.

Event types from SDK:

- `EventType.ON_START`
- `EventType.ON_STOP`
- `EventType.ON_MESSAGE_PRE_PROCESS`
- `EventType.ON_MESSAGE`
- `EventType.ON_PLAN`
- `EventType.POST_LLM`
- `EventType.AFTER_LLM`
- `EventType.POST_SEND_PRE_PROCESS`
- `EventType.POST_SEND`
- `EventType.AFTER_SEND`

Example:

```python
@EventHandler("message_logger", event_type=EventType.ON_MESSAGE)
async def message_logger(self, message=None, stream_id: str = "", **kwargs):
    if isinstance(message, dict):
        self.ctx.logger.info("message=%s", message.get("plain_text") or message.get("raw_message"))
    return True, True, None, None, None
```

## HookHandler

Signature:

```python
@HookHandler(
    hook: str,
    *,
    name: str = "",
    description: str = "",
    mode: HookMode = HookMode.BLOCKING,
    order: HookOrder = HookOrder.NORMAL,
    timeout_ms: int = 0,
    error_policy: ErrorPolicy = ErrorPolicy.SKIP,
    **metadata,
)
```

Use `HookMode.OBSERVE` for non-mutating observers. Use `HookMode.BLOCKING` when the result affects pipeline flow. Order options are `HookOrder.EARLY`, `HookOrder.NORMAL`, `HookOrder.LATE`. Error policies are `ErrorPolicy.ABORT`, `ErrorPolicy.SKIP`, `ErrorPolicy.LOG`.

```python
@HookHandler(
    "heart_fc.heart_flow_cycle_start",
    name="cycle_start_guard",
    mode=HookMode.BLOCKING,
    order=HookOrder.EARLY,
)
async def cycle_start_guard(self, **kwargs):
    return {"action": "continue", "modified_kwargs": kwargs}
```

## MessageGateway

Signature:

```python
@MessageGateway(
    route_type: str,
    *,
    name: str = "",
    description: str = "",
    platform: str = "",
    protocol: str = "",
    account_id: str = "",
    scope: str = "",
    **metadata,
)
```

`route_type` accepts `send`, `receive`, `recv`, `recive`, or `duplex`. A gateway must report runtime readiness through `ctx.gateway.update_state(...)`; declaration alone is not enough.

Outbound handler:

```python
@MessageGateway(route_type="duplex", name="qq_gateway", platform="qq", protocol="napcat")
async def send_to_platform(self, message: dict, route: dict | None = None, metadata: dict | None = None, **kwargs):
    return {"success": True, "external_message_id": "platform-msg-id"}
```

Inbound routing:

```python
await self.ctx.gateway.route_message(
    "qq_gateway",
    message_dict,
    route_metadata={"self_id": "10001"},
    external_message_id="platform-msg-id",
    dedupe_key="platform-msg-id",
)
```

## LLMProvider

Signature:

```python
@LLMProvider(
    client_type: str,
    *,
    name: str = "",
    description: str = "",
    version: str = "1.0.0",
    **metadata,
)
```

Provider plugins must also declare the same `client_type` in `_manifest.json` top-level `llm_providers`. Do not put handler names in manifest provider entries; the decorator supplies the handler.

```python
@LLMProvider("example.provider", name="Example Provider", description="示例 LLM Provider")
async def handle_provider_request(self, request: dict, **kwargs):
    return {"success": True, "content": "...", "model": request.get("model", "")}
```

`LLMProviderBase` is a recommended helper base class, but registration is driven by `@LLMProvider`.

## Action Compatibility

Signature:

```python
@Action(
    name: str,
    description: str = "",
    activation_type: ActivationType = ActivationType.ALWAYS,
    activation_keywords: list[str] | None = None,
    activation_probability: float = 1.0,
    chat_mode: ChatMode = ChatMode.NORMAL,
    action_parameters: dict[str, Any] | None = None,
    action_require: list[str] | None = None,
    associated_types: list[str] | None = None,
    parallel_action: bool = False,
    action_prompt: str = "",
    **metadata,
)
```

Use only for migration or compatibility. New behavior should use `@Tool`.

Activation types:

- `ActivationType.NEVER`
- `ActivationType.ALWAYS`
- `ActivationType.RANDOM`
- `ActivationType.KEYWORD`

Chat modes:

- `ChatMode.FOCUS`
- `ChatMode.NORMAL`
- `ChatMode.PRIORITY`
- `ChatMode.ALL`

## Config Model

Use typed config for new plugins with settings:

```python
class PluginSection(PluginConfigBase):
    __ui_label__ = "插件"
    __ui_icon__ = "package"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="0.1.0", description="配置版本")


class MyConfig(PluginConfigBase):
    plugin: PluginSection = Field(default_factory=PluginSection)


class MyPlugin(MaiBotPlugin):
    config_model = MyConfig
```

Useful field metadata:

- `json_schema_extra={"label": "..."}`
- `placeholder`
- `hint`
- `x-widget`
- `x-icon`
- `depends_on`
- `depends_value`
- `step`
- `i18n`

Plugin self config changes arrive via `on_config_update(scope="self", ...)`. Global subscriptions use `config_reload_subscriptions = {ON_BOT_CONFIG_RELOAD, ON_MODEL_CONFIG_RELOAD}`.

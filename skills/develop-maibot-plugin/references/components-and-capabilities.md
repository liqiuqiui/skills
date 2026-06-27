# Components And Capabilities

Use this reference when selecting decorators or calling `self.ctx`.

## Component Selection

| Need | Use |
|---|---|
| LLM should decide when to call plugin behavior | `@Tool` |
| User explicitly types a command or slash-style instruction | `@Command` |
| Plugin reacts to Host lifecycle/message events | `@EventHandler` |
| Plugin extends a named pipeline hook with order/error policy | `@HookHandler` |
| Other plugins should call this plugin | `@API(public=True)` |
| External platform integration or message bridge | `@MessageGateway` |
| New LLM provider/client type | `_manifest.json` `llm_providers` plus `@LLMProvider` |
| Old plugin compatibility only | `@Action` |

For new work, avoid `@Action` unless preserving old behavior. SDK 2.x converts it to Tool metadata internally.
`WorkflowStep` is removed and raises at runtime; use `@HookHandler`.

## Tool Pattern

```python
from maibot_sdk import Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType


@Tool(
    "lookup_profile",
    brief_description="查询指定用户的资料并在对话需要时总结",
    detailed_description="参数说明：\n- platform：string，必填。平台名。\n- user_id：string，必填。平台用户 ID。",
    parameters=[
        ToolParameterInfo(name="platform", param_type=ToolParamType.STRING, description="平台名", required=True),
        ToolParameterInfo(name="user_id", param_type=ToolParamType.STRING, description="平台用户 ID", required=True),
    ],
)
async def handle_lookup_profile(self, platform: str, user_id: str, **kwargs):
    del kwargs
    person_id = await self.ctx.person.get_id(platform, user_id)
    if not person_id:
        return {"success": False, "message": "未找到用户"}
    nickname = await self.ctx.person.get_value(person_id, "nickname")
    return {"success": True, "nickname": nickname}
```

Tool parameters can also be JSON-schema-like dictionaries; use `ToolParameterInfo` when staying close to local examples.

## Command Pattern

```python
@Command("set_mode", description="设置模式", pattern=r"^/mode\s+(?P<mode>\w+)$", aliases=["/m"])
async def handle_set_mode(self, stream_id: str = "", **kwargs):
    matched_groups = kwargs.get("matched_groups")
    mode = str((matched_groups or {}).get("mode") or "").strip()
    if not mode:
        return False, "用法：/mode <mode>", True
    await self.ctx.send.text(f"模式已切换为 {mode}", stream_id)
    return True, f"模式已切换为 {mode}", True
```

Keep regexes anchored. Provide fallback parsing only when existing Host behavior requires it.

## EventHandler Pattern

```python
from maibot_sdk import EventHandler
from maibot_sdk.types import EventType


@EventHandler("message_logger", description="记录收到的文本消息", event_type=EventType.ON_MESSAGE)
async def handle_message(self, message=None, stream_id: str = "", **kwargs):
    del stream_id
    del kwargs
    if isinstance(message, dict):
        self.ctx.logger.info("message=%s", message.get("plain_text") or message.get("raw_message"))
    return True, True, None, None, None
```

## HookHandler Notes

Use `@HookHandler` when the SDK guide names a hook point and the plugin must run before/after other hook subscribers. Choose `HookMode.OBSERVE` for non-mutating observers and `HookMode.BLOCKING` only when the hook must affect flow. Set `ErrorPolicy.LOG` or `SKIP` for non-critical hooks; reserve abort behavior for hard requirements.

## MessageGateway Notes

Gateway plugins must both declare `@MessageGateway` and report runtime readiness:

- On load/connect: `await self.ctx.gateway.update_state(gateway_name="...", ready=True, platform="...", account_id="...", scope="...")`
- On unload/disconnect: `await self.ctx.gateway.update_state(gateway_name="...", ready=False)`
- For inbound platform messages: `await self.ctx.gateway.route_message(...)`

Only `route_type="receive"` or `"duplex"` gateways can inject inbound messages. Only `route_type="send"` or `"duplex"` gateways can be selected for outbound sends.

## LLMProvider Notes

Provider plugins need two matching declarations:

1. `_manifest.json` top-level `llm_providers` entry with the static `client_type`.
2. A plugin method decorated with `@LLMProvider("same.client_type")`.

If two plugins declare the same `client_type`, the Host blocks the conflict. Do not put handler names in manifest provider declarations unless the current local guide explicitly requires it.

## Capability Map

`self.ctx` exposes:

- `api`: list/get/call plugin APIs, dynamic API sync.
- `gateway`: route inbound messages and update gateway state.
- `send`: text, image, emoji, forward, hybrid, command, custom messages.
- `db`: query/get/save/delete/count.
- `llm`: generate text, tool generation, embeddings, audio transcription.
- `config`: raw config reads.
- `emoji`: emoji pack lookup and random retrieval.
- `message`: history query and readable message building.
- `frequency`: talk frequency reads/adjustments.
- `component`: plugin/component management and runtime status.
- `chat`: stream lookup and session opening.
- `person`: person ID and value lookup.
- `render`: HTML to PNG rendering.
- `knowledge`: LPMM knowledge search.
- `tool`: Host tool definition lookup.
- `statistics`: local model/token/message/tool/online-time trend summaries.
- `maisaka`: active task and context APIs.
- `logger`: standard `logging.Logger`.
- `paths`: plugin-owned `data_dir` and `runtime_dir`.

Manifest capability names usually match the RPC string, not always the Python attribute name. For example, calls through `self.ctx.db.*` require `database.*` declarations in `_manifest.json`. Inspect `<maibot-dir>/plugins/_manifest.schema.json`, `<sdk-dir>/maibot_sdk/context.py`, and `<sdk-dir>/maibot_sdk/capabilities/*.py` for exact method signatures before implementing an unfamiliar call.

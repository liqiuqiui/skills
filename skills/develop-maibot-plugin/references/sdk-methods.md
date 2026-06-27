# SDK Methods

Use this method-level reference when a plugin needs a specific SDK capability. It reflects the SDK shape observed when this skill was written, but the current MaiBot source, its manifest schema, and the `maibot_sdk` package imported by its active Python environment are authoritative. For unfamiliar calls, inspect the imported SDK package source, any active `<sdk-dir>` checkout, and `<maibot-dir>/plugins/_manifest.schema.json`.

## Manifest Capability Names

When a plugin calls `self.ctx.<capability>`, update `_manifest.json` with matching capability strings where the Host enforces them. Common names:

- `api.call`, `api.get`, `api.list`, `api.replace_dynamic`
- `gateway.route_message`, `gateway.update_state`
- `send.text`, `send.emoji`, `send.image`, `send.forward`, `send.hybrid`, `send.command`, `send.custom`
- `database.query`, `database.save`, `database.get`, `database.delete`, `database.count`
- `llm.generate`, `llm.generate_with_tools`, `llm.embed`, `llm.transcribe_audio`, `llm.get_available_models`
- `config.get`, `config.get_plugin`, `config.get_all`
- `emoji.get_random`, `emoji.get_by_description`, `emoji.get_count`, `emoji.get_info`, `emoji.get_emotions`, `emoji.get_all`, `emoji.register`, `emoji.delete`
- `message.get_recent`, `message.get_by_id`, `message.build_readable`, `message.get_by_time`, `message.get_by_time_in_chat`, `message.count_new`
- `frequency.get_current_talk_value`, `frequency.set_adjust`, `frequency.get_adjust`
- `component.get_all_plugins`, `component.get_plugin_info`, `component.get_plugin_config_schema`, `component.list_loaded_plugins`, `component.list_registered_plugins`, `component.enable`, `component.disable`, `component.load_plugin`, `component.unload_plugin`, `component.reload_plugin`
- `chat.get_all_streams`, `chat.get_group_streams`, `chat.get_private_streams`, `chat.get_stream_by_group_id`, `chat.get_stream_by_user_id`, `chat.open_session`
- `person.get_id`, `person.get_value`, `person.get_id_by_name`
- `render.html2png`
- `knowledge.search`
- `tool.get_definitions`
- `statistics.local.models`, `statistics.local.model_trend`, `statistics.local.token_trend`, `statistics.local.token_distribution`, `statistics.local.message_trend`, `statistics.local.tool_trend`, `statistics.local.online_time_trend`
- `maisaka.context.append`, `maisaka.proactive.trigger`

Note the naming distinction: plugin code calls `self.ctx.db.*`, but the manifest declares `database.*`.

## `ctx.api`

- `await self.ctx.api.call(api_name: str, *, version: str = "", **kwargs)` - call another plugin's public API. `api_name` may be `plugin_id.api_name` or a unique short name.
- `await self.ctx.api.get(api_name: str, *, version: str = "")` - get one visible API's metadata.
- `await self.ctx.api.list(*, plugin_id: str = "")` - list visible APIs, optionally filtered by provider plugin.
- `await self.ctx.api.replace_dynamic_apis(apis: list[dict], *, offline_reason: str = "动态 API 已下线")` - replace currently exposed dynamic APIs.

Prefer static `@API(public=True)` for stable APIs. Use dynamic APIs for runtime-backed tool sets.

## `ctx.gateway`

- `await self.ctx.gateway.route_message(gateway_name: str, message: dict, *, route_metadata: dict | None = None, external_message_id: str = "", dedupe_key: str = "") -> bool`
- `await self.ctx.gateway.update_state(gateway_name: str, *, ready: bool, platform: str = "", account_id: str = "", scope: str = "", metadata: dict | None = None)`
- `await self.ctx.gateway.receive_external_message(message: dict, *, gateway_name: str, route_metadata: dict | None = None, external_message_id: str = "", dedupe_key: str = "")` - compatibility alias for `route_message`.
- `await self.ctx.gateway.update_runtime_state(*, gateway_name: str, connected: bool, platform: str = "", account_id: str = "", scope: str = "", metadata: dict | None = None)` - compatibility alias for `update_state`.

Use only from plugins that declare `@MessageGateway`. Report `ready=True` after the external link is actually usable, and `ready=False` on disconnect/unload.

## `ctx.send`

- `await self.ctx.send.text(text: str, stream_id: str, **kwargs)` - send text.
- `await self.ctx.send.emoji(emoji_data: str, stream_id: str, **kwargs)` - send emoji base64.
- `await self.ctx.send.image(image_data: str, stream_id: str, **kwargs)` - send image base64.
- `await self.ctx.send.forward(messages: list[dict], stream_id: str, **kwargs)` - send forward messages.
- `await self.ctx.send.hybrid(segments: list[dict], stream_id: str, **kwargs)` - send mixed text/image segments.
- `await self.ctx.send.command(command: str, stream_id: str, **kwargs)` - send command content.
- `await self.ctx.send.custom(custom_type: str, data: Any, stream_id: str, **kwargs)` - send custom message; SDK emits old and new field aliases.

`send.*` methods usually return a boolean-like Host result after SDK normalization. Always handle failed sends when the target stream may be missing.

## `ctx.db`

- `await self.ctx.db.query(model_name: str, query_type: str = "get", data: dict | None = None, filters: dict | None = None, order_by: list[str] | None = None, limit: int | None = None, single_result: bool = False)`
- `await self.ctx.db.save(model_name: str, data: dict, key_field: str = "id", key_value: Any = None)`
- `await self.ctx.db.get(model_name: str, filters: dict | None = None, limit: int | None = None, order_by: str | list[str] | None = None, single_result: bool = False)`
- `await self.ctx.db.delete(model_name: str, filters: dict)`
- `await self.ctx.db.count(model_name: str, filters: dict | None = None) -> int`

Model names must match Host database model names. Do not assume plugin-local arbitrary tables exist unless the Host supports them.

## `ctx.llm`

- `await self.ctx.llm.generate(prompt: str | list[dict], model: str = "", temperature: float | None = None, max_tokens: int | None = None, **kwargs) -> dict`
- `await self.ctx.llm.generate_with_tools(prompt: str | list[dict], tools: list[dict], model: str = "", temperature: float | None = None, max_tokens: int | None = None, **kwargs) -> dict`
- `await self.ctx.llm.embed(text: str | None = None, *, texts: list[str] | None = None, task_name: str = "embedding", model: str = "", model_name: str = "", max_concurrent: int | None = None, **kwargs) -> dict`
- `await self.ctx.llm.transcribe_audio(audio: bytes | str | None = None, *, audio_base64: str = "", voice_base64: str = "", task_name: str = "voice", model: str = "", model_name: str = "", **kwargs) -> dict`
- `await self.ctx.llm.get_available_models() -> list[str]`

`generate()` and `generate_with_tools()` normalize common fields such as `response`, `reasoning`, `model`, and `tool_calls`.

## `ctx.config`

- `await self.ctx.config.get(key: str, default: Any = None)` - dot-path config lookup.
- `await self.ctx.config.get_plugin(plugin_name: str | None = None) -> dict`
- `await self.ctx.config.get_all() -> dict`

For new plugins with structured settings, prefer `config_model` and `self.config`. Use `ctx.config` for raw or cross-plugin config reads.

## `ctx.emoji`

- `await self.ctx.emoji.get_random(count: int = 5)`
- `await self.ctx.emoji.get_by_description(description: str, limit: int = 5)`
- `await self.ctx.emoji.get_count()`
- `await self.ctx.emoji.get_info()`
- `await self.ctx.emoji.get_emotions()`
- `await self.ctx.emoji.get_all()`
- `await self.ctx.emoji.register_emoji(emoji_base64: str)`
- `await self.ctx.emoji.delete_emoji(emoji_hash: str, keep_desc: bool | None = None)`

`keep_desc=True` deletes the file but keeps description cache; `False` deletes both; `None` lets Host decide.

## `ctx.message`

- `await self.ctx.message.get_recent(chat_id: str, limit: int = 10)`
- `await self.ctx.message.get_by_id(message_id: str, *, chat_id: str = "", stream_id: str = "", include_binary_data: bool = False)`
- `await self.ctx.message.build_readable(messages: Any, **kwargs)`
- `await self.ctx.message.get_by_time(start_time: str, end_time: str, **kwargs)`
- `await self.ctx.message.get_by_time_in_chat(chat_id: str, start_time: str, end_time: str, **kwargs)`
- `await self.ctx.message.count_new(chat_id: str, since: str)`

Use `build_readable()` before feeding history into LLM prompts.

## `ctx.frequency`

- `await self.ctx.frequency.get_current_talk_value(chat_id: str)`
- `await self.ctx.frequency.set_adjust(chat_id: str, value: float)`
- `await self.ctx.frequency.get_adjust(chat_id: str)`

Use for temporary speech-frequency influence, not durable behavior settings.

## `ctx.component`

- `await self.ctx.component.get_all_plugins()`
- `await self.ctx.component.get_plugin_info(plugin_name: str)`
- `await self.ctx.component.get_plugin_config_schema(plugin_name: str)`
- `await self.ctx.component.list_loaded_plugins()`
- `await self.ctx.component.list_registered_plugins()`
- `await self.ctx.component.enable_component(name: str, component_type: str, scope: str = "global", stream_id: str = "", version: str = "")`
- `await self.ctx.component.disable_component(name: str, component_type: str, scope: str = "global", stream_id: str = "", version: str = "")`
- `await self.ctx.component.load_plugin(plugin_name: str)`
- `await self.ctx.component.unload_plugin(plugin_name: str)`
- `await self.ctx.component.reload_plugin(plugin_name: str)`

Component type names are normalized to uppercase protocol values. `WorkflowStep` is removed; use `HOOK_HANDLER`.

The local manifest schema includes `component.update_plugin_config`, but the current SDK `ComponentCapability` does not expose a typed helper for it. Do not call it from plugin code unless you first verify a public SDK method in the local code.

## `ctx.chat`

- `await self.ctx.chat.get_all_streams(platform: str = "qq")`
- `await self.ctx.chat.get_group_streams(platform: str = "qq")`
- `await self.ctx.chat.get_private_streams(platform: str = "qq")`
- `await self.ctx.chat.get_stream_by_group_id(group_id: str, platform: str = "qq")`
- `await self.ctx.chat.get_stream_by_user_id(user_id: str, platform: str = "qq")`
- `await self.ctx.chat.open_session(platform: str = "qq", chat_type: str = "private", *, user_id: str = "", group_id: str = "", account_id: str = "", scope: str = "", **kwargs)`

Use `open_session()` before proactive sends when a stream may not already exist.

## `ctx.person`

- `await self.ctx.person.get_id(platform: str, user_id: str)`
- `await self.ctx.person.get_value(person_id: str, field_name: str)`
- `await self.ctx.person.get_id_by_name(person_name: str)`

Use `person_id` for internal person records, not platform IDs.

## `ctx.render`

- `await self.ctx.render.html2png(html: str, *, selector: str = "body", viewport: dict[str, int] | None = None, device_scale_factor: float = 2.0, full_page: bool = False, omit_background: bool = False, wait_until: str = "load", wait_for_selector: str = "", wait_for_timeout_ms: int = 0, render_timeout_ms: int = 0, allow_network: bool = False)`

Returns a render result usually containing `image_base64`, `mime_type`, `width`, and `height`. Use for card images, charts, leaderboards, and shareable visual summaries.

## `ctx.knowledge`

- `await self.ctx.knowledge.search(query: str, limit: int = 5)`

Use for LPMM knowledge search when plugin behavior needs context from the Host knowledge base.

## `ctx.tool`

- `await self.ctx.tool.get_definitions()`

Use for inspecting Host-visible LLM tool definitions.

## `ctx.statistics`

- `await self.ctx.statistics.local.models(days: int = 7, limit: int = 10)`
- `await self.ctx.statistics.local.model_trend(days: int = 7, bucket: str = "day", top_models: int = 10, metric: str = "token", module_name: str = "")`
- `await self.ctx.statistics.local.token_trend(days: int = 7, bucket: str = "day", group_by: str = "", top_items: int = 10)`
- `await self.ctx.statistics.local.token_distribution(days: int = 7, group_by: str = "model", top_items: int = 10)`
- `await self.ctx.statistics.local.message_trend(days: int = 7, bucket: str = "day", top_chats: int = 10)`
- `await self.ctx.statistics.local.tool_trend(days: int = 7, bucket: str = "day", top_tools: int = 10)`
- `await self.ctx.statistics.local.online_time_trend(days: int = 7, bucket: str = "day")`

Use for local observability plugins. Declare the matching `statistics.local.*` capability.

## `ctx.maisaka`

- `await self.ctx.maisaka.context.append(stream_id: str, segments: list[dict], *, visible_text: str = "", source_kind: str = "", message_id: str = "", **kwargs)`
- `await self.ctx.maisaka.proactive.trigger(stream_id: str, intent: str, *, reason: str = "", priority: str = "", metadata: dict | None = None, **kwargs)`
- `await self.ctx.maisaka.append_context(stream_id: str, segments: list[dict], **kwargs)` - compatibility shortcut.
- `await self.ctx.maisaka.trigger_proactive(stream_id: str, intent: str, **kwargs)` - compatibility shortcut.

`proactive.trigger()` needs an existing Host stream ID. If needed, call `ctx.chat.open_session()` first.

## `ctx.logger`

`self.ctx.logger` is a standard `logging.Logger` named `plugin.<plugin_id>`.

```python
self.ctx.logger.info("started")
self.ctx.logger.error("failed", exc_info=True)
```

The old async logging API is removed. Standard library logging is the intended interface.

## `ctx.paths`

`self.ctx.paths.data_dir` and `self.ctx.paths.runtime_dir` are `pathlib.Path` objects scoped to the plugin id. Use them for plugin-owned persistent data and temporary runtime files instead of writing into arbitrary project directories.

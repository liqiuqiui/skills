# Testing And Debugging MaiBot Plugins

Use this reference before claiming a plugin loads or when diagnosing runtime problems.

## Lightweight Checks

From the workspace root:

```bash
python3 -m compileall MaiBot/plugins/<plugin_name>
```

If the environment has the SDK import path available:

```bash
PYTHONPATH=maibot-plugin-sdk python3 - <<'PY'
import importlib.util
from pathlib import Path

path = Path("MaiBot/plugins/<plugin_name>/plugin.py")
spec = importlib.util.spec_from_file_location("plugin_under_test", path)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
plugin = mod.create_plugin()
print(type(plugin).__name__)
print([c.name for c in plugin.get_components()])
PY
```

Prefer the project's own test runner if it already has plugin runtime tests.

## SDK Checks

When changing `maibot-plugin-sdk` itself:

```bash
cd maibot-plugin-sdk
python3 -m pytest
python3 -m ruff check .
python3 -m mypy maibot_sdk
```

Use `uv run python ...` if the repository is already managed that way and dependencies are installed through uv. If only `python` is available in a target environment, using `python` instead of `python3` is fine.

## Main Project Checks

When changing MaiBot plugin runtime behavior, inspect `MaiBot/pyproject.toml` and existing test commands. Avoid inventing a broad test command if a targeted one exists. Useful searches:

```bash
rg -n "pytest|plugin|runtime|maibot_sdk|PluginRuntime|PluginLoader" MaiBot
```

## Runtime Debugging

For load/reload failures:

1. Check `_manifest.json` parse errors and version bounds.
2. Confirm `plugin.py` exists and exports `create_plugin()`.
3. Confirm lifecycle methods are implemented on the concrete subclass.
4. Confirm the plugin imports only `maibot_sdk` and available third-party dependencies.
5. Confirm declared capabilities cover actual `self.ctx` calls.
6. Check logs under `MaiBot/logs/` and search for the plugin id or class name.
7. Remember hot reload uses "validate new runner, then switch"; a failed reload should leave the old plugin instance active.

For handler failures:

- Log inputs with `self.ctx.logger.debug/info` instead of `print`.
- Validate that expected kwargs exist; command handlers often receive `stream_id`, `text`, and `matched_groups`.
- Defensive-check message dictionaries before reading fields like `plain_text`, `raw_message`, and `message_info`.
- For sending failures, check whether `stream_id` is present and whether `ctx.send.*` returns `False`.

## Verification Standard

Before reporting success, state exactly what was run and what passed. If a command cannot run because dependencies are missing, say that and include the next most useful check that did run.

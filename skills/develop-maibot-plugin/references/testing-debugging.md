# Testing And Debugging MaiBot Plugins

Use this reference before claiming a plugin loads or when diagnosing runtime problems.

## Lightweight Checks

Set `PLUGIN_DIR` to the target plugin folder. If `MAIBOT_DIR` is not supplied, derive it from the common layout where plugin folders live under `<maibot-dir>/plugins/`.

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
python3 -m compileall "$MAIBOT_DIR/plugins/<plugin_name>"
```

Use the SDK that the main program's current Python environment imports. Prefer `<maibot-dir>/.venv/bin/python`; if that interpreter does not exist, first inspect the project to find the active venv/interpreter.

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
MAIBOT_PYTHON="${MAIBOT_PYTHON:-$MAIBOT_DIR/.venv/bin/python}"
MAIBOT_DIR="$MAIBOT_DIR" "$MAIBOT_PYTHON" - <<'PY'
import importlib.util
import inspect
import os
from pathlib import Path

import maibot_sdk

print("maibot_sdk:", Path(inspect.getfile(maibot_sdk)).resolve())
path = Path(os.environ["MAIBOT_DIR"]) / "plugins/<plugin_name>/plugin.py"
spec = importlib.util.spec_from_file_location("plugin_under_test", path)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
plugin = mod.create_plugin()
print(type(plugin).__name__)
print([c.name for c in plugin.get_components()])
PY
```

If `_manifest.json` changed, validate it against the local schema:

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
MAIBOT_DIR="$MAIBOT_DIR" python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["MAIBOT_DIR"])
manifest = json.loads((root / "plugins/<plugin_name>/_manifest.json").read_text(encoding="utf-8"))
required = {
    "manifest_version", "version", "name", "description", "author", "license",
    "urls", "host_application", "sdk", "capabilities", "i18n", "id",
}
missing = sorted(required - set(manifest))
if missing:
    raise SystemExit(f"missing required manifest keys: {missing}")
print("manifest required keys ok")
PY
```

If `jsonschema` is installed, run full schema validation:

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
MAIBOT_DIR="$MAIBOT_DIR" python3 - <<'PY'
import json
import os
from pathlib import Path
from jsonschema import Draft7Validator

root = Path(os.environ["MAIBOT_DIR"])
schema = json.loads((root / "plugins/_manifest.schema.json").read_text(encoding="utf-8"))
manifest = json.loads((root / "plugins/<plugin_name>/_manifest.json").read_text(encoding="utf-8"))
errors = sorted(Draft7Validator(schema).iter_errors(manifest), key=lambda e: list(e.path))
if errors:
    for error in errors:
        path = ".".join(str(part) for part in error.path) or "<root>"
        print(f"{path}: {error.message}")
    raise SystemExit(1)
print("manifest ok")
PY
```

Prefer the project's own test runner if it already has plugin runtime tests.

## SDK Checks

When changing the SDK itself, first identify whether you are editing a checkout or the SDK package imported by the current MaiBot environment:

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
MAIBOT_PYTHON="${MAIBOT_PYTHON:-$MAIBOT_DIR/.venv/bin/python}"
SDK_PACKAGE_DIR="$("$MAIBOT_PYTHON" - <<'PY'
import inspect
import maibot_sdk
from pathlib import Path
print(Path(inspect.getfile(maibot_sdk)).resolve().parent)
PY
)"
cd "${SDK_DIR:-$(cd "$SDK_PACKAGE_DIR/.." && pwd -P)}"
python3 -m pytest
python3 -m ruff check .
python3 -m mypy maibot_sdk
```

Use `uv run python ...` if the repository is already managed that way and dependencies are installed through uv. If only `python` is available in a target environment, using `python` instead of `python3` is fine.

## Main Project Checks

When changing MaiBot plugin runtime behavior, inspect `<maibot-dir>/pyproject.toml` and existing test commands. Avoid inventing a broad test command if a targeted one exists. Useful searches:

```bash
PLUGIN_DIR="${PLUGIN_DIR:-MaiBot/plugins/<plugin_name>}"
MAIBOT_DIR="${MAIBOT_DIR:-$(cd "$PLUGIN_DIR/../.." && pwd -P)}"
rg -n "pytest|plugin|runtime|maibot_sdk|PluginRuntime|PluginLoader" "$MAIBOT_DIR"
```

## Runtime Debugging

For load/reload failures:

1. Check `_manifest.json` parse errors and version bounds.
2. Confirm `plugin.py` exists and exports `create_plugin()`.
3. Confirm lifecycle methods are implemented on the concrete subclass.
4. Confirm the plugin imports only `maibot_sdk` and available third-party dependencies.
5. Confirm declared capabilities cover actual `self.ctx` calls.
6. Check logs under `<maibot-dir>/logs/` and search for the plugin id or class name.
7. Remember hot reload uses "validate new runner, then switch"; a failed reload should leave the old plugin instance active.

For handler failures:

- Log inputs with `self.ctx.logger.debug/info` instead of `print`.
- Validate that expected kwargs exist; command handlers often receive `stream_id`, `text`, and `matched_groups`.
- Defensive-check message dictionaries before reading fields like `plain_text`, `raw_message`, and `message_info`.
- For sending failures, check whether `stream_id` is present and whether `ctx.send.*` returns `False`.

## Verification Standard

Before reporting success, state exactly what was run and what passed. If a command cannot run because dependencies are missing, say that and include the next most useful check that did run.

## Online Docs Check

Online docs are reference only. If needed, fetch with `curl` using browser-like headers, and keep local code authoritative:

```bash
curl -L --fail --compressed \
  -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  'https://github.com/Mai-with-u/docs/tree/main/develop/plugin-dev'
```

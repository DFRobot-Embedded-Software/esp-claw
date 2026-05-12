---
{
  "name": "http_server_lua_demo",
  "description": "Start a small Lua-hosted web page that shows Hello World and logs switch toggles from the browser.",
  "metadata": {
    "cap_groups": [
      "cap_lua"
    ],
    "manage_mode": "readonly"
  }
}
---

# HTTP Server Lua Demo

Use this skill when the user wants a simple Lua HTTP server demo page, a Hello World web UI, or a browser switch that calls back into Lua.

Run exactly one bundled Lua script asynchronously with the Lua script execution capability.

If script execution returns an error, report that error directly to the user.

## Script Args Schema

```json
{
  "type": "object",
  "properties": {
    "app_id": {
      "type": "string",
      "description": "Optional URL-safe app id. Defaults to lua_demo."
    },
    "web_root": {
      "type": "string",
      "description": "Optional absolute FatFS directory for static web files. Defaults to /fatfs/skills/http_server_lua_demo/assets."
    }
  }
}
```

## Tool Call Inputs

Default action:

```json
{
  "path": "{CUR_SKILL_DIR}/scripts/lua_demo_server.lua",
  "args": {
    "app_id": "lua_demo",
    "web_root": "{CUR_SKILL_DIR}/assets"
  }
}
```

## Recommended Flow

Run the bundled Lua script asynchronously so the HTTP callbacks stay alive:

- Script: `{CUR_SKILL_DIR}/scripts/lua_demo_server.lua`
- Capability: `lua_run_script_async`
- Timeout: `0`
- Name: `http_server_lua_demo`
- Exclusive: `http_server_lua_demo`
- Replace: `true`
- Args: optional object

Example args:

```json
{
  "app_id": "lua_demo",
  "web_root": "{CUR_SKILL_DIR}/assets"
}
```

After the script starts, open:

```text
/lua/lua_demo/
```

## Behavior

The script mounts the bundled `assets/` directory with `http_server` and registers:

- `GET /api/lua/lua_demo/state`
- `POST /api/lua/lua_demo/toggle`

The page displays "Hello World" and a switch. When the switch changes, the browser posts the new state to Lua, and Lua logs:

```text
[http_server_lua_demo] switch toggled: enabled=true
```

Stop the async Lua job when the demo page should be closed.

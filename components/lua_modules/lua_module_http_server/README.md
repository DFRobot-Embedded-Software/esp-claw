# Lua HTTP Server

This module lets a long-running Lua script publish static FatFS files and HTTP
callbacks through the existing edge_agent HTTP server.

## Example

```lua
local http = require("http_server")
local system = require("system")

local app = http.app("panel")
app:mount_static("/fatfs/www/panel")

app:get("/state", function(req)
  return {
    json = {
      ok = true,
      uptime = system.uptime(),
      method = req.method,
      path = req.path,
    },
  }
end)

app:post("/echo", function(req)
  return { json = { ok = true, body = req.body } }
end)

print(app:url())
app:serve_forever()
```

Run scripts that serve callbacks through `lua_run_script_async`, because
`serve_forever()` keeps the Lua state alive until the job is stopped.

## URL Space

- Static files: `/lua/<app_id>/...`
- Callback APIs: `/api/lua/<app_id>/...`

`app_id` may contain only letters, digits, `_`, and `-`.

## Packaged Skill Example

The repository includes a ready-to-run skill example:

```text
components/lua_modules/lua_module_http_server/skills/http_server_lua_demo/
```

It starts a background Lua web page at `/lua/lua_demo/`, shows "Hello World",
and logs every switch toggle from the browser in the Lua script output.

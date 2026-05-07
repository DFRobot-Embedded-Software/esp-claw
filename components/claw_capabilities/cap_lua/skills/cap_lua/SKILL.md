---
{
  "name": "cap_lua",
  "description": "Discover, read, run, inspect, and stop Lua scripts, including async Lua jobs.",
  "metadata": {
    "cap_groups": [
      "cap_lua"
    ],
    "manage_mode": "readonly"
  }
}
---

# Lua Script Operations

Use this skill for Lua scripts: discover scripts, read module docs, run scripts, and manage async jobs.

## Path Rules

There are two path namespaces. Do not mix them:

- Lua run paths: used by `lua_run_script` and `lua_run_script_async`
- File paths: used by `list_dir` and `read_file`

Rules:

- `builtin/test/` is for shipped examples, tests, and demos.
- `builtin/lib/` is for reusable Lua libraries. Read the matching `.md` guide before using a library.
- `docs/` is for module API docs.
- Treat `builtin/` as read-only unless the user explicitly asks to change it.
- Lua run tools can address managed Lua run paths and skill-owned absolute script paths, but user-facing behavior must use skill-owned scripts.
- `list_dir` returns file paths for reference discovery.
- Use managed Lua run paths such as `builtin/...` only for reading reference examples unless a specific skill explicitly instructs running one.
- Do not create or run `temp/...`, `user/...`, or ad hoc generated Lua paths for user-facing work.
- `lua_run_script` and `lua_run_script_async` must use the absolute skill script path from an active skill's instructions for user-facing work.
- `read_file` uses file paths, not Lua run paths.
- To run a managed script found by `list_dir`, remove exactly one leading `scripts/`.
- To read a skill-bundled Lua file, use `skills/<skill_id>/scripts/...`.
- Never call `read_file("scripts/scripts/...")`.
- Never pass a bare Lua run path directly to `read_file`.

Examples:

| Intent | Correct path |
| --- | --- |
| `list_dir` result | `scripts/builtin/test/abc.lua` |
| `lua_run_script` for listed managed script | `builtin/test/abc.lua` |
| `lua_run_script` path for user work | `{CUR_SKILL_DIR}/scripts/action.lua` |
| `lua_run_script_async` path for user work | `{CUR_SKILL_DIR}/scripts/action.lua` |
| `read_file` for listed script | `scripts/builtin/test/abc.lua` |
| `read_file` for library source | `scripts/builtin/lib/arg_schema.lua` |
| `read_file` for library guide | `scripts/builtin/lib/arg_schema.md` |
| `read_file` for module doc | `scripts/docs/lua_module_display.md` |
| `read_file` for skill script | `skills/skill_id/scripts/abc.lua` |

## Documentation Read Strategy

For Lua debugging, hardware control, or reference inspection, gather likely needed references before running code.
Prefer several consecutive `read_file` tool calls in the same step instead of reading one document, reasoning, then coming back for another.

- Read every Lua module doc needed by the task before running or adapting code.
- Read the closest builtin test script source as the implementation pattern.
- Keep each `read_file` call to one path; issue multiple calls when several documents are needed.
- If output ends with `[read_file truncated: ...]`, treat it as incomplete and do not infer missing APIs.

## Discover Scripts

Call `list_dir` before reading or running unless the exact path is already confirmed in the current turn.

`list_dir` input:

- `keyword`: optional case-insensitive substring filter on the full file path, such as `scripts/builtin/` or `blink`.

Reading source:

- Use file paths returned by `list_dir` directly with `read_file`.
- Convert `scripts/...` file paths to Lua run paths only when calling `lua_run_script` or `lua_run_script_async`.

## Use Builtin References

Before choosing modules, APIs, or arguments for Lua execution:

- Prefer task-specific skills for user-facing actions.
- Use `builtin/test/` for module or hardware validation, including advanced demos, and `builtin/lib/` only as reusable source to read or require.
- Read the `.lua` source only when needed.
- Activate `builtin_lua_modules` and use its table to find the needed doc path.
- Batch-read module docs with `read_file("scripts/docs/<doc-file>")`.
- Read the closest builtin script source and reuse its patterns.

Builtin patterns:

- Display scripts use `board_manager`, `display`, `delay`, `display.begin_frame`, `display.present`, `display.end_frame`, and `pcall(display.deinit)` cleanup.
- Long display animations or games should usually run async with `exclusive: "display"` and a stable `name`.
- Hardware scripts open resources in `run()`, close them in `cleanup()`, then wrap execution in `xpcall(run, debug.traceback)`.

## Run Scripts

Run Lua only through a skill-owned script path as defined in Path Rules. The skill must be activated first, and its instructions must provide the exact `{CUR_SKILL_DIR}/scripts/...` path and args contract.

- Input: `path`, optional object `args`, and optional positive `timeout_ms`. Omitted or `0` timeout means `60000` ms.
- `path` must follow the active skill's documented script path.
- `args` is a JSON object keyed by parameter name, for example `"args":{"enabled":true}`. Lua reads it from global `args`.
- No output returns `Lua script completed with no output.`.
- Long output ends with `[output truncated]`. On failure, error text is appended after captured output.

Use `lua_run_script` for short one-shot skill scripts where output is needed in the current turn.

Use `lua_run_script_async` for skill-owned loops, animations, monitors, games, display holds, and other long-running work.

Async behavior:

- Input: `path`, optional object `args`, `timeout_ms`, `name`, `exclusive`, and `replace`.
- `timeout_ms` `0` or omitted means run until cancelled. Omitted `name` defaults to the script basename.
- At most 4 async Lua jobs can run concurrently.
- Active jobs with the same `name` cannot coexist.
- Active jobs with the same `exclusive` group cannot coexist.
- If `replace` is omitted or `false`, a conflict returns an error.
- If `replace=true`, the conflicting job is stopped first. If that does not complete in time, takeover fails.

- Always set `name` for long-running scripts.
- Set `exclusive` when the job owns singleton hardware such as display or audio.
- Use `replace:true` only when the user explicitly wants to switch jobs.

## Inspect And Stop Async Jobs

Use `lua_list_async_jobs` first, then `lua_get_async_job` when details are needed.

- Status values are `queued`, `running`, `done`, `failed`, `timeout`, and `stopped`.
- `lua_list_async_jobs` accepts optional `status`, supporting all statuses plus `all`.
- `lua_get_async_job` can query by `job_id` or `name`.
- Name lookup only matches active jobs. For finished jobs, prefer `job_id`.
- `lua_get_async_job` returns `job_id`, `name`, `status`, `exclusive`, `runtime_s`, `path`, `args`, and `summary`.

Stopping rules:

- If the user asks to stop, cancel, close, clear, or switch an async script, call the stop tool or run the replacement with `replace:true` in the same turn.
- Do not claim a job is stopped or switched based only on context.
- `lua_stop_async_job` input is `job_id` or `name`, with optional `wait_ms`.
- `lua_stop_all_async_jobs` input is optional `exclusive` and optional `wait_ms`.
- If `wait_ms` is omitted or `0`, the default wait is `2000` ms.
- If stop wait times out, do not assume the job is fully stopped yet.

## IM And Events From Lua

- For direct user replies, images, or files that do not depend on Lua runtime state, prefer calling the corresponding IM capability outside Lua.
- For router trigger events from Lua, read `builtin/test/llm_analyze_trigger.lua` and the event publisher docs before emitting a table event.

## Recommended Flow

1. Classify the task as run an existing skill-owned script, create or update a Lua-backed packaged skill, inspect or stop async jobs, or use Lua docs/references.
2. For existing behavior, activate the task-specific skill first and use only the script path and args documented by that active skill.
3. For new or adapted Lua behavior, activate `skill_creator` and create or update a packaged skill with Lua under `skills/<skill_id>/scripts/`.
4. Activate `builtin_lua_modules` before running or adapting Lua, then read only the needed module docs from `scripts/docs/*.md`.
5. Use `list_dir` and `builtin/test/` only to find reference patterns unless a specific skill explicitly instructs running a builtin script.
6. Choose sync execution for short scripts and async execution for long-running or hardware-owning scripts.
7. Stop or replace async jobs with the relevant Lua tool before saying they are stopped or switched.

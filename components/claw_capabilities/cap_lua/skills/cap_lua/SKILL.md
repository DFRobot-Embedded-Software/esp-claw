---
{
  "name": "cap_lua",
  "description": "Run, inspect, debug, and manage existing or temporary Lua scripts; use skill_creator for reusable features.",
  "metadata": {
    "cap_groups": [
      "cap_lua"
    ],
    "manage_mode": "readonly"
  }
}
---

# Lua Script Operations

Use this skill for existing Lua scripts and explicitly temporary or standalone Lua scripts: discover scripts, read module docs, run scripts, and manage async jobs.

Activation boundary: do not use this skill as the entry point for creating new reusable user-facing features, new skills, or new Lua-backed capabilities. Activate `skill_creator` first for that workflow, then use `cap_lua` only when Lua authoring or runtime rules are needed.

Creation boundary: this skill may create or edit Lua files only for temporary experiments, tests, demos, debugging, or when the user explicitly asks for a standalone Lua file. If the user asks to add or implement behavior and does not clearly say it is temporary or standalone, treat it as a reusable skill workflow and activate `skill_creator` first.

## Path Rules

Logical categories you will see in `list_dir` results and can use as `keyword` filters:

- `builtin/test/` — shipped examples, tests, and demos. Read these for patterns; treat as read-only unless the user explicitly asks to change them.
- `builtin/lib/` — reusable Lua libraries; read the matching `.md` guide before requiring.
- `docs/` — module API docs.
- Skill-owned scripts — exposed by an active skill's instructions, which already give you the exact path to pass to the run tools.

Requirements for `lua_run_script` / `lua_run_script_async`:

- Use a path returned by `list_dir`, or a path the active skill's instructions provide. Do not hand-craft paths.
- Path must end in `.lua` and must not contain `..`.
- For user-facing behavior prefer the skill-owned path. Do not run ad hoc Lua paths for user-facing work; use a packaged skill instead.

Examples:

| Intent | Use |
| --- | --- |
| Find a script | `list_dir({"keyword": "blink"})` |
| Read a discovered script or doc | `read_file({"path": "<path from list_dir>"})` |
| Run a script | `lua_run_script({"path": "<path of script>"})` |
| Run a script async | `lua_run_script_async({"path": "<path of script>", "name": "..."})` |

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

- `keyword`: optional case-insensitive substring filter on the full file path, such as `builtin/test`, `docs/`, or part of the filename.

Reading source:

- Pass paths returned by `list_dir` directly to `read_file`, `lua_run_script`, or `lua_run_script_async`.

## Use Builtin References

Before choosing modules, APIs, or arguments for Lua execution:

- Prefer task-specific skills for user-facing actions.
- Use `builtin/test/` results for module or hardware validation, including advanced demos, and `builtin/lib/` only as reusable source to read or require.
- Read the `.lua` source only when needed.
- Activate `builtin_lua_modules` and use its table to find the needed doc path.
- Batch-read module docs by passing the path `list_dir` returned (or the path the module table provides) to `read_file`.
- Read the closest builtin script source and reuse its patterns.

Builtin patterns:

- Display scripts use `board_manager`, `display`, `delay`, `display.begin_frame`, `display.present`, `display.end_frame`, and `pcall(display.deinit)` cleanup.
- Long display animations or games should usually run async with `exclusive: "display"` and a stable `name`.
- Hardware scripts open resources in `run()`, close them in `cleanup()`, then wrap execution in `xpcall(run, debug.traceback)`.

## Run Scripts

Prefer running Lua through a skill-owned script path as defined in Path Rules. For user-facing behavior, the skill must be activated first and its instructions must provide the exact script path and args contract.

- Input: `path`, optional object `args`, and optional positive `timeout_ms`. Omitted or `0` timeout means `60000` ms.
- `path` must end in `.lua` and must not contain `..`. Use a path returned by `list_dir`, or a path the active skill's instructions provide. Do not hand-craft paths.
- For user-facing work, `path` should follow the active skill's documented script path; `builtin/...` reference scripts are allowed for inspection and demos only.
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
- For router trigger events from Lua, find `llm_analyze_trigger.lua` via `list_dir({"keyword": "llm_analyze_trigger"})`, read it, and review the event publisher docs before emitting a table event.

## Recommended Flow

1. Classify the task as run an existing skill-owned script, inspect or stop async jobs, or use Lua docs/references.
2. For existing behavior, activate the task-specific skill first and use only the script path and args documented by that active skill.
3. Activate `builtin_lua_modules` before running or adapting Lua, then read only the needed module docs (find them via `list_dir({"keyword": "docs/"})` or the module table).
4. Use `list_dir` with a `builtin/test` keyword only to find reference patterns; do not run those scripts for user-facing work unless a specific skill explicitly instructs doing so (in which case pass the path `list_dir` returned directly).
5. Choose sync execution for short scripts and async execution for long-running or hardware-owning scripts.
6. Stop or replace async jobs with the relevant Lua tool before saying they are stopped or switched.

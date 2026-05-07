---
{
  "name": "skill_creator",
  "description": "Create, register, update, or remove skills with Lua support.",
  "metadata": {
    "cap_groups": [
      "cap_skill"
    ],
    "manage_mode": "readonly"
  }
}
---

# Skill Creator

Use this skill when the user asks to create, register, update, or remove a skill, or asks how to create a skill that includes Lua files.

For Lua-backed skills, follow the Lua-specific reference before generating or editing Lua files.

## Core Rules

Every skill creation flow has two mandatory phases:

1. Create the skill files or generated runtime skill description.
2. Immediately call `register_skill` so the newly created skill is added to the active skill registry.

Skills with source files live under a `skills/<skill_id>/` directory that is included in the firmware or file image build. They may require rebuilding or regenerating the image that contains skills.

Skill id rules:

- Use lowercase letters, digits, underscores, or hyphens.
- Do not use spaces, slashes, backslashes, absolute paths, or `..`.
- Make the id match the user-facing behavior rather than the implementation.
- Do not reuse an existing skill id.

Intent description rules:

- Describe user intent, not just internal implementation.
- Include trigger words users are likely to say.
- Include prerequisites when they are required.
- Keep it to one concise sentence.
- Do not summarize a skill as only running a script or calling a tool.

Capability group rules:

- Use capability groups that already exist in the project.
- Include every capability group the skill needs.
- Include `cap_lua` when the skill instructs the model to run Lua.
- Include `cap_skill` only when the skill instructs the model to register, unregister, or inspect skills.

File generation rules:

- Create skill files by directly writing the needed files. Do not run a bundled preparation script or template generator.
- Generate `SKILL.md` from the final behavior, not from a generic unchanged template.
- Generate optional bundled files directly, such as `scripts/<name>.lua`, `references/<name>.md`, or assets.
- If the environment cannot write files or cannot call `register_skill`, provide the target relative paths and full file contents, report the blocker, and do not claim the skill was fully created and registered.

Registration rules:

- Call `register_skill` for every newly created skill as the final creation step.
- Register with `file` set exactly to `<skill_id>/SKILL.md`.
- Use the tool result as the source of truth for registered skill metadata.
- If registration fails, report the returned error directly and do not claim the skill was registered.

The model remains responsible for intent, final `skill_id` choice, user-facing wording, capability group choice, prerequisite analysis, `Recommended Flow`, args schema design, hardware/API behavior, and final source edits.

## Skill File Layout

Use this source layout for a skill with files:

```text
component_or_app/
└── skills/
    └── skill_id/
        ├── SKILL.md
        ├── references/
        │   └── guide.md
        ├── scripts/
        │   └── action.lua
        └── assets/
            └── image.bin
```

Valid source locations are project-specific. Common locations include component skill directories and application FATFS image skill directories. Do not create skills outside a directory that the current build or file-image generation path includes.

Rules:

- `skills/<skill_id>/SKILL.md` is required.
- `references/`, `scripts/`, `assets/`, and other subdirectories are optional.
- `skills/<skill_id>/scripts/*.lua` files are optional, but all bundled Lua files must live under `scripts/`.
- The `SKILL.md` frontmatter `name` must match `skill_id`.
- Set `metadata.manage_mode` to `readonly` for source-file skills.
- Reference bundled files in the skill body with `{CUR_SKILL_DIR}/...`.
- Reference bundled scripts in the skill body with `{CUR_SKILL_DIR}/scripts/<name>.lua`.
- Do not reference source-tree paths or FATFS output paths directly.

## Create A Skill

Flow:

1. Decide the user-facing behavior, title, description, capability groups, whether Lua is needed, and bundled file names.
2. If Lua is needed, read `{CUR_SKILL_DIR}/references/write_lua.md`.
3. Check the target `skills/<skill_id>/` directory does not already exist unless the user explicitly asked to update or replace that skill.
4. Write the complete `SKILL.md` and any optional bundled files into a valid source `skills/<skill_id>/` directory.
5. Make semantic sections specific to the skill: trigger wording, prerequisites, `Recommended Flow`, args schema, and script behavior when Lua is used.
6. Register the skill using the flow below.
7. Tell the user the registered skill id.
8. Tell the user if a rebuild, file image regeneration, registry reload, or device restart may still be required before a newly created source skill is fully available.

Use this `SKILL.md` pattern for a Lua-backed skill:

````md
---
{
  "name": "skill_id",
  "description": "Describe the user-facing action and any prerequisites in one sentence.",
  "metadata": {
    "cap_groups": [
      "cap_lua"
    ],
    "manage_mode": "readonly"
  }
}
---

# Skill Title

Use this skill when the user asks to perform the specific user-facing action.

Run exactly one bundled Lua script with the Lua script execution capability.

If script execution returns an error, report that error directly to the user.
Do not retry with changed arguments or run another script in the same turn unless the user explicitly asks.

## Script Args Schema

```json
{
  "type": "object",
  "properties": {}
}
```

## Tool Call Inputs

Default action:

```json
{"path":"{CUR_SKILL_DIR}/scripts/action.lua","args":{}}
```

## Recommended Flow

1. Check required prerequisite skills, hardware declarations, or capability availability.
2. Confirm the script path is the bundled skill-local path `{CUR_SKILL_DIR}/scripts/action.lua`.
3. Validate or choose safe arguments from the documented args schema.
4. Run `{CUR_SKILL_DIR}/scripts/action.lua` with the resolved `args`.
5. Report the script result or error directly to the user.
````

For a non-Lua skill, omit Lua-specific sections and include only the capability groups and flow needed for the user-facing action.

## Create A Lua File

Read `{CUR_SKILL_DIR}/references/write_lua.md` before creating or editing Lua files. It contains the Lua template, script path rules, module documentation strategy, authoring rules, and quality rules.

## Register Every Created Skill

Before registering a skill, choose:

- `skill_id`: stable, short, and based on the user-facing behavior.
- `file`: exactly `<skill_id>/SKILL.md`.
- `summary`: one sentence describing when the skill should be used, including common user wording and critical prerequisites.

Flow:

1. Choose or edit the final `skill_id` and `summary`.
2. Ensure the skill's `SKILL.md` content has been created or generated.
3. Call `register_skill` directly with `skill_id`, `file`, and `summary`.
4. If registration succeeds, tell the user the skill id that was registered.
5. If registration fails, report the returned error directly and do not claim the skill was registered.

The `register_skill` input has this shape:

```json
{"skill_id":"weather_alerts","file":"weather_alerts/SKILL.md","summary":"Answer weather alert and forecast questions for a requested location using available search or weather capabilities."}
```

Use the tool result as the source of truth for the registered skill metadata.

## Update A Skill

When updating a skill, update its files or generated summary, then refresh registration:

1. Confirm the target `skill_id` and whether the user asked to update or replace that skill.
2. Update the existing skill files or generated runtime description.
3. Call `unregister_skill` for the old `skill_id` when the registry requires replacement.
4. Call `register_skill` with the same `skill_id`, the same `file`, and the updated `summary`.

If unregistering or registering fails, stop and report the error.

## Remove A Skill

Use `unregister_skill` to remove a skill from the active registry:

```json
{"skill_id":"weather_alerts"}
```

If the tool says the skill is readonly or cannot be removed, report that error directly.

## Good Examples

Create and register a reminder skill:

```json
{"skill_id":"simple_reminders","file":"simple_reminders/SKILL.md","summary":"Help create, list, and cancel simple reminders when the user asks to remember something later."}
```

Create and register a board notes skill:

```json
{"skill_id":"board_notes","file":"board_notes/SKILL.md","summary":"Record and retrieve short board-specific notes when the user asks to save or recall local device information."}
```

Create and register a Lua skill when the user asks for scripts, assets, or detailed flow:

```text
components/example/skills/take_measurement/
├── SKILL.md
└── scripts/
    └── take_measurement.lua
```

## Bad Examples

Do not use implementation-only summaries:

```json
{"skill_id":"script_runner","file":"script_runner/SKILL.md","summary":"Run a Lua script."}
```

Do not use invalid paths:

```json
{"skill_id":"my skill","file":"../my skill/SKILL.md","summary":"Create a skill."}
```

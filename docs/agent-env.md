# `.zagent/`

`.zagent/` is the fixed runtime environment directory inside a workspace.
There is no environment YAML file; runtime discovers files by convention.

## Structure

```text
.zagent/
├── run.yaml
├── prompts/
│   ├── system.md
│   ├── developer.md
│   └── task.md
├── rules/
│   └── *.md
├── skills/
│   └── *.md
├── mcp/
│   └── servers.yaml
├── files/
└── artifacts/
    └── <run_id>/
```

## Discovery Rules

`run.yaml` describes one run. It can contain the task prompt inline through
`task.prompt`, or point to a file through `task.prompt_file`.

`prompts/system.md` is optional. If present, runtime adds it to the system
message.

`prompts/developer.md` is optional. If present, runtime also adds it to the
system message.

`prompts/task.md` is not loaded automatically. Use it by setting:

```yaml
task:
  prompt_file: prompts/task.md
```

All markdown files under `rules/` are added to the `You have rules:` catalog.
Runtime does not inline rule bodies; it includes path, title, and a short
description so the agent can read a relevant file when needed.

All markdown files under `skills/` are added to the `You have skills:` catalog
with the same path/title/description format.

`mcp/servers.yaml` is used when `tools.enable_mcp` is true.

Files under `files/` are reserved for extra context and future runtime features.

## Artifacts

Runtime writes run artifacts to:

```text
.zagent/artifacts/<run_id>/
```

Core artifacts:

```text
chat.jsonl
events.jsonl
tools.jsonl
state.json
result.json
summary.md
```

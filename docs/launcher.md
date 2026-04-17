# Launcher Architecture And Roadmap

`zagent-launcher` is the host-side package that exposes the `zagent` CLI. It is
installed on the user's machine. `zagent-runtime` is not installed on the host;
it is delivered only as a runtime image that contains the `zagent-runtime`
entrypoint.

The launcher owns project initialization, runtime container startup, and artifact
inspection. Runtime owns agent execution. They communicate only through files in
the mounted workspace.

## User Contract

The primary command is:

```bash
zagent
```

MVP commands:

```bash
zagent init
zagent run
zagent status
zagent logs
zagent result
zagent doctor
```

`zagent init` runs in a project root and creates:

```text
.zagent/
├── run.yaml
├── prompts/
│   ├── system.md
│   └── task.md
├── rules/
│   └── global.md
├── skills/
├── mcp/
└── files/
```

It must not overwrite existing files unless `--force` is passed. The generated
`run.yaml` should be valid for the current runtime contract:

```yaml
run_id: default
mode: task

task:
  title: Describe the task
  prompt_file: prompts/task.md
  workspace: /workspace

model:
  provider: openai_compatible
  model: gpt-5-mini
  api_key_env: OPENAI_API_KEY
  timeout_seconds: 60
  reasoning_effort: medium

runtime:
  image: zagent-runtime:local
  workdir: /workspace
  max_turns: 40

tools:
  builtin:
    - shell
    - files
  custom: []
  enable_mcp: false

policy:
  network: restricted
  git_push: false
  writable_paths:
    - /workspace
```

`agent_env.path` is intentionally omitted. Runtime defaults it to `.zagent`
relative to `task.workspace`, which resolves to `/workspace/.zagent` inside the
container.

`zagent run` finds `.zagent/run.yaml`, mounts the host project root to
`/workspace`, and starts the configured runtime image:

```bash
docker run --rm \
  --workdir /workspace \
  --volume "$PWD:/workspace" \
  --env OPENAI_API_KEY \
  zagent-runtime:local \
  run --run-spec /workspace/.zagent/run.yaml
```

The actual command must be built from structured `ContainerSpec` and
`MountSpec`, not string concatenation. The runtime Dockerfile uses:

```text
ENTRYPOINT ["zagent-runtime"]
```

so the launcher passes runtime CLI arguments as the container command.

## Runtime Integration

Launcher and runtime must remain independently installable and independently
testable. The launcher does not import `zagent_runtime`.

Stable integration points:

- `.zagent/run.yaml`
- `.zagent/` fixed directory structure
- `.zagent/artifacts/<run_id>/state.json`
- `.zagent/artifacts/<run_id>/chat.jsonl`
- `.zagent/artifacts/<run_id>/events.jsonl`
- `.zagent/artifacts/<run_id>/tools.jsonl`
- `.zagent/artifacts/<run_id>/result.json`
- `.zagent/artifacts/<run_id>/summary.md`
- runtime image entrypoint `zagent-runtime`
- runtime command `run --run-spec /workspace/.zagent/run.yaml`

The launcher may duplicate lightweight DTOs for reading `run.yaml`, but shared
runtime behavior must live in file contracts or JSON Schema under `contracts/`.
If launcher and runtime need the same validation rule, prefer updating the
contract first.

## Clean Architecture

The package follows the same dependency direction as runtime:

```text
presentation -> application -> domain
infrastructure -> application/domain
```

Domain has no dependency on Typer, Rich, Docker, YAML, or the filesystem.
Application use cases depend on ports. Infrastructure implements ports.
Presentation adapts Typer commands to application use cases.

Target structure:

```text
packages/launcher/src/zagent_launcher/
├── domain/
│   ├── project_layout.py
│   ├── run_request.py
│   ├── run_spec_ref.py
│   ├── container_spec.py
│   ├── mount_spec.py
│   ├── env_var.py
│   ├── launch_result.py
│   ├── run_status.py
│   └── artifact_ref.py
├── application/
│   ├── dto/
│   ├── interfaces/
│   │   ├── artifacts.py
│   │   ├── config.py
│   │   ├── containers.py
│   │   ├── environment.py
│   │   └── projects.py
│   ├── use_cases/
│   │   ├── init_project.py
│   │   ├── prepare_run.py
│   │   ├── start_run.py
│   │   ├── read_run_state.py
│   │   ├── read_run_trace.py
│   │   ├── collect_run_result.py
│   │   └── check_environment.py
│   └── errors.py
├── infrastructure/
│   ├── filesystem/
│   │   ├── local_project_writer.py
│   │   └── artifact_reader.py
│   ├── config/
│   │   ├── run_spec_reader.py
│   │   ├── templates.py
│   │   └── template_files/
│   ├── docker/
│   │   ├── docker_cli_runner.py
│   │   └── image_resolver.py
│   └── di/
│       └── container.py
└── presentation/
    ├── cli/
    │   ├── app.py
    │   ├── dependencies.py
    │   ├── output.py
    │   └── commands/
    └── api.py
```

## Domain

Recommended domain models:

- `ProjectLayout`: host project root, `.zagent` path, default run spec path, artifacts root.
- `RunSpecRef`: host path to run spec, container path to run spec, run id, runtime image.
- `RunRequest`: user intent for one launch, including project root, run spec path, dry run flag, and optional continue message.
- `ContainerSpec`: image, command, workdir, mounts, env vars, network mode, remove flag, tty flag.
- `MountSpec`: host path, container path, read/write mode.
- `EnvVar`: name and optional resolved value source.
- `LaunchResult`: exit code, run id, artifact paths, final message preview.
- `ArtifactRef`: artifact name, path, media type.

These models should be immutable dataclasses or Pydantic models with no side
effects.

## Application Use Cases

`InitProject`

Creates `.zagent` from templates. It receives a project root and init options,
checks collisions, writes files through a `ProjectWriter` port, and returns a
summary of created/skipped files.

`DiscoverProject`

Finds the project root. MVP behavior: current directory must contain `.zagent`.
Later behavior: walk parents until `.zagent` is found.

`PrepareRun`

Reads `.zagent/run.yaml`, resolves the runtime image, validates that required
environment variables exist on the host for real runs, and builds a
`ContainerSpec`. Dry runs intentionally skip the model API key check because the
runtime does not call the LLM backend in that mode.

`StartRun`

Runs the container through a `ContainerRunner` port. It does not know whether the
implementation uses Docker CLI, Docker SDK, Podman, or a remote runner.

`ReadRunState`, `ReadRunTrace`, `CollectRunResult`

Read runtime artifacts from `.zagent/artifacts/<run_id>/`. They should tolerate
partially written JSONL files so `zagent logs --follow` can work while the
container is still running.

MVP status: `status`, `logs`, and `result` can read completed run artifacts.
Live `logs --follow` is still pending.

`CheckEnvironment`

Checks host prerequisites:

- Docker SDK can reach the Docker daemon;
- Docker daemon is reachable;
- configured runtime image exists locally or can be pulled;
- `.zagent/run.yaml` exists and is readable;
- required model API key env vars are present;
- project root is mountable.

## Infrastructure

MVP uses Docker SDK for Python (`docker-py`) behind the `ContainerRunner` port.
The launcher must not build shell command strings for Docker interaction.

`DockerSdkRunner` responsibilities:

- convert `ContainerSpec` into Docker SDK `containers.run` arguments;
- stream container logs to launcher output;
- wait for container completion;
- return the exit code;
- remove the container after completion when `ContainerSpec.remove` is true;
- wrap Docker SDK failures in launcher-owned errors.

`LocalProjectWriter` responsibilities:

- create directories;
- write template files;
- prevent overwrite without `--force`;
- keep file permissions simple and portable.

`YamlRunSpecReader` responsibilities:

- read only fields launcher needs: `run_id`, `task.workspace`, `model.api_key_env`,
  `runtime.image`, `runtime.workdir`, `policy.network`;
- fail with launcher-owned errors;
- avoid importing runtime DTOs.

## Presentation

Typer stays only in `presentation/cli.py`.

Command shape:

```text
zagent init [--template basic|python|research] [--force]
zagent run [--run-spec .zagent/run.yaml] [--image IMAGE] [--dry-run] [--continue TEXT]
zagent status [--run-id RUN_ID]
zagent logs [--run-id RUN_ID] [--follow]
zagent result [--run-id RUN_ID] [--json]
zagent doctor
```

The CLI should print human-friendly output through Rich, but application use
cases should return plain domain/application DTOs so the Python API can reuse
them.

## Multi-Agent Direction

Runtime currently executes one run spec. Launcher can grow multi-agent support
without changing runtime by scheduling multiple run specs.

Future layout:

```text
.zagent/
├── run.yaml
└── runs/
    ├── lint-fix.yaml
    ├── tests-fix.yaml
    └── research.yaml
```

Future commands:

```bash
zagent run --run-spec .zagent/runs/lint-fix.yaml
zagent run --all .zagent/runs
zagent run-group .zagent/runs --parallel 2
```

Each runtime container still receives exactly one run spec and writes to its own
`.zagent/artifacts/<run_id>/` directory.

## Roadmap

### Milestone 1: CLI Skeleton

- Keep `zagent = zagent_launcher.presentation.cli:main`.
- Add commands `init`, `run`, `status`, `logs`, `result`, `doctor`.
- Wire use cases through a small DI factory.
- Add unit tests for command registration and help output.

### Milestone 2: Project Init

- Implement `ProjectLayout`.
- Implement `InitProject`.
- Add basic templates for `.zagent/run.yaml`, `prompts/system.md`,
  `prompts/task.md`, and `rules/global.md`.
- Ensure `init` is idempotent and refuses overwrites without `--force`.
- Add tests for created files and collision behavior.

### Milestone 3: Run Preparation

- Implement `YamlRunSpecReader`. Done.
- Implement `DiscoverProject`.
- Implement `PrepareRun`. Done.
- Validate required host env vars from `model.api_key_env`. Done.
- Build `ContainerSpec` for the current runtime contract. Done.
- Add tests for default `.zagent/run.yaml`, custom `--run-spec`, `--image`, and
  missing env vars. Partially done.

### Milestone 4: Docker Runner

- Implement `DockerSdkRunner`. Done.
- Use Docker SDK instead of subprocess Docker CLI. Done.
- Pass the workspace mount, workdir, env vars, and runtime command. Done.
- Support `--dry-run` by passing runtime `--dry-run`. Done.
- Add integration tests with a fake Docker SDK client before real Docker tests. Done.

### Milestone 5: Artifact Readers

- Implement `ReadRunState`, `ReadRunTrace`, and `CollectRunResult`.
- Add `status`, `logs`, and `result` commands.
- Support missing/incomplete artifacts with clear messages.
- Add JSONL tailing for `logs --follow`.

### Milestone 6: Environment Checks And UX

- Implement the `CheckEnvironment` use case behind the `zagent doctor` command.
- Add Rich output for init summaries, run start, run finish, and failures.
- Document install and first-run flow.
- Add examples that use only `zagent init` and `zagent run`.

### Milestone 7: Multi-Run Launcher

- Add `.zagent/runs/*.yaml` discovery.
- Add sequential run groups.
- Add bounded parallel run groups.
- Keep one runtime container per run spec.

## Non-Goals For MVP

- Do not import `zagent_runtime`.
- Do not reimplement agent execution in launcher.
- Do not support remote runners before local Docker SDK execution is stable.
- Do not add multi-agent orchestration until single-run init/run/status/result is
  reliable.

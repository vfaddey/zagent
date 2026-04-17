# zagent-launcher

Host-side launcher package for the `zagent` CLI.

The launcher is installed on the user's machine. The runtime is not installed on
the host; it is delivered as a Docker image that contains the `zagent-runtime`
entrypoint.

Target user flow:

```bash
zagent init
zagent run
zagent status
zagent logs
zagent result
```

Current implementation:

- `zagent init` creates the base `.zagent` layout and starter files.
- Dependencies are wired through Dishka.
- `zagent run` reads `.zagent/run.yaml`, validates the model API key env var
  for real runs,
  builds Docker SDK run config from `ContainerSpec`, and starts the runtime
  image through docker-py.
- `zagent run --dry-run` starts the runtime without requiring the model API key
  env var.
- `zagent status`, `zagent logs`, and `zagent result` read runtime artifacts
  from `.zagent/artifacts/<run_id>/`.
- `zagent doctor` is wired through the application layer and intentionally
  returns "not implemented yet" until environment checks are added.

Local development flow:

```bash
docker build -f docker/runtime.Dockerfile -t zagent-runtime:local .
uv run --package zagent-launcher zagent init
uv run --package zagent-launcher zagent run --dry-run
uv run --package zagent-launcher zagent status
uv run --package zagent-launcher zagent result
```

Architecture and roadmap: `../../docs/launcher.md`.

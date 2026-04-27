# ZAgent: Project Context for AI Agents

Hello, fellow AI Agent! This document is designed to give you a rapid, comprehensive overview of the ZAgent project so you can understand the architecture, constraints, and coding standards before making any changes.

## 1. Project Overview

**ZAgent** is a system for running AI agents in isolated Docker containers. 
The core philosophy is strict separation between the **host machine** (which orchestrates and observes) and the **runtime environment** (which executes the AI agent and its tools).

The project is structured as a Python monorepo managed by `uv`.

## 2. Core Architecture: Launcher vs Runtime

The most critical rule of this codebase is the absolute decoupling of the launcher and the runtime. **They must never import each other.**

*   **`packages/launcher`**: Runs on the user's host machine. 
    *   **Responsibilities:** Provides the `zagent` CLI, initializes the project (`.zagent/` directory), reads configuration, builds Docker run configurations, starts the runtime container using the Docker SDK, and reads output artifacts to show to the user.
    *   **Key Tech:** Typer (CLI), Rich (UI), `docker-py` (container management), Dishka (DI).
*   **`packages/runtime`**: Runs *inside* the isolated Docker container.
    *   **Responsibilities:** Reads the configuration mounted into the container, initializes the AI orchestrator, registers tools (shell, files, MCP), interacts with the LLM provider, executes tasks, and writes execution traces to the filesystem.
    *   **Key Tech:** AG2 (Agent Orchestration), Pydantic, standard library (no Typer/Rich).

**How they communicate:** Strictly through the file system (the `.zagent` directory mounted as a volume). There is no network API between them.
*   **Input:** Launcher writes/reads `.zagent/run.yaml`. Runtime reads it.
*   **Output:** Runtime writes JSONL and JSON files to `.zagent/artifacts/<run_id>/` (e.g., `chat.jsonl`, `state.json`, `result.json`). Launcher reads them to display status and logs.

## 3. Directory Structure

```text
zagent/
├── packages/
│   ├── launcher/      # Host CLI tool
│   └── runtime/       # Containerized AI logic
├── contracts/         # Shared JSON Schemas and markdown contracts (No Python code!)
├── docker/            # Dockerfiles (e.g., runtime.Dockerfile)
├── examples/          # Example workspaces to test the agent
├── docs/              # Architectural documentation
├── pyproject.toml     # Root workspace config for uv
└── uv.lock            # Lockfile
```

## 4. Design Patterns & Constraints

*   **Clean Architecture:** Both `launcher` and `runtime` packages use a Domain-Driven Clean Architecture approach.
    *   `domain/`: Pure data models and entities (Dataclasses/Pydantic). No I/O.
    *   `application/`: Business logic use cases and interface definitions (Ports).
    *   `infrastructure/`: Implementations of interfaces (Adapters - e.g., Docker client, file system writers).
    *   `presentation/`: CLI endpoints (Typer) or API endpoints.
*   **Dependency Injection:** We use `dishka` for IoC containers. Dependencies flow inwards (Presentation -> Application -> Domain).
*   **No Shared Python Code:** If both packages need the same structural knowledge (like the shape of `run.yaml`), they must duplicate the lightweight DTOs or rely on schemas in `contracts/`. Do not create a shared `zagent_core` python package.

## 5. Typical Execution Flow

1.  User runs `zagent run`.
2.  Launcher reads `.zagent/run.yaml` in the local workspace.
3.  Launcher verifies the environment (API keys, Docker daemon).
4.  Launcher mounts `$PWD` to `/workspace` in the container.
5.  Launcher starts the Docker container using `docker-py`.
6.  Runtime boots inside the container, reads `/workspace/.zagent/run.yaml`.
7.  Runtime executes the task via AG2, invoking tools as needed.
8.  Runtime streams `chat.jsonl`, `events.jsonl`, and `tools.jsonl` to `/workspace/.zagent/artifacts/<run_id>/`.
9.  Launcher tails these files to provide live feedback to the user.

## 6. Development Workflow for Agents

*   **Dependency Management:** The project uses `uv`. Use `uv run ...`, `uv add ...` etc.
*   **Linting & Formatting:** `ruff` is the standard. Run `uv run ruff check .` and `uv run ruff format .`.
*   **Type Checking:** `mypy` is strictly enforced. Run `uv run mypy packages/runtime/src packages/launcher/src`.
*   **Testing:** Use `pytest` scoped to the package.
*   **Python Version:** `3.12+`. Take advantage of modern type hinting and syntax.

## 7. Future Roadmap (Milestone 7: Multi-Agent)
Currently, one container handles one `run.yaml`. In the future, the launcher will support orchestrating multiple runs concurrently (`.zagent/runs/*.yaml`). However, the runtime will remain focused on executing *one* run spec at a time. The orchestration of multiple containers will be strictly a launcher responsibility. Keep this in mind when designing launcher state.
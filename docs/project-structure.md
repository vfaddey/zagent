# Project Structure

ZAgent is a workspace with two independent Python packages.

`zagent-runtime` is installed into the runtime container. It owns the agent execution
pipeline, tools, MCP integration, policies, and observability.

`zagent-launcher` runs on the host. It prepares a run, starts a runtime container, and
reads artifacts from the mounted workspace.

The two packages communicate through file contracts under `contracts/`.

Launcher architecture and roadmap are documented in `docs/launcher.md`.

from __future__ import annotations

import json
from pathlib import Path

from zagent_runtime.application.bootstrap import BootstrapRun
from zagent_runtime.domain.run import ResultStatus
from zagent_runtime.infrastructure.di.container import RuntimeContainerFactory


def test_bootstrap_dry_run_writes_runtime_artifacts(tmp_path: Path) -> None:
    run_spec_file = _write_runtime_workspace(tmp_path)
    container = RuntimeContainerFactory().create_dry_run()

    result = container.get(BootstrapRun)(run_spec_file)

    run_dir = tmp_path / ".zagent" / "artifacts" / "run-1"
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    result_json = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert result.result.status is ResultStatus.SUCCESS
    assert result.result.final_message.endswith("ZAGENT_DONE")
    assert state["status"] == "succeeded"
    assert state["artifacts"] == ["result.json", "summary.md"]
    assert result_json["status"] == "success"
    assert (run_dir / "summary.md").read_text(encoding="utf-8") == "Dry run completed."
    assert [event["event"] for event in _jsonl(run_dir / "events.jsonl")] == [
        "run_started",
        "task_started",
        "result_collecting",
        "run_finished",
    ]
    assert [message["role"] for message in _jsonl(run_dir / "chat.jsonl")] == [
        "system",
        "user",
        "assistant",
    ]


def _write_runtime_workspace(root: Path) -> Path:
    agent_env = root / ".zagent"
    (agent_env / "prompts").mkdir(parents=True)
    (agent_env / "rules").mkdir()
    (agent_env / "skills").mkdir()

    (agent_env / "prompts" / "system.md").write_text(
        "You are a runtime agent.",
        encoding="utf-8",
    )
    (agent_env / "prompts" / "task.md").write_text(
        "Use only configured tools.",
        encoding="utf-8",
    )
    (agent_env / "rules" / "global.md").write_text(
        "# Global Rule\n\nKeep changes scoped.",
        encoding="utf-8",
    )
    (agent_env / "skills" / "python.md").write_text(
        "# Python Skill\n\nRun tests when possible.",
        encoding="utf-8",
    )
    run_spec_file = agent_env / "run.yaml"
    run_spec_file.write_text(
        """
run_id: run-1
mode: fix
task:
  title: Test bootstrap
  prompt_file: prompts/task.md
  workspace: ..
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
agent_env:
  path: .zagent
runtime:
  image: zagent-runtime:local
  workdir: .
  max_turns: 3
tools:
  builtin:
    - files
    - shell
  custom: []
  enable_mcp: false
policy:
  network: restricted
  git_push: false
  writable_paths:
    - .
""".lstrip(),
        encoding="utf-8",
    )
    return run_spec_file


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]

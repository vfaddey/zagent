from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner
from zagent_launcher.presentation.cli import app

runner = CliRunner()


def test_cli_registers_mvp_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "run", "status", "logs", "result", "doctor"):
        assert command in result.output


def test_init_creates_basic_zagent_layout(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".zagent/run.yaml").is_file()
    assert (tmp_path / ".zagent/prompts/system.md").is_file()
    assert (tmp_path / ".zagent/prompts/task.md").is_file()
    assert (tmp_path / ".zagent/rules/global.md").is_file()
    assert (tmp_path / ".zagent/skills").is_dir()
    assert (tmp_path / ".zagent/mcp").is_dir()
    assert (tmp_path / ".zagent/files").is_dir()


def test_init_skips_existing_files_without_force(tmp_path: Path) -> None:
    run_spec = tmp_path / ".zagent/run.yaml"
    run_spec.parent.mkdir(parents=True)
    run_spec.write_text("custom: true\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert run_spec.read_text(encoding="utf-8") == "custom: true\n"
    assert "skipped" in result.output


def test_run_command_is_wired_to_prepare_run(tmp_path: Path) -> None:
    result = runner.invoke(app, ["run", "--project-root", str(tmp_path)])

    assert result.exit_code == 1
    assert "Run spec not found" in result.output


def test_status_reads_runtime_state(tmp_path: Path) -> None:
    _write_run_spec(tmp_path)
    run_dir = tmp_path / ".zagent/artifacts/default"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(
        json.dumps({"run_id": "default", "status": "succeeded", "phase": "finished"}),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["status", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "run_id: default" in result.output
    assert "status: succeeded" in result.output


def test_result_reads_runtime_result_as_json(tmp_path: Path) -> None:
    _write_run_spec(tmp_path)
    run_dir = tmp_path / ".zagent/artifacts/default"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "run_id": "default",
                "status": "success",
                "summary": "done",
                "final_message": "done\n\nZAGENT_DONE",
                "artifacts": ["result.json"],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["result", "--project-root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    assert '"status": "success"' in result.output


def test_logs_reads_runtime_trace(tmp_path: Path) -> None:
    _write_run_spec(tmp_path)
    run_dir = tmp_path / ".zagent/artifacts/default"
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        '{"ts":"2026-04-17T10:00:00Z","event":"run_started"}\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["logs", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "events.jsonl" in result.output
    assert "run_started" in result.output


def _write_run_spec(project_root: Path) -> None:
    run_spec = project_root / ".zagent/run.yaml"
    run_spec.parent.mkdir(parents=True, exist_ok=True)
    run_spec.write_text(
        """
run_id: default
model:
  api_key_env: OPENAI_API_KEY
runtime:
  image: zagent-runtime:local
  workdir: /workspace
policy:
  network: restricted
""".lstrip(),
        encoding="utf-8",
    )

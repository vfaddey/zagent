from __future__ import annotations

from pathlib import Path

import pytest
from zagent_runtime.infrastructure.security.errors import PolicyViolationError
from zagent_runtime.infrastructure.security.policies import FileSystemPolicy
from zagent_runtime.infrastructure.tools.builtin.files import FilesTool
from zagent_runtime.infrastructure.tools.builtin.shell import ShellTool

from .factories import create_context


def test_files_tool_reads_writes_and_lists_workspace_files(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    tool = FilesTool(FileSystemPolicy())

    write_result = tool.write_text(context, "src/example.txt", "hello")
    read_result = tool.read_text(context, "src/example.txt")
    list_result = tool.list_dir(context, "src")

    assert write_result.ok
    assert read_result.output == "hello"
    assert list_result.data == {
        "path": str(tmp_path / "src"),
        "entries": ["example.txt"],
    }


def test_files_tool_blocks_writes_outside_writable_roots(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    tool = FilesTool(FileSystemPolicy())

    with pytest.raises(PolicyViolationError):
        tool.write_text(context, str(tmp_path.parent / "outside.txt"), "blocked")


def test_shell_tool_runs_command_in_workspace(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    tool = ShellTool()

    result = tool.run(context, "pwd && printf done")

    assert result.ok
    assert str(tmp_path) in result.output
    assert result.output.endswith("done")



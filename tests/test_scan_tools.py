"""Tests for scanner tools."""

import os
import tempfile

from chaos_agents.tools.scan_tools import (
    find_python_files,
    read_file_content,
    search_pattern_in_file,
)


def test_find_python_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "agent.py"), "w").write("from agentscope.agent import ReActAgent")
        open(os.path.join(tmpdir, "readme.md"), "w").write("# Readme")
        os.makedirs(os.path.join(tmpdir, "sub"))
        open(os.path.join(tmpdir, "sub", "tools.py"), "w").write("pass")

        files = find_python_files(tmpdir)
        assert len(files) == 2
        assert any("agent.py" in f for f in files)
        assert any("tools.py" in f for f in files)


def test_search_pattern_in_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('agent = ReActAgent(name="Bot", sys_prompt="You are helpful")\n')
        f.write("toolkit.register_tool_function(dangerous_func)\n")
        f.flush()

        matches = search_pattern_in_file(f.name, r"ReActAgent\(")
        assert len(matches) == 1
        assert "ReActAgent(" in matches[0]["line"]
        assert matches[0]["line_number"] == 1

        tool_matches = search_pattern_in_file(f.name, r"register_tool_function\(")
        assert len(tool_matches) == 1

    os.unlink(f.name)


def test_read_file_content():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\n")
        f.flush()

        content = read_file_content(f.name)
        assert "line1" in content
        assert "line3" in content

    os.unlink(f.name)


def test_read_file_content_max_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        for i in range(100):
            f.write(f"line {i}\n")
        f.flush()

        content = read_file_content(f.name, max_lines=10)
        assert "line 0" in content
        assert "line 9" in content
        assert "line 10" not in content

    os.unlink(f.name)

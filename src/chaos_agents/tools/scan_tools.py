"""Tools for the Scanner Agent — static code analysis of target codebases."""

from __future__ import annotations

import os
import re

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


def find_python_files(directory: str) -> list[str]:
    """Recursively find all Python files in a directory.

    Args:
        directory: Root directory to search.

    Returns:
        List of absolute file paths.
    """
    python_files = []
    for root, _dirs, files in os.walk(directory):
        # Skip hidden dirs and common non-source dirs
        if any(
            part.startswith(".") or part in ("__pycache__", "node_modules", ".venv", "venv")
            for part in root.split(os.sep)
        ):
            continue
        for fname in files:
            if fname.endswith(".py"):
                python_files.append(os.path.join(root, fname))
    return sorted(python_files)


def search_pattern_in_file(
    file_path: str,
    pattern: str,
) -> list[dict]:
    """Search for a regex pattern in a file and return matches with line numbers.

    Args:
        file_path: Path to the file to search.
        pattern: Regex pattern to search for.

    Returns:
        List of dicts with 'line_number', 'line', and 'match' keys.
    """
    matches = []
    try:
        with open(file_path, "r", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                m = re.search(pattern, line)
                if m:
                    matches.append({
                        "line_number": i,
                        "line": line.rstrip(),
                        "match": m.group(0),
                    })
    except (OSError, UnicodeDecodeError):
        pass
    return matches


def read_file_content(file_path: str, max_lines: int = 200) -> str:
    """Read file content up to a maximum number of lines.

    Args:
        file_path: Path to the file.
        max_lines: Maximum lines to read.

    Returns:
        File content as a string.
    """
    lines = []
    try:
        with open(file_path, "r", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
    except (OSError, UnicodeDecodeError):
        return f"Error: Could not read {file_path}"
    return "".join(lines)


# --- AgentScope tool-compatible wrappers ---


async def scan_find_files(directory: str) -> ToolResponse:
    """Find all Python files in the target directory.

    Args:
        directory: Root directory to scan.

    Returns:
        List of Python file paths found.
    """
    files = find_python_files(directory)
    result = "\n".join(files) if files else "No Python files found."
    return ToolResponse(content=[TextBlock(type="text", text=result)])


async def scan_search_pattern(file_path: str, pattern: str) -> ToolResponse:
    """Search for a regex pattern in a file.

    Args:
        file_path: Path to the file to search.
        pattern: Regex pattern to find.

    Returns:
        Matching lines with line numbers.
    """
    matches = search_pattern_in_file(file_path, pattern)
    if not matches:
        return ToolResponse(content=[TextBlock(type="text", text=f"No matches for '{pattern}' in {file_path}")])
    lines = [f"L{m['line_number']}: {m['line']}" for m in matches]
    return ToolResponse(content=[TextBlock(type="text", text="\n".join(lines))])


async def scan_read_file(file_path: str, max_lines: int = 200) -> ToolResponse:
    """Read the content of a file.

    Args:
        file_path: Path to the file.
        max_lines: Maximum number of lines to read (default 200).

    Returns:
        File content.
    """
    content = read_file_content(file_path, max_lines)
    return ToolResponse(content=[TextBlock(type="text", text=content)])

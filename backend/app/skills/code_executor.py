from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any


async def execute_python_code(code: str, timeout_seconds: int = 8) -> dict[str, Any]:
    """Execute Python code in a short-lived subprocess and capture output."""

    with tempfile.TemporaryDirectory(prefix="skill_exec_") as temp_dir:
        script_path = Path(temp_dir) / "snippet.py"
        script_path.write_text(code, encoding="utf-8")

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_raw, stderr_raw = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds} seconds",
                "exit_code": -1,
            }

    return {
        "stdout": stdout_raw.decode("utf-8", errors="replace").strip(),
        "stderr": stderr_raw.decode("utf-8", errors="replace").strip(),
        "exit_code": process.returncode,
    }

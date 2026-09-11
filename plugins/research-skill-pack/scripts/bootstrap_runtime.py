#!/usr/bin/env python3
"""Create the isolated local runtime used by the Research Skill Pack MCP server."""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = PLUGIN_ROOT / ".runtime"
REQUIREMENTS = PLUGIN_ROOT / "requirements-runtime.txt"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize the isolated Research Skill Pack MCP runtime.")
    parser.add_argument("--recreate", action="store_true", help="recreate the local runtime before installing locked dependencies")
    args = parser.parse_args(argv)
    if args.recreate and RUNTIME.exists():
        import shutil
        shutil.rmtree(RUNTIME)
    if not (RUNTIME / "bin" / "python").is_file():
        venv.EnvBuilder(with_pip=True, clear=False).create(RUNTIME)
    python = RUNTIME / "bin" / "python"
    subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--requirement", str(REQUIREMENTS)], check=True)
    print(f"READY: isolated MCP runtime at {RUNTIME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

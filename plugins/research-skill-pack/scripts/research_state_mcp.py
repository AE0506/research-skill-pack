#!/usr/bin/env python3
"""MCP entry point for the local Research Skill Pack canonical write gate."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import research_state


mcp = FastMCP(
    "research-state",
    instructions=(
        "Use this local service before and after any canonical .research state or artifact change. "
        "It never contacts providers or reads registered raw-data paths."
    ),
)


@mcp.tool(name="inspect_research_project", description="Read a redacted local project summary, required gates, receipt integrity, and next canonical routes.")
def inspect_research_project(project_root: str) -> dict[str, Any]:
    return research_state.inspect_research_project(project_root)


@mcp.tool(name="validate_canonical_change", description="Preflight a canonical artifact/state change without writing files. Returns a change fingerprint and deterministic findings.")
def validate_canonical_change(project_root: str, change: dict[str, Any]) -> dict[str, Any]:
    return research_state.validate_canonical_change(project_root, change)


@mcp.tool(name="commit_canonical_change", description="Revalidate and commit one canonical artifact/state change. Returns a receipt ID on success; immutable artifacts are never overwritten.")
def commit_canonical_change(project_root: str, change: dict[str, Any]) -> dict[str, Any]:
    return research_state.commit_canonical_change(project_root, change)


if __name__ == "__main__":
    mcp.run(transport="stdio")

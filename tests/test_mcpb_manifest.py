"""The MCPB manifest must list exactly the tools the server exposes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from kommo_mcp.tools import get_tool_definitions

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "mcpb" / "manifest.json"

_spec = importlib.util.spec_from_file_location("build_mcpb", ROOT / "scripts" / "build_mcpb.py")
build_mcpb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_mcpb)


def test_manifest_tools_match_server_tools() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["tools"] == [
        {"name": t.name, "description": t.description} for t in get_tool_definitions()
    ]


def test_smithery_tools_include_input_schema() -> None:
    tools = build_mcpb.smithery_tools()
    assert len(tools) == len(get_tool_definitions())
    assert all(isinstance(t["inputSchema"], dict) for t in tools)


def test_smithery_tools_include_annotations() -> None:
    tools = build_mcpb.smithery_tools()
    assert all(t.get("annotations") for t in tools)


def test_smithery_tools_include_object_output_schema() -> None:
    tools = build_mcpb.smithery_tools()
    assert all(t["outputSchema"]["type"] == "object" for t in tools)
    assert {t["name"]: t["outputSchema"] for t in tools} == {
        t.name: t.outputSchema for t in get_tool_definitions()
    }


def test_spec_manifest_tools_have_no_extra_keys() -> None:
    assert all(set(t) == {"name", "description"} for t in build_mcpb.spec_tools())

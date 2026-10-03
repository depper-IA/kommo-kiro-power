"""Quality checks for MCP tool definitions (names, annotations, descriptions)."""

from __future__ import annotations

import pytest

from kommo_mcp.tools import get_tool_definitions

TOOLS = get_tool_definitions()


def test_tool_count_and_unique_names() -> None:
    names = [t.name for t in TOOLS]
    assert len(names) == 30
    assert len(set(names)) == len(names)


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_annotations_present(tool) -> None:
    ann = tool.annotations
    assert ann is not None, "missing annotations"
    assert ann.title
    assert ann.readOnlyHint is not None
    assert ann.destructiveHint is not None
    assert ann.idempotentHint is not None
    assert ann.openWorldHint is True


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_read_only_tools_flagged(tool) -> None:
    if tool.name.startswith(("list_", "get_")):
        assert tool.annotations is not None and tool.annotations.readOnlyHint is True
    elif tool.annotations is not None:
        assert tool.annotations.readOnlyHint is False


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_delete_tools_destructive(tool) -> None:
    if tool.name.startswith("delete_"):
        assert tool.annotations is not None and tool.annotations.destructiveHint is True


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_read_only_tools_not_destructive(tool) -> None:
    if tool.annotations is not None and tool.annotations.readOnlyHint:
        assert tool.annotations.destructiveHint is False


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_description_length(tool) -> None:
    assert 80 <= len(tool.description or "") <= 600


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_every_property_described(tool) -> None:
    for pname, spec in tool.inputSchema.get("properties", {}).items():
        assert (spec.get("description") or "").strip(), f"{pname} lacks description"
        if spec.get("type") == "array" and isinstance(spec.get("items"), dict):
            items = spec["items"]
            if items.get("type") == "object":
                for iname, ispec in items.get("properties", {}).items():
                    assert (ispec.get("description") or "").strip(), f"{pname}.{iname}"

"""Keep mcpb/manifest.json in sync with the server tools and build bundles.

    python scripts/build_mcpb.py                    # sync manifest tools only
    python scripts/build_mcpb.py --smithery OUT     # also write a Smithery bundle

The MCPB spec only allows `name` and `description` per tool, so the manifest in
the repo stays spec-compliant. Smithery requires each tool's `inputSchema` and
scores `annotations` and `outputSchema`, so the Smithery bundle adds all three.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from kommo_mcp.tools import get_tool_definitions

MCPB_DIR = Path(__file__).resolve().parent.parent / "mcpb"
MANIFEST = MCPB_DIR / "manifest.json"
BUNDLE_FILES = ("pyproject.toml", "src/server.py")


def spec_tools() -> list[dict]:
    return [{"name": t.name, "description": t.description} for t in get_tool_definitions()]


def smithery_tools() -> list[dict]:
    tools = []
    for t in get_tool_definitions():
        entry = {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
        if t.outputSchema is not None:
            entry["outputSchema"] = t.outputSchema
        if t.annotations is not None:
            entry["annotations"] = t.annotations.model_dump(exclude_none=True)
        tools.append(entry)
    return tools


def sync_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["tools"] = spec_tools()
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def build_smithery_bundle(manifest: dict, out: Path) -> None:
    smithery_manifest = {**manifest, "tools": smithery_tools()}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(smithery_manifest, indent=2, ensure_ascii=False))
        for name in BUNDLE_FILES:
            zf.write(MCPB_DIR / name, name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--smithery", type=Path, help="write a Smithery bundle to this path")
    args = parser.parse_args()

    manifest = sync_manifest()
    print(f"Synced {len(manifest['tools'])} tools into {MANIFEST}")
    if args.smithery:
        build_smithery_bundle(manifest, args.smithery)
        print(f"Wrote Smithery bundle to {args.smithery}")


if __name__ == "__main__":
    main()

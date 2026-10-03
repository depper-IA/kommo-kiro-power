"""Every skill must have valid YAML frontmatter, or Kiro skips it."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with frontmatter"
    block = text.split("---\n", 2)[1]
    return yaml.safe_load(block)


def test_skills_exist() -> None:
    assert SKILL_FILES


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_frontmatter_is_valid_yaml(path: Path) -> None:
    data = _frontmatter(path)
    assert data["name"] == path.parent.name
    assert isinstance(data["description"], str) and data["description"]

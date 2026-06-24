#!/usr/bin/env python3
"""Validate a personal skills catalog."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
FRONTMATTER_RE = re.compile(r"^---\r?\n(?P<yaml>[\s\S]*?)\r?\n---\r?\n?")


def read_simple_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter")

    data: dict[str, str] = {}
    for raw_line in match.group("yaml").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized = value.strip().strip('"').strip("'")
        if key.strip() in {"name", "description"}:
            data[key.strip()] = normalized
    return data


def main() -> int:
    if (ROOT / "SKILL.md").exists():
        print("error: root SKILL.md would shadow nested skills; move it under skills/<name>/", file=sys.stderr)
        return 1

    if not SKILLS_DIR.is_dir():
        print("error: missing skills/ directory", file=sys.stderr)
        return 1

    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        print("error: no skills found under skills/*/SKILL.md", file=sys.stderr)
        return 1

    names: set[str] = set()
    for skill_file in skill_files:
        data = read_simple_frontmatter(skill_file)
        name = data.get("name", "")
        description = data.get("description", "")
        if not name:
            print(f"error: {skill_file.relative_to(ROOT)} missing name", file=sys.stderr)
            return 1
        if not description:
            print(f"error: {skill_file.relative_to(ROOT)} missing description", file=sys.stderr)
            return 1
        if name in names:
            print(f"error: duplicate skill name {name!r}", file=sys.stderr)
            return 1
        names.add(name)
        if skill_file.parent.name != name:
            print(
                f"warning: directory {skill_file.parent.name!r} differs from frontmatter name {name!r}",
                file=sys.stderr,
            )

        evals = skill_file.parent / "evals" / "evals.json"
        if evals.exists():
            json.loads(evals.read_text(encoding="utf-8"))

    print(f"ok: {len(skill_files)} skill(s): {', '.join(sorted(names))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

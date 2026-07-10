#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py — generates index.md from the pages' frontmatter.
Columns: Page (uniform full-path link) | Description (background) | Last updated (last_compiled).
Requires fix_frontmatter.py to run first so every page has a background.
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

INDEX = V.WIKI / "index.md"

HEADER = [
    '---', 'subject: "[[Wiki Index]]"', 'tags:', '  - wiki', '  - index',
    'private: false', '---', '# Wiki Index', '',
    '| Page | Description | Last updated |', '|------|-------------|--------------|',
]


def get_date(meta):
    return meta.get("last_compiled") or meta.get("updated") or ""


def existing_descriptions():
    """name(stem) -> description from the current index, as a fallback so
    descriptions aren't lost."""
    out = {}
    if not INDEX.exists():
        return out
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*\[\[([^\]]+)\]\]\s*\|\s*(.*?)\s*\|", line)
        if m:
            out[V.nfc(m.group(1).split("/")[-1].strip())] = m.group(2).strip()
    return out


def main():
    prev_desc = existing_descriptions()
    rows, missing_desc = [], []
    for p, meta, _ in V.iter_wiki_pages():
        name = V.nfc(p.stem)
        desc = (meta.get("background") or "").strip() or prev_desc.get(name, "")
        if not desc:
            missing_desc.append(name)
        rows.append((get_date(meta), name, desc))

    # Sort: by date descending, then name
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)

    lines = list(HEADER)
    for date, name, desc in rows:
        lines.append(f"| [[7 - Wikipedia/{name}]] | {desc} | {date} |")

    V.backup([INDEX], "index")
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✅ Wrote index: {V.rel(INDEX)} ({len(rows)} pages)")
    if missing_desc:
        print(f"⚠️  Pages with no background (empty description): {', '.join(missing_desc)}")


if __name__ == "__main__":
    main()

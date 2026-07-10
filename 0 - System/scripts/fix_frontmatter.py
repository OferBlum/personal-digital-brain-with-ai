#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_frontmatter.py — cleans up frontmatter in 7 - Wikipedia/ pages:
  • unifies the date field to last_compiled (converts updated/created if present)
  • fills background from hand-written descriptions in the old index.md
    (so the index becomes fully derived)
  • ensures required fields: tags includes wiki, private exists
  • quotes wikilinks in YAML

Default: dry-run (writes nothing, just shows what would change).
With --apply: backs up to .backup/ and then writes.
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

INDEX = V.WIKI / "index.md"
APPLY = "--apply" in sys.argv


def index_descriptions():
    """name(stem) -> description, from the table in the old index.md."""
    out = {}
    if not INDEX.exists():
        return out
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*\[\[([^\]]+)\]\]\s*\|\s*(.*?)\s*\|", line)
        if not m:
            continue
        name = V.nfc(m.group(1).split("/")[-1].strip())
        out[name] = m.group(2).strip()
    return out


def fix_one(meta, desc_map, name):
    changes = []
    # 1. date → last_compiled
    if "last_compiled" not in meta:
        for old in ("updated", "created"):
            if old in meta:
                meta["last_compiled"] = meta.pop(old)
                changes.append(f"date: {old} → last_compiled")
                break
    for old in ("updated", "created"):
        if old in meta:
            meta.pop(old)
            changes.append(f"removed duplicate field: {old}")
    # 2. background from the index
    if not (meta.get("background") or "").strip():
        d = desc_map.get(V.nfc(name))
        if d:
            meta["background"] = d
            changes.append("background: filled from the index")
        else:
            changes.append("background: missing (not in index — fill manually)")
    # 3. tags includes wiki
    tags = meta.get("tags")
    if isinstance(tags, str):
        tags = [tags]
    if tags is None:
        tags = []
    if "wiki" not in tags:
        tags = ["wiki"] + tags
        meta["tags"] = tags
        changes.append("tags: added wiki")
    elif "tags" not in meta:
        meta["tags"] = tags
    # 4. private exists
    if "private" not in meta:
        meta["private"] = "false"
        changes.append("private: added false")
    return changes


def main():
    desc_map = index_descriptions()
    planned, touched_paths = [], []
    for p, meta, body in V.iter_wiki_pages():
        before = V.render_page(dict(meta), body)
        changes = fix_one(meta, desc_map, p.stem)
        after = V.render_page(meta, body)
        if before != after:
            planned.append((p, changes, meta, body))
            touched_paths.append(p)

    if not planned:
        print("✅ Nothing to fix — all frontmatter is valid.")
        return

    print(f"{'🟢 writing' if APPLY else '🔍 preview (dry-run)'} — {len(planned)} pages:")
    for p, changes, _, _ in planned:
        print(f"\n  📄 {V.nfc(p.stem)}")
        for c in changes:
            print(f"     • {c}")

    if not APPLY:
        print("\nℹ️  Nothing written. To apply: python3 fix_frontmatter.py --apply")
        return

    dest = V.backup(touched_paths, "frontmatter")
    for p, _, meta, body in planned:
        p.write_text(V.render_page(meta, body), encoding="utf-8")
    print(f"\n✅ Wrote {len(planned)} pages. Backup: {V.rel(dest)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trim_cache.py — keeps only the N most recent sessions in _cache.md,
pushing older ones to _cache-archive.md. Default: N=2.
Usage: python3 trim_cache.py [N]
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

CACHE = V.WIKI / "_cache.md"
ARCHIVE = V.WIKI / "_cache-archive.md"
KEEP = int(sys.argv[1]) if len(sys.argv) > 1 else 2


def main():
    if not CACHE.exists():
        print("ℹ️  No _cache.md.")
        return
    text = CACHE.read_text(encoding="utf-8")
    # split into header + blocks by "## Session"
    parts = re.split(r"(?m)^(?=## Session)", text)
    header = parts[0]
    blocks = parts[1:]
    if len(blocks) <= KEEP:
        print(f"ℹ️  Only {len(blocks)} sessions — nothing to archive.")
        return

    keep_blocks = blocks[:KEEP]
    archive_blocks = blocks[KEEP:]

    V.backup([CACHE, ARCHIVE], "cache")
    CACHE.write_text(header + "".join(keep_blocks), encoding="utf-8")

    prev = ARCHIVE.read_text(encoding="utf-8") if ARCHIVE.exists() else \
        "---\ntags: [cache, archive]\nprivate: false\n---\n\n# Cache Archive\n\n"
    ARCHIVE.write_text(prev + "".join(archive_blocks), encoding="utf-8")

    print(f"✅ Kept {KEEP} sessions in _cache.md, archived {len(archive_blocks)}.")


if __name__ == "__main__":
    main()

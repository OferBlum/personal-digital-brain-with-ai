#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
append_log.py — appends a log entry to log.md (newest at the end; history left untouched).
Usage:
  python3 append_log.py --op ingest --title "Title" --pages "Page A,Page B" [--source "raw/..."]
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V


def require_public_target(path):
    """Reject unavailable targets before body reads, backups or replacement."""
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents) or V.is_forbidden(path):
        raise SystemExit("Unavailable bookkeeping target; operation refused.")

LOG = V.WIKI / "log.md"


def require_public_reference(reference, page=False):
    inner = str(reference).strip().removeprefix("[[").removesuffix("]]")
    inner = inner.split("|")[0].split("#")[0].strip()
    if inner.startswith(("http://", "https://")):
        return
    ref = Path(inner)
    if page and len(ref.parts) == 1:
        target = V.WIKI / ref
    elif inner.startswith("raw/"):
        target = V.WIKI / ref
    else:
        target = V.VAULT / ref
    require_public_target(target)
    if not target.suffix:
        require_public_target(target.with_suffix(".md"))
    if not page and len(ref.parts) == 1:
        for directory in (V.RAW, V.NOTES, V.TOPICS):
            candidate = directory / ref
            require_public_target(candidate if candidate.suffix else candidate.with_suffix(".md"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", required=True, help="ingest / crosslink / resolve / lint ...")
    ap.add_argument("--title", required=True)
    ap.add_argument("--pages", default="", help="comma-separated list of pages")
    ap.add_argument("--source", default="")
    a = ap.parse_args()

    require_public_target(LOG)

    pages = [p.strip() for p in a.pages.split(",") if p.strip()]
    for page in pages:
        require_public_reference(page, page=True)
    if a.source:
        require_public_reference(a.source)
    links = " · ".join(f"[[7 - Wikipedia/{p}]]" for p in pages)

    entry = f"## [{V.today()}] {a.op} | {a.title}\n"
    if a.source or links:
        arrow = f"{a.source} → " if a.source else ""
        entry += f"\n{arrow}{links}\n"

    exists = LOG.exists()
    require_public_target(LOG)
    V.backup([LOG], "log")
    require_public_target(LOG)
    # Append mode preserves every byte of old history, including line endings
    # and trailing whitespace; the old body is neither read nor rearranged.
    with LOG.open("a", encoding="utf-8", newline="") as out:
        if not exists:
            out.write("---\ntype: log\nsubject:\ntags:\n  - wiki\n  - log\n---\n\n# Wiki Log\n")
        out.write("\n\n" + entry)
    print(f"✅ Log entry added: [{V.today()}] {a.op} | {a.title}")


if __name__ == "__main__":
    main()

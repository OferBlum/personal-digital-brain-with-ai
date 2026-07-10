#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
append_log.py — appends a log entry to log.md (newest on top).
Usage:
  python3 append_log.py --op ingest --title "Title" --pages "Page A,Page B" [--source "raw/..."]
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

LOG = V.WIKI / "log.md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", required=True, help="ingest / crosslink / resolve / lint ...")
    ap.add_argument("--title", required=True)
    ap.add_argument("--pages", default="", help="comma-separated list of pages")
    ap.add_argument("--source", default="")
    a = ap.parse_args()

    pages = [p.strip() for p in a.pages.split(",") if p.strip()]
    links = " · ".join(f"[[7 - Wikipedia/{p}]]" for p in pages)

    entry = f"## [{V.today()}] {a.op} | {a.title}\n"
    if a.source or links:
        arrow = f"{a.source} → " if a.source else ""
        entry += f"\n{arrow}{links}\n"

    if LOG.exists():
        text = LOG.read_text(encoding="utf-8")
    else:
        text = "---\nsubject: \"[[Wiki Log]]\"\ntags:\n  - wiki\n  - log\nprivate: false\n---\n\n# Wiki Log\n"

    # Inject right after the "# Wiki Log" heading
    marker = "# Wiki Log"
    idx = text.find(marker)
    if idx == -1:
        new = text.rstrip() + "\n\n" + entry
    else:
        cut = text.find("\n", idx) + 1
        new = text[:cut] + "\n" + entry + "\n" + text[cut:].lstrip("\n")

    V.backup([LOG], "log")
    LOG.write_text(new, encoding="utf-8")
    print(f"✅ Log entry added: [{V.today()}] {a.op} | {a.title}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wiki_sources_report.py — scans wiki_sources in every page, classifies each
entry, and writes a report of the problems. Read-only, touches no page.
Run this first, before making any changes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

REPORT = V.WIKI / "wiki_sources_issues.md"


def classify(page_path, entry, md_index):
    inner = entry.split("|")[0].strip()
    if inner.startswith("[[") and inner.endswith("]]"):
        inner = inner[2:-2].strip()
    status, target = V.resolve_link(inner, md_index)
    if status == "missing":
        return ("🔴 missing target", f"`{inner}` — no such file found")
    if status == "ambiguous":
        return ("🟠 ambiguous name", f"`{inner}` — several files with this name, needs a full path")
    # ok — but maybe it points to itself or to another wiki page (not a real ingestion source)
    if V.nfc(str(target)) == V.nfc(str(page_path)):
        return ("🟣 self-reference", f"`{inner}` — the page lists itself as a source")
    if V.WIKI in Path(target).parents and V.RAW not in Path(target).parents:
        return ("🔵 source is a wiki page", f"`{inner}` — probably a cross-link, not a real source")
    return None  # valid (raw/ or a note)


def main():
    md_index = V.all_md_index()
    rows = []
    ok = 0
    for p, meta, _ in V.iter_wiki_pages():
        srcs = meta.get("wiki_sources", [])
        if isinstance(srcs, str):
            srcs = [srcs]
        if not srcs:
            rows.append((V.nfc(p.stem), "⚪ no source", "no wiki_sources field"))
            continue
        for entry in srcs:
            res = classify(p, entry, md_index)
            if res:
                rows.append((V.nfc(p.stem), res[0], res[1]))
            else:
                ok += 1

    lines = [
        "---", "tags: [report]", "private: false", "---",
        "# wiki_sources report", "",
        f"Generated: {V.today()} · valid entries: {ok} · problems: {len(rows)}", "",
    ]
    if rows:
        lines += ["| Page | Kind | Detail |", "|------|------|--------|"]
        for name, kind, detail in rows:
            lines.append(f"| [[7 - Wikipedia/{name}]] | {kind} | {detail} |")
    else:
        lines.append("✅ No problems — all wiki_sources are valid.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✅ valid entries: {ok}")
    print(f"⚠️  problems recorded: {len(rows)}")
    print(f"📄 report: {V.rel(REPORT)}")
    for name, kind, detail in rows:
        print(f"   {kind}  {name}: {detail}")


if __name__ == "__main__":
    main()
